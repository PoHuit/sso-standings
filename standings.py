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
import csv
from sys import stdout, stderr

# The ergonomics of Python's base64 module pretty much suck.
# Here's a wrapper for our use case.
def base64encode(s):
    "String-to-string base64 encoding."
    return base64.standard_b64encode(s.encode('ascii')).decode('ascii')

# You need to have client data from your CCP registration.
# Should be JSON in the form
#   { "client-id" : "MYCLIENTID", "client-secret" : "MYCLIENTSECRET" }
# The capitalized stuff comes from
# https://developers.eveonline.com/applications; see the
# tutorial for details about setting this up. Make sure your
# client-data file is mode 600. Do not distribute this file.
client_data = None
with open("client-data", "r") as f:
    client_data = json.load(f)
client_id = client_data['client-id']
client_secret = client_data['client-secret']

# Port on localhost given as a callback when your app was
# registered.  Can be any random number between 1024 and
# 65535 that doesn't happen to conflict with somebody.
PORT = 3133
# Single-use short-expiry authorization code to be retrieved
# from CCP if needed by our local one-off webservice.
auth_code = None
# Nonce to ensure that two copies of our code running on the
# same port at the same time won't get confused by a data race.
state = str(random.getrandbits(128))

# This fancy wrapper is essentially our version of 'curl'
# from the tutorial. The data argument is expected to be a
# Python object, and headers a Python dictionary.  This
# function does a POST if data is provided and a GET
# otherwise: all in JSON.
def http_request(path, data=None, headers={}):
    "Make an HTTP request and return the resulting parsed JSON."

    # Set up the arguments.
    headers['Content-Type'] = "application/json"
    if data != None:
        data = json.dumps(data)
        data = data.encode('utf-8')

    # Actually run the request.
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
    "Single-request webserver used get the authentication code."

    # XXX Formatting is terrible.
    def my_respond(self, code, body):
        "Send a generic response."
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        body_html = "<html><body><h1>{}</h1></body></html>" \
                    .format(body) \
                    .encode('utf-8')
        self.wfile.write(body_html)

    def do_GET(self):
        """Handle the GET request from the browser after
        redirection from CCP's auth server."""
        global auth_code, state
        req = urllib.parse.urlparse(self.path)
        if req == None or req.path != "/":
            self.my_respond(400, "Bad Request " + self.path)
            return
        # XXX Note that parse_qs() returns a dictionary
        # whose values are lists.
        query = urllib.parse.parse_qs(req.query)
        if query == None or 'code' not in query:
            self.my_respond(400, "Bad request " + self.path)
            return
        if 'state' not in query or query['state'][0] != state:
            self.my_respond(409, "Race with other client: please retry")
            return
        auth_code = query['code'][0]
        self.my_respond(200, auth_code)


    def log_message(self, format, *args):
        "Silence the log messages from the server."
        return

# The thread worker to run the request server.
def worker():
    # https://brokenbad.com/address-reuse-in-pythons-socketserver/
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        httpd.handle_request()

# Get the authentication code from which the initial
# authorization tokens can be derived.
webserver = threading.Thread(target=worker)
webserver.start()
authurl = "https://login.eveonline.com/oauth/authorize?" + \
          "response_type=code&" + \
          "redirect_uri=http://localhost:{}&" + \
          "client_id={}&" + \
          "scope=esi-characters.read_standings.v1&" + \
          "state={}"
authurl = authurl.format(PORT, client_id, state)
webbrowser.open(authurl)
webserver.join()
if auth_code == None:
    print("Could not get auth code", file=stderr)
    exit(1)

# Get the auth info associated with this auth code.
client_data = base64encode(client_id + ":" + client_secret)
req = { 'grant_type' : "authorization_code",
        'code' : auth_code }
auth_info = http_request("https://login.eveonline.com/oauth/token",
                         data=req,
                         headers={'Authorization' : "Basic " + client_data})

# Get the character info associated with this access token.
access_token = auth_info['access_token']
char_info = http_request("https://login.eveonline.com/oauth/verify",
                         headers={'Authorization' : "Bearer " + access_token})

# Get the standings of the authenticated character.
standings = http_request("https://esi.tech.ccp.is/v1/characters/{}/standings"
                         .format(char_info['CharacterID']),
                         headers={'Authorization' : "Bearer " + access_token})

# Format standings as CSV for "convenience".
writer = csv.writer(stdout)
for s in standings:
    writer.writerow((s['from_id'], s['from_type'], s['standing']))
