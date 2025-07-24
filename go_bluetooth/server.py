import logging

logger = logging.getLogger(__name__)

server = None


def set_server(server):
    global server
    server = server


def get_server():
    global server
    return server


# slightly expanded s.send function so not every command has to convert the string to bytes
def send(string):
    global server
    logger.debug(f"outgoing:\n{bytes(string, 'utf-8')}")
    server.send(bytes(string, "utf-8"))
