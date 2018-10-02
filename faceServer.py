import socket

import sys
if sys.version_info >= (3, 0):
    from http.server import HTTPServer, SimpleHTTPRequestHandler
else:
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'hell0000o!')


class HTTPServerV6(HTTPServer):
  address_family = socket.AF_INET6

def main():
  server = HTTPServerV6(('::', 8080), MyHandler)
  server.serve_forever()

if __name__ == '__main__':
    main()
