import http.server
import socketserver
import urllib.parse as parse
import webbrowser
import threading
import os

PORT = 3133
auth_code = None
state = str(os.getpid())
client_id = None
with open("client-id", "r") as f:
    client_id = f.read().strip()

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
        req = parse.urlparse(self.path)
        if req == None or req.path != "/":
            self.my_respond(400, "Bad Request " + self.path)
            return
        query = parse.parse_qs(req.query)
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
print("auth code:", auth_code)
