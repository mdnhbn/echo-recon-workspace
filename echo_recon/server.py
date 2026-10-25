"""Build the fixed loopback server without macOS reverse-hostname discovery."""
from socketserver import TCPServer
import sys

from werkzeug.serving import ThreadedWSGIServer, make_server


class LoopbackWSGIServer(ThreadedWSGIServer):
    def server_bind(self):
        # HTTPServer's normal bind calls socket.getfqdn even for 127.0.0.1.
        # A local dashboard does not need that lookup, which can stall on Mac
        # name-service configuration before the server becomes ready.
        TCPServer.server_bind(self)
        self.server_name = "localhost"
        self.server_port = self.server_address[1]


def make_local_server(app):
    if sys.platform == "darwin":
        return LoopbackWSGIServer("127.0.0.1", 8001, app)
    return make_server("127.0.0.1", 8001, app, threaded=True)
