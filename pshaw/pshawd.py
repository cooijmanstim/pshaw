import sys, json, datetime, logging, os, socket, threading
from pathlib import Path
import paramiko

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PORT = 8022
CLIENT_KEY = paramiko.RSAKey(filename=Path(os.environ["HOME"], ".ssh", "pshaw_client"))
SERVER_KEY = paramiko.RSAKey(filename=Path(os.environ["HOME"], ".ssh", "pshaw_server"))
SUBSYSTEM = "pshaw"

password_store = dict()
password_times = dict()  # time of storage

class PshawSubsystemHandler(paramiko.server.SubsystemHandler):
  def start_subsystem(self, name, transport, channel):
    logger.info("entered subsystem")
    with channel.makefile("rw") as pipe:
      # get label from client
      realm = recv(pipe)

      # look up password for label, if any, and report to client
      password = password_store.get(realm, None)
      send(pipe, password)

      # if no password stored, client will ask user and give it to us
      if realm not in password_store:
        logging.info("asking client for %s password..." % realm)
        password = recv(pipe)
        time = datetime.datetime.now()
        password_store[realm] = password
        password_times[realm] = time
        logging.info("%s password stored at %s", realm, time)

      self.get_server().event.set()

def recv(pipe):
  string = pipe.readline()
  #logger.info("recv %s", string)
  return json.loads(string)

def send(pipe, object):
  string = json.dumps(object)
  #logger.info("send %s", string)
  pipe.write(string + "\n")

class Server(paramiko.ServerInterface):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.event = threading.Event()

  def check_channel_request(self, kind, chanid):
    if kind == 'session':
      return paramiko.OPEN_SUCCEEDED
    return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

  def check_auth_publickey(self, username, key):
    return paramiko.AUTH_SUCCESSFUL if key == CLIENT_KEY else paramiko.AUTH_FAILED

  def get_allowed_auths(self, username):
    return "publickey"

def main():
  while True:
    try:
      # yuuuuck do i really need to do all this myself?? i thought these days were over
      # FIXME check return values -___-
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      sock.bind(("localhost", PORT))

      sock.listen(100)
      client, addr = sock.accept()

      transport = paramiko.Transport(client)
      transport.load_server_moduli()
      transport.add_server_key(SERVER_KEY)
      transport.set_subsystem_handler(SUBSYSTEM, PshawSubsystemHandler)

      server = Server()
      transport.start_server(server=server)
      # close the connection after at most 300 seconds
      server.event.wait(300)
      transport.close()
    except KeyboardInterrupt:
      sys.exit(0)
    except Exception as exc:
      logger.error(exc)

if __name__ == "__main__":
  main()
