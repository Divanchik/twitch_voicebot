import asyncio
import websockets
import logging
import json
import re
import os
from twitch_token import validate_token, refresh_token
CONFIG_PATH = "./config.json"


def parce_src(s: str):
    src_parts = s.split("!")
    return {
        "nick": src_parts[0] if len(src_parts) == 2 else None,
        "host": src_parts[1] if len(src_parts) == 2 else src_parts[0]
    }


def parse_params(s: str):
    res = {}
    idx = 0
    command_parts = s[idx+1:].strip()
    params_idx = command_parts.find(" ")

    if params_idx == -1:
        res["bot_command"] = command_parts[:]
    else:
        res["bot_command"] = command_parts[:params_idx]
        res["bot_command_params"] = command_parts[params_idx:].strip()
    return res


def parse_msg(msg: str):
    parsed_message = {
        "tags": None,
        "source": None,
        "command": None,
        "parameters": None
    }
    raw_tags = ""
    raw_source = ""
    raw_command = ""
    raw_parameters = ""

    idx = 0

    if msg[idx] == "@":
        end_idx = msg.index(" ")
        raw_tags = msg[1:end_idx]
        idx = end_idx + 1
    
    if msg[idx] == ":":
        idx += 1
        end_idx = msg.index(" ", idx)
        raw_source = msg[idx:end_idx]
        idx = end_idx + 1
    
    end_idx = msg.find(":", idx)
    if end_idx == -1:
        end_idx = len(msg)
    
    raw_command = msg[idx:end_idx].strip()

    if end_idx != len(msg):
        idx = end_idx + 1
        raw_parameters = msg[idx:]
    
    parsed_message["source"] = parce_src(raw_source)
    parsed_message["parameters"] = raw_parameters
    if raw_parameters[0] == "!":
        parsed_message["command"] = parse_params(raw_parameters)
    
    return parsed_message
    

async def handle_message(wsock, message):
    msg = parse_msg(message)
    if re.match("PING.*", message):
        await wsock.send(f"PONG{message[4:]}")
        logging.info("PING PONG")
    else:
        logging.info(f"{msg['source']['nick']} >> {msg['parameters']}")
        os.system(f"echo \"{msg[0][1]}\" | RHVoice-test -p Anna -r 80")
        await asyncio.sleep(0.5)


async def listener(wsock):
    async for message in wsock:
        await handle_message(wsock, message)


async def main(config):
    uri = "ws://irc-ws.chat.twitch.tv:80"
    channel = "dimadivan"
    async with websockets.connect(uri) as wsock:
        await wsock.send(f"PASS oauth:{config['access_token']}")
        await wsock.send("NICK dimadivan")
        resp = await wsock.recv()
        print(resp)
        await wsock.send(f"JOIN #{channel}")
        logging.info(f"Joining [{channel}] channel...")
        await listener(wsock)


if __name__ == "__main__":
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
        asyncio.run(main(conf))
