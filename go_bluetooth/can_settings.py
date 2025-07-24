import subprocess
import threading
import time

import rfcommServerConstants as commands
import server
from common import get_line_num


def can_settings(commandnmbr, arg):
    global read_can_bus_load
    level1 = ord(arg[0])
    arg = arg[1:]

    # initialize the screen for the user
    if level1 == commands.INIT_CAN_SETTINGS:
        read_can_bus_load = False
        # print("Gathering can info")
        path = "/etc/network/interfaces"
        can_ifs_string = ""
        ip_a_info = subprocess.run(
            ["ip", "-br", "a"], stdout=subprocess.PIPE, text=True
        )
        ip_a_info = ip_a_info.stdout
        ip_a_info_arr = ip_a_info.split("\n")
        for i in range(4):
            baudrate = "0"
            can_if = "|"
            if f"can{i}" in ip_a_info:
                can_if = "_"
                index = [idx for idx, s in enumerate(ip_a_info_arr) if f"can{i}" in s][
                    0
                ]
                if "UP" in ip_a_info_arr[index]:
                    can_if = "-"
                baudrate = get_baudrate(i)
                baudrate = int(int(baudrate) / 1000)
            can_ifs_string = f"{can_ifs_string}{can_if}:{baudrate} kBit/s\n"
        can_ifs_string = can_ifs_string[:-1]
        server.send(chr(commandnmbr) + chr(commands.INIT_CAN_SETTINGS) + can_ifs_string)

    # change the baudrate of a specified bus
    elif level1 == commands.SET_CAN_BAUDRATE:
        # arg= "interface:baudrate(int):state(up or down)"
        arg = arg.split(":")
        path = "/etc/network/interfaces.d/can.conf"
        search_string = f"iface {arg[0]} inet manual"
        interface_line = get_line_num(path, search_string)
        if interface_line is not False:
            with open(path, "r") as interfaces:
                file = interfaces.readlines()
            line = file[interface_line + 1]
            line = line.split(" ")
            line[8] = arg[1]
            line = " ".join(line)
            file[interface_line + 1] = line
            with open(path, "w") as interfaces:
                interfaces.writelines(file)
            if arg[2] == "up":
                subprocess.run(["ifdown", arg[0]])
                time.sleep(0.2)
                subprocess.run(["ifup", arg[0]])
        server.send(chr(commandnmbr) + chr(commands.SET_CAN_BAUDRATE))

    # monitors the bus load of all enabled can interfaces
    elif level1 == commands.CAN_BUS_LOAD:
        time.sleep(1)
        interfaces = arg.split(":")
        for i, interface in enumerate(interfaces):
            interfaces[i] = f"can{interface}@" + get_baudrate(interface)
        interfaces = [":".join(interfaces)]
        read_can_bus_load = not read_can_bus_load
        if read_can_bus_load:
            ts = threading.Thread(target=bus_load_thread, args=(interfaces))
            ts.start()

    # turn on or of a can interface
    elif level1 == commands.SET_CAN_STATE:
        read_can_bus_load = False
        arg = arg.split(":")
        if arg[1] == "true":
            subprocess.run(["ifup", arg[0]])
        else:
            subprocess.run(["ifdown", arg[0]])
        server.send(chr(commandnmbr) + chr(commands.SET_CAN_STATE))


# seperate thread to monitor the bus load
def bus_load_thread(interfaces):
    global kill_threads
    if len(interfaces) > 1:
        interfaces = interfaces.split(":")
    busload = subprocess.Popen(
        ["canbusload"] + interfaces, stdout=subprocess.PIPE, text=True
    )
    while True:
        output = busload.stdout.readline()
        if busload.poll() is not None or not read_can_bus_load or kill_threads:
            break
        if output:
            output_split = output.strip().split(" ")
            if len(output_split) > 1:
                interface = output_split[0].split("@")[0]
                load = output_split[-1]
                server.send(
                    chr(commands.CAN_SETTINGS)
                    + chr(commands.CAN_BUS_LOAD)
                    + interface
                    + ":"
                    + load
                )
                time.sleep(0.1)


# get the baud rate of canx
def get_baudrate(x):
    path = "/etc/network/interfaces.d/can.conf"
    search_string = f"iface can{x} inet manual"
    interface_line = get_line_num(path, search_string)
    if interface_line is not False:
        with open(path, "r") as interfaces:
            file = interfaces.readlines()
        line = file[interface_line + 1]
        line = line.split(" ")
        return line[8]
    return "0"
