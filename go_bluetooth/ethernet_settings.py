import logging
import subprocess
import time

import rfcommServerConstants as commands
import server
import PyModuline.networking as networking
from PyModuline import ethernet

logger = logging.getLogger("__name__")


def ethernet_settings(commandnmbr, arg):
    level1 = ord(arg[0])
    arg = arg[1:]

    # get the information for the ethernet settings screen
    if level1 == commands.INIT_ETHERNET_SETTINGS:
        try:
            ip = ethernet.get_ethernet_ip()
        except EnvironmentError:
            ip = "-"

        try:
            ip_static = ethernet.get_ethernet_static_ip()
        except EnvironmentError:
            ip_static = "-"

        try:
            static_mode = ethernet.get_ethernet_static_status()
        except EnvironmentError:
            static_mode = False
        if static_mode:
            mode = "auto"
        else:
            mode = "static"

        connection_status = "False"
        connection_status = str(networking.connectivity_state())

        server.send(
            chr(commandnmbr)
            + chr(commands.INIT_ETHERNET_SETTINGS)
            + mode
            + ":"
            + ip_static
            + ":"
            + ip
            + ":"
            + connection_status
        )

    # apply changes that were made by the user
    elif level1 == commands.SET_ETHERNET_SETTINGS:
        ethernet.set_static_ethernet_ip(f"10.100.{arg}")
        try:
            static = ethernet.get_ethernet_static_status()
        except EnvironmentError:
            static = True
        if static:
            subprocess.run(["nmcli", "con", "up", "Wired connection auto"])
            time.sleep(0.5)
            subprocess.run(["nmcli", "con", "up", "Wired connection static"])
            time.sleep(0.5)
        ethernet_settings(commandnmbr, chr(commands.INIT_ETHERNET_SETTINGS) + "")

    # switch between static or dynamic ip connection
    elif level1 == commands.SWITCH_ETHERNET_MODE:
        try:
            if arg == "true":
                ethernet.activate_ethernet_static()
            else:
                ethernet.deactivate_ethernet_static()
        except subprocess.CalledProcessError as ex:
            logger.error(f"Could not switch ethernet mode: {ex}")
        ethernet_settings(commandnmbr, chr(commands.INIT_ETHERNET_SETTINGS) + "")
