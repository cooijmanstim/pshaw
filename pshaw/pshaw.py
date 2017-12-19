import asyncio, asyncssh, sys, json, os, subprocess as sp, getpass, logging, argparse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PORT = 8022
CLIENT_KEY = os.path.join(os.environ["HOME"], ".ssh", "pshaw_client")
SERVER_KEY = os.path.join(os.environ["HOME"], ".ssh", "pshaw_server")

async def recv(process):
  string = await process.stdout.readline()
  return json.loads(string)

async def send(object, process):
  string = json.dumps(object)
  process.stdin.write(string + "\n")

async def client_app(conn, label):
  # we just want to send/receive stuff through the ssh channel, not run a command, but there seems
  # to be no other way, and the server side will not receive anything regarding "cat" but just the
  # input we give the process O__o whatever works I guess
  async with conn.create_process('cat') as process:
    # request the password for the given label
    await send(label, process)

    # receive the password
    password = await recv(process)

    # if the server doesn't have it, ask the user
    if password is None:
      password = getpass.getpass(prompt="%s password (will be stored in pshawd): " % label)

      # store the password with the server
      await send(password, process)

  process.close()
  return password

async def get_password(label):
  with open("%s.pub" % SERVER_KEY) as infile:
    known_hosts = asyncssh.import_known_hosts("localhost %s" % infile.read())
  async with asyncssh.connect(
      "localhost", PORT,
      known_hosts=known_hosts,
      client_keys=[CLIENT_KEY],
  ) as conn:
    password = await client_app(conn, label)
    return password

def main():
  parser = argparse.ArgumentParser(description="ssh with password persistence.")
  parser.add_argument("label", help="A name to associate with the password so it can later be retrieved under that name.")
  args, command = parser.parse_known_args()

  password = asyncio.get_event_loop().run_until_complete(get_password(args.label))

  rpipe, wpipe = os.pipe()
  os.set_inheritable(rpipe, True)
  os.set_blocking(wpipe, False)
  os.write(wpipe, password.encode("ascii"))
  os.close(wpipe)

  os.execvp("sshpass", ["sshpass", "-d%i" % rpipe] + command)

if __name__ == "__main__":
  main()
