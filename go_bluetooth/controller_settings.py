import rfcommServerConstants as commands
import server
from common import get_line_content
import time
import subprocess

def controller_settings(commandnmbr, arg):
    level1 = ord(arg[0])
    arg = arg[1:]

    # change the bluetooth name
    if level1 == commands.SET_CONTROLLER_SETTINGS:
        try:
            if ":" in arg:
                server.send(chr(commandnmbr) + chr(commands.SET_CONTROLLER_SETTINGS) + "0")
            if "GOcontroll" in arg:
                write_device_name(arg)
            else:
                arg = "GOcontroll-" + arg
                write_device_name(arg)
            server.send(chr(commandnmbr) + chr(commands.SET_CONTROLLER_SETTINGS) + "1")
        except PermissionError:
            server.send(chr(commandnmbr) + chr(commands.SET_CONTROLLER_SETTINGS) + "0")

    # gather information to display
    elif level1 == commands.INIT_CONTROLLER_SETTINGS:
        software_version = "missing"
        time.sleep(
            0.2
        )  # if the controller responds too quick the app gets wacky
        with open("/sys/firmware/devicetree/base/hardware", "r") as file:
            hardware_version = file.read()
        try:
            name = (
                get_line_content("/etc/machine-info", "PRETTY_HOSTNAME")
                .split("=")[1]
                .split(":")[0] # no : allowed in name
                .strip()
            )
        except FileNotFoundError or IndexError:
            name = "missing"
        try:
            res = subprocess.run(["uname", "-r"],check=True, text=True, stdout=subprocess.PIPE)
            software_version = res.stdout.strip()
        except subprocess.CalledProcessError:
            pass
        server.send(
            chr(commandnmbr)
            + chr(commands.INIT_CONTROLLER_SETTINGS)
            + hardware_version
            + ":"
            + software_version
            + ":"
            + name
        )


# write the new bluetooth name to the right file
def write_device_name(name):
    with open("/etc/machine-info", "w") as file:
        file.write("PRETTY_HOSTNAME=" + name)
