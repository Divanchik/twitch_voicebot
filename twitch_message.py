import re


def filter_message(s: str):
    emoji_pattern = "[a-z]+\d*[A-Z][a-zA-Z\d]*"
    result = re.sub(emoji_pattern, '', s)
    return result


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


def parse_command(s: str):
    result = {}
    tmp = s.split(' ')

    if tmp[0] in ['JOIN', 'PART', 'NOTICE', 'CLEARCHAT', 'HOSTTARGET', 'PRIVMSG']:
        result = {'command': tmp[0], 'channel': tmp[1]}
    elif tmp[0] == 'PING':
        result = {'command': tmp[0]}
    elif tmp[0] == 'CAP':
        result = {'command': tmp[0], 'is_cap_request_enabled': True if tmp[2] == 'ACK' else False}
    elif tmp[0] == 'GLOBALUSERSTATE':
        result = {'command': tmp[0]}
    elif tmp[0] in ['USERSTATE', 'ROOMSTATE']:
        result = {'command': tmp[0], 'channel': tmp[1]}
    elif tmp[0] == 'RECONNECT':
        print("\nThe Twitch IRC server is about to terminate the connection for maintenance.")
        result = {'command': tmp[0]}
    elif tmp[0] == '421':
        print(f"\nUnsupported IRC command: {tmp[2]}")
        result = None
    elif tmp[0] == '001':
        result = {'command': tmp[0], 'channel': tmp[1]}
    elif tmp[0] in ['002', '003', '004', '353', '366', '372', '375', '376']:
        print(f"\nNumeric message: {tmp[0]}")
        return None
    else:
        print(f"\nUnexpected command: {tmp[0]}")
        return None
    return result


def parse_source(s: str):
    if s is None or len(s) == 0:
        return None
    tmp = s.split('!')
    if len(tmp) == 2:
        return {'nick': tmp[0], 'host': tmp[1]}
    else:
        return {'nick': None, 'host': tmp[0]}


def parse_message(msg: str):
    i = 0
    raw_tags = None
    raw_source = None
    raw_command = None
    raw_parameters = None

    # search tags
    if msg[i] == '@':
        j = msg.index(' ')
        raw_tags = msg[1:j]
        i = j + 1
    
    # search source
    if msg[i] == ':':
        i += 1
        j = msg.index(' ', i)
        raw_source = msg[i:j]
        i = j + 1
    
    # search command
    j = msg.find(':', i)
    if j == -1:
        j = len(msg)
    raw_command = msg[i:j].strip()

    # search parameters
    if j != len(msg):
        i = j + 1
        raw_parameters = msg[i:]
    
    tags = None
    source = None
    command = None
    parameters = None

    command = parse_command(raw_command)
    if raw_tags is not None:
        tags = parse_tags(raw_tags)
    source = parse_source(raw_source)
    if raw_parameters is None:
        parameters = raw_parameters
    else:
        parameters = raw_parameters.strip()
        # print('\n')
        # print('='*50)
        # print(parameters)
        parameters = filter_message(parameters)
        # print(parameters)
        # print('='*50)

    return {'tags': tags, 'source': source, 'command': command, 'parameters': parameters}

if __name__ == "__main__":
    from json import dumps
    print(dumps(parse_message('@badge-info=;badges=;client-nonce=d8747a27930a536e38d795752611d2ed;color=#FF0000;display-name=WB_Ghost;emotes=;first-msg=0;flags=;id=bb42c555-402d-48f2-82a8-40c23b6fa607;mod=0;returning-chatter=0;room-id=135015290;subscriber=0;tmi-sent-ts=1681925706763;turbo=0;user-id=755589900;user-type= :wb_ghost!wb_ghost@wb_ghost.tmi.twitch.tv PRIVMSG #dimadivan :Как дела хоть?'), indent=4, ensure_ascii=False))