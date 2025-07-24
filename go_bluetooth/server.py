import logging

logger = logging.getLogger(__name__)

bt_server = None


def set_server(server):
    global bt_server
    server = bt_server


def get_server():
    global bt_server
    return bt_server


# slightly expanded s.send function so not every command has to convert the string to bytes
def send(string):
    logger.debug(f"outgoing:\n{bytes(string, 'utf-8')}")
    bt_server.send(bytes(string, "utf-8"))
