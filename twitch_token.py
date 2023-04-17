from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import re
import webbrowser
from twitch_functions import get_access_token
from threading import Thread
CONFIG_PATH = "./config.json"


class HttpGetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        with open(CONFIG_PATH) as f:
            conf = json.load(f)
        auth_code = re.findall('(?<=code=).*?(?=&)', self.path)
        access_token = get_access_token(conf["client_id"], conf["client_secret"], auth_code)
        conf["access_token"] = access_token["access_token"]
        conf["refresh_token"] = access_token["refresh_token"]
        with open(CONFIG_PATH, "w") as f:
            json.dump(conf, f, ensure_ascii=False, indent=4)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write('<p>Код авторизации получен.</p>'.encode())
        raise KeyboardInterrupt


def run_http_server():
    httpd = HTTPServer(('', 5000), HttpGetHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


if __name__ == "__main__":
    with open(CONFIG_PATH) as f:
        conf = json.load(f)
    url = f"https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={conf['client_id']}&redirect_uri=http://localhost:5000&scope=chat%3Aread+channel%3Aread%3Aredemptions"
    server_thread = Thread(target=run_http_server)
    server_thread.start()
    print("Opening browser page...")
    webbrowser.open(url, 2)
    server_thread.join()
