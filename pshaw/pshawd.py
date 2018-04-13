import asyncio, asyncssh, sys, json, datetime, logging, os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PORT = 8022
LIFETIME = 24 * 60 * 60
EVICT_INTERVAL = LIFETIME / 100

CLIENT_KEY = os.path.join(os.environ["HOME"], ".ssh", "pshaw_client")
SERVER_KEY = os.path.join(os.environ["HOME"], ".ssh", "pshaw_server")

password_store = dict()
password_times = dict()  # time of storage

loop = asyncio.get_event_loop()

def evict():
  now = loop.time()
  for label, then in list(password_times.items()):
    if now - then > LIFETIME:
      logging.warning("%s expired", label)
      del password_store[label]
      del password_times[label]

def evict_repeatedly():
  evict()
  loop.call_later(EVICT_INTERVAL, evict_repeatedly)

async def recv(process):
  string = await process.stdin.readline()
  return json.loads(string)

async def send(object, process):
  string = json.dumps(object)
  process.stdout.write(string + "\n")

async def server_app(process):
  # get label from client
  label = await recv(process)

  # look up password for label, if any, and report to client
  password = password_store.get(label, None)
  await send(password, process)

  # if no password stored, client will ask user and give it to us
  if label not in password_store:
    logging.info("asking client for %s password..." % label)
    password = await recv(process)
    password_store[label] = password
    password_times[label] = loop.time()
    tomorrow = datetime.date.now() + datetime.timedelta(days=1)
    # FIXME somehow we never get here, but the password *IS* stored
    logging.info("%s password stored. Expires: %s", label, tomorrow)

  process.exit(0)

def main():
  async def start_server():
    await asyncssh.listen(
      "localhost", PORT,
      server_host_keys=[SERVER_KEY],
      authorized_client_keys="%s.pub" % CLIENT_KEY,
      allow_pty=False,
      agent_forwarding=False,
      process_factory=server_app)

  try:
    loop.run_until_complete(start_server())
  except (OSError, asyncssh.Error) as exc:
    sys.exit("Error starting server: " + str(exc))
  evict_repeatedly()
  loop.run_forever()

if __name__ == "__main__":
  main()
