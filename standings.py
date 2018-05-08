# Copyright © 2018 Po Huit
# [This program is licensed under the "MIT License"]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

# Demo of command-line ESI SSO auth.
# Follows https://developers.eveonline.com/blog/article/
#   sso-to-authenticated-calls

import http.server
import urllib.request
import socketserver
import urllib.parse
import webbrowser
import threading
import json
import random
import base64
from sys import stderr

client_data = None
with open("client-data", "r") as f:
    client_data = json.load(f)

PORT = 3133
auth_code = None
state = str(random.getrandbits(128))
client_id = client_data['client-id']
client_secret = client_data['client-secret']

def http_request(path, data=None, headers={}):
    "Make an HTTP request and return the resulting parsed JSON."
    headers['Content-Type'] = "application/json"
    if data != None:
        data = json.dumps(data)
        print("data:", data)
        data = data.encode('utf-8')
    request = urllib.request.Request(path,
                                     data=data,
                                     headers=headers)
    try:
        response = urllib.request.urlopen(request)
        if response.status == 200:
            try:
                return json.load(response)
            except json.decoder.JSONDecodeError as e:
                print("json error: ", e, file=stderr)
        else:
            print("bad response status: ", response.status, file=stderr)
    except urllib.error.URLError as e:
        print("http error: ", e.code, file=stderr)
    print("fetch failed for", path, file=stderr)
    exit(1)


class MyHandler(http.server.BaseHTTPRequestHandler):
    def my_respond(self, code, body):
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        body_html = "<html><body><h1>{}</h1></body></html>" \
                    .format(body) \
                    .encode('utf-8')
        self.wfile.write(body_html)

    def do_GET(self):
        global auth_code, state
        req = urllib.parse.urlparse(self.path)
        if req == None or req.path != "/":
            self.my_respond(400, "Bad Request " + self.path)
            return
        query = urllib.parse.parse_qs(req.query)
        if query == None or 'code' not in query:
            self.my_respond(400, "Bad Request Query" + self.path)
            return
        if 'state' not in query or query['state'][0] != state:
            self.my_respond(409, "Race with other client: please retry")
            return
        auth_code = query['code'][0]
        self.my_respond(200, auth_code)

def worker():
    global PORT
    # https://brokenbad.com/address-reuse-in-pythons-socketserver/
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print("serving at port", PORT)
        httpd.handle_request()

print("starting webserver")
webserver = threading.Thread(target=worker)
webserver.start()
print("opening browser")
authurl = "https://login.eveonline.com/oauth/authorize?" + \
          "response_type=code&" + \
          "redirect_uri=http://localhost:{}&" + \
          "client_id={}&" + \
          "scope=esi-characters.read_standings.v1&" + \
          "state={}"
authurl = authurl.format(PORT, client_id, state)
webbrowser.open(authurl)
print("gathering code")
webserver.join()
if auth_code == None:
    print("Could not get auth code")
    exit(1)

def base64encode(s):
    return base64.standard_b64encode(s.encode('utf-8')).decode('utf-8')

client_data = base64encode(client_id + ":" + client_secret)
req = { 'grant_type' : "authorization_code",
        'code' : auth_code }
auth_info = http_request("https://login.eveonline.com/oauth/token",
                         data=req,
                         headers={'Authorization' : "Basic " + client_data})
print('auth_info:', auth_info)

access_token = auth_info['access_token']
char_info = http_request("https://login.eveonline.com/oauth/verify",
                         headers={'Authorization' : "Bearer " + access_token})
print('char_info:', char_info)

standings = http_request("https://esi.tech.ccp.is/v1/characters/{}/standings"
                         .format(char_info['CharacterID']),
                         headers={'Authorization' : "Bearer " + access_token})

print(standings)
