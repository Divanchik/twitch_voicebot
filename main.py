import asyncio
import websockets
import logging
import json
import re
import os
from twitch_token import validate_token, refresh_token
CONFIG_PATH = "./config.json"


def parse_tags(s: str):
    tags_to_ignore = {
        'client-nonce': None,
        'flags': None
    }

    parsed_tags = dict()
    tags = s.split(";")
    for tag in tags:
        parsed_tag = tag.split("=")
        tag_value = None if parsed_tag[1] == '' else parsed_tag[1]
        if parsed_tag[0] in ["badges", "badge-info"]:
            if tag_value is not None:
                tmp = dict()
                badges = tag_value.split(',')
                for pair in badges:
                    badge_parts = pair.split('/')
                    tmp[badge_parts[0]] = badge_parts[1]
                parsed_tags[parsed_tag[0]] = tmp.copy()
            else:
                parsed_tags[parsed_tag[0]] = None
        elif parsed_tag[0] == 'emotes':
            if tag_value is not None:
                emotes = dict()
                emotes_list = tag_value.split('/')
                for emote in emotes_list:
                    emote_parts = emote.split(':')
                    text_pos = []
                    positions = emote_parts[1].split(',')
                    for pos in positions:
                        pos_parts = pos.split('-')
                        text_pos.append({
                            'start_pos': pos_parts[0],
                            'end_pos': pos_parts[1]
                        })
                    emotes[emote_parts[0]] = text_pos.copy()
                parsed_tags[parsed_tag[0]] = emotes.copy()
            else:
                parsed_tags[parsed_tag[0]] = None
        elif parsed_tag[0] == 'emote-sets':
            emote_set_ids = tag_value.split(',')
            parsed_tags[parsed_tag[0]] = emote_set_ids
        else:
            if parsed_tag[0] in tags_to_ignore.keys():
                pass
            else:
                parsed_tags[parsed_tag[0]] = tag_value
    return parsed_tags
        

def parse_cmd(s: str):
    return None


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
    logging.info(f"parsing ({msg})")
    parsed_message = {
        "tags": None,
        "source": None,
        "command": None,
        "parameters": None
    }

    idx = 0

    raw_tags = ""
    raw_source = ""
    raw_command = ""
    raw_parameters = ""

    # get tags component
    if msg[idx] == "@":
        end_idx = msg.index(" ")
        raw_tags = msg[1:end_idx]
        idx = end_idx + 1
    
    # get source component
    if msg[idx] == ":":
        idx += 1
        end_idx = msg.index(" ", idx)
        raw_source = msg[idx:end_idx]
        idx = end_idx + 1
    
    # get command component
    end_idx = msg.find(":", idx)
    if end_idx == -1:
        end_idx = len(msg)
    raw_command = msg[idx:end_idx].strip()

    # get parameters component
    if end_idx != len(msg):
        idx = end_idx + 1
        raw_parameters = msg[idx:]
    
    # parse
    parsed_message["command"] = raw_command
    if len(raw_tags) != 0:
        parsed_message["tags"] = parse_tags(raw_tags)
    parsed_message["source"] = parce_src(raw_source)
    parsed_message["parameters"] = raw_parameters
    # if len(raw_parameters) != 0 and raw_parameters[0] == "!":
    #     parsed_message["command"] = parse_params(raw_parameters)
    
    return parsed_message
    

async def handle_message(wsock, message):
    # msg = parse_msg(message)
    if re.match("PING.*", message):
        await wsock.send(f"PONG{message[4:]}")
        logging.info("PING PONG")
    else:
        # logging.info(f"{msg['source']['nick']} >> {msg['parameters']}")
        # os.system(f"echo \"{msg['parameters']}\" | RHVoice-test -p Anna -r 80")
        await asyncio.sleep(0.5)


async def listener(wsock, flogger: logging.Logger):
    async for message in wsock:
        flogger.info(message)
        await handle_message(wsock, message)


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
