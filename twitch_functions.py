import requests


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
