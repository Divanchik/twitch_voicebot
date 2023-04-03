import requests
import json
import logging


def validate_token(token):
    resp = requests.get(
        "https://id.twitch.tv/oauth2/validate",
        headers={"Authorization": f"OAuth {token}"}
    )
    data = resp.json()
    if resp.status_code == 401:
        return -1
    return int(data["expires_in"] / 60)


def refresh_token(client_id, client_secret, r_token):
    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": r_token
        }
    )
    data = resp.json()
    return data


def get_access_token(client_id, client_secret, auth_code):
    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://localhost:3000"
        }
    )
    data = resp.json()
    return data


if __name__ == "__main__":
    # get new token
    with open("config.json") as f:
        conf = json.load(f)
    print(f"https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={conf['client_id']}&redirect_uri=http://localhost:3000&scope=chat%3Aread")
    auth_code = input("Enter authorization code: ").strip()
    access_token = get_access_token(conf["client_id"], conf["client_secret"], auth_code)
    conf["access_token"] = access_token["access_token"]
    conf["refresh_token"] = access_token["refresh_token"]
    with open("config.json", "w") as f:
        json.dump(conf, f, ensure_ascii=False, indent=4)