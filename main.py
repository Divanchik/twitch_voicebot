import asyncio
import websockets
import logging
import json
import re
import os
from twitch_functions import validate_token, refresh_token
from twitch_message import *
CONFIG_PATH = "./config.json"
ONLY_HIGHLIGHTED = False
VOICE = True

    
async def handle_message(wsock, message):
    global ONLY_HIGHLIGHTED, VOICE
    nicks_to_ignore = ["moobot"]
    if len(message) == 0:
        return
    if re.match("PING.*", message):
        await wsock.send(f"PONG{message[4:]}")
        logging.info("PING PONG")
    else:
        msg = parse_message(message)
        if msg['command'] is not None and msg['command'].get('command') == 'PRIVMSG':
            logging.info(f"{msg['source'].get('nick')} >> {msg['parameters']}")
            if VOICE and ((not ONLY_HIGHLIGHTED) or (ONLY_HIGHLIGHTED and msg['tags'] is not None and msg['tags'].get('msg-id') == 'highlighted-message')):
                os.system(f"echo \"{msg['parameters']}\" | RHVoice-test -p Anna -r 80")
        await asyncio.sleep(0.5)


async def listener(wsock, flogger: logging.Logger):
    async for raw_input in wsock:
        flogger.info(raw_input)
        messages = raw_input.split('\n')
        for msg in messages:
            await handle_message(wsock, msg)


async def main(config, flogger: logging.Logger):
    uri = "ws://irc-ws.chat.twitch.tv:80"
    channel = "dimadivan"
    async with websockets.connect(uri) as wsock:
        await wsock.send(f"CAP REQ :twitch.tv/commands twitch.tv/tags")
        await wsock.send(f"PASS oauth:{config['access_token']}")
        await wsock.send("NICK dimadivan")
        resp = await wsock.recv()
        print(resp)
        await wsock.send(f"JOIN #{channel}")
        logging.info(f"Joining [{channel}] channel...")
        resp = await wsock.recv()
        print(resp)
        await listener(wsock, flogger)


if __name__ == "__main__":
    filelogger = logging.getLogger("filelogger")
    filelogger.setLevel(logging.INFO)
    filehandler = logging.FileHandler("./raw_messages.log", encoding="utf-8")
    filehandler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
    filelogger.addHandler(filehandler)

    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
    with open(CONFIG_PATH) as f:
        conf = json.load(f)
    exp_in = validate_token(conf['access_token'])
    if exp_in < 0:
        logging.warning("Invalid or expired access token! Trying to refresh token...")
        ref_data = refresh_token(conf["client_id"], conf["client_secret"], conf["refresh_token"])
        if "error" in ref_data.keys():
            logging.error(f"Refreshing error: {ref_data['message']}")
            exit(0)
        logging.info("New token acquired!")
        conf["access_token"] = ref_data["access_token"]
        conf["refresh_token"] = ref_data["refresh_token"]
        with open("config.json", "w") as f:
            conf = json.dump(conf, f)
    else:
        logging.info(f"Token expires in {exp_in} minutes!")
        try:
            asyncio.run(main(conf, filelogger))
        except KeyboardInterrupt:
            logging.info("Exit routine...")
