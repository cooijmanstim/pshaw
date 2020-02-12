import sys, json, os, subprocess as sp, getpass, logging, argparse
from pathlib import Path
import paramiko

# silence deprecation warnings
# https://github.com/paramiko/paramiko/issues/1386
import warnings
warnings.filterwarnings(action='ignore',module='.*paramiko.*')


logger = logging.getLogger()
logger.setLevel(logging.INFO)

PORT = 8022
CLIENT_KEY = paramiko.RSAKey(filename=Path(os.environ["HOME"], ".ssh", "pshaw_client"))
SERVER_KEY = paramiko.RSAKey(filename=Path(os.environ["HOME"], ".ssh", "pshaw_server"))
SUBSYSTEM = "pshaw"

def recv(pipe):
  string = pipe.readline()
  #logger.info("recv %s", string)
  return json.loads(string)

def send(pipe, object):
  string = json.dumps(object)
  #logger.info("send %s", string)
  pipe.write(string + "\n")

def get_password(realm):
  client = paramiko.SSHClient()
  client.get_host_keys().add("[localhost]:%s" % PORT, "ssh-rsa", SERVER_KEY)
  client.connect("localhost", pkey=CLIENT_KEY, port=PORT)
  transport = client.get_transport()
  # using channel as a context manager causes it to be closed afterwards, which seems to conflict
  # with the close on client or pipe.
  #with transport.open_channel("session") as channel:
  channel = transport.open_channel("session")
  if True:
    logger.info("invoking subsystem")
    channel.invoke_subsystem("pshaw")
    with channel.makefile("rw") as pipe:
      send(pipe, realm)
      password = recv(pipe)
      if password is None:
        password = getpass.getpass(prompt="%s password (will be stored in pshawd): " % realm)
        send(pipe, password)
  client.close()
  return password

def main():
  parser = argparse.ArgumentParser(description="ssh with password persistence.")
  parser.add_argument("realm", help="A name to associate with the password so it can later be retrieved under that name.")
  args, command = parser.parse_known_args()

  password = get_password(args.realm)

  rpipe, wpipe = os.pipe()
  os.set_inheritable(rpipe, True)
  os.set_blocking(wpipe, False)
  os.write(wpipe, password.encode("ascii"))
  os.close(wpipe)

  os.execvp("sshpass", ["sshpass", "-d%i" % rpipe] + command)

if __name__ == "__main__":
  main()
