import requests
import json
from consolemenu import SelectionMenu
import webbrowser
CONFIG_PATH = "./config.json"


def validate_token(token):
    """
    Запрос валидации токена.
        return: время действия токена (минуты) или -1 при окончании действия токена.
    """
    resp = requests.get(
        "https://id.twitch.tv/oauth2/validate",
        headers={"Authorization": f"OAuth {token}"}
    )
    data = resp.json()
    if resp.status_code == 401:
        return -1
    return int(data["expires_in"] / 60)


def refresh_token(client_id, client_secret, r_token):
    """
    Запрос на реактивацию токена.
    """
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
    menu = SelectionMenu(["New token", "Refresh token"])
    menu.show()
    if menu.selected_option == 0:
        with open(CONFIG_PATH) as f:
            conf = json.load(f)
        url = f"https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={conf['client_id']}&redirect_uri=http://localhost:3000&scope=chat%3Aread+channel%3Aread%3Aredemptions"
        webbrowser.open(url, 2)
        auth_code = input("Enter authorization code: ").strip()
        access_token = get_access_token(conf["client_id"], conf["client_secret"], auth_code)
        conf["access_token"] = access_token["access_token"]
        conf["refresh_token"] = access_token["refresh_token"]
        with open(CONFIG_PATH, "w") as f:
            json.dump(conf, f, ensure_ascii=False, indent=4)
    elif menu.selected_option == 1:
        print("Not implemented!")