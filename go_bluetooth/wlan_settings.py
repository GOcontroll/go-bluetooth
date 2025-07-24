import logging
import os
import subprocess
import time

import rfcommServerConstants as commands
import server
from PyModuline import wifi, networking

logger = logging.getLogger(__name__)


def wireless_settings(commandnmbr, arg):
    level1 = ord(arg[0])
    arg = arg[1:]

    # get information to set up the main wireless settings screen
    if level1 == commands.INIT_WIRELESS_SETTINGS:
        try:
            wifi_state = wifi.get_wifi()
        except:
            wifi_state = True
            logger.error(f"could not get wifi state: {ex}")
        logger.debug(f"wifi state: {wifi_state}")
        if wifi_state:
            try:
                status = wifi.get_wifi_mode()
            except subprocess.CalledProcessError as ex:
                logger.error(f"could not get wifi mode: {ex}")
                status = "ap"
        else:
            status = "off"

        connection_status = str(networking.connectivity_state())

        try:
            ip = wifi.get_wifi_address()
        except Exception as ex:
            logger.error(f"Could not get wifi address: {ex}")
            ip = "no IP available"

        server.send(
            chr(commands.WIRELESS_SETTINGS)
            + chr(commands.INIT_WIRELESS_SETTINGS)
            + status
            + ":"
            + connection_status
            + ":"
            + ip
        )
        return

    # get the list of networks available to the controller
    elif level1 == commands.GET_WIFI_NETWORKS:
        wifi_list = wifi.get_wifi_networks()

        wifi_list = subprocess.run(
            ["nmcli", "-t", "dev", "wifi"], stdout=subprocess.PIPE, text=True
        )  # gets the list in a layout optimal for scripting, networks seperated by \n, columns seperated by :
        networks = wifi_list.stdout[:-1].split("\n")
        i = len(networks) - 1
        for n in range(len(networks)):
            networks[i] = networks[i].split(":")
            if len(networks[i]) < 2:
                networks.pop(i)
            elif (
                len(networks[i]) > 8
            ):  # new Network manager (bullseye) format, includes mac address at index 1, but it gets split by : aswell which is annoying.
                if networks[i][7] == "":
                    networks.pop(i)
                else:
                    networks[i] = [
                        networks[i][0],
                        networks[i][7],
                        networks[i][11],
                        networks[i][13],
                    ]
                    if networks[i][3] == "":
                        networks[i][3] = "No Security"
                    networks[i] = ":".join(networks[i])
            else:  # old Network manager (buster) format, does not include mac address
                if (
                    networks[i][1] == ""
                ):  # if this is true the current index contains a network with no name
                    networks.pop(i)
                else:
                    networks[i] = [
                        networks[i][0],
                        networks[i][1],
                        networks[i][5],
                        networks[i][7],
                    ]
                    if networks[i][3] == "":
                        networks[i][3] = "No Security"
                    networks[i] = ":".join(networks[i])
            i -= 1
        networks.sort(reverse=True)
        networks = "\n".join(networks)

        server.send(chr(commandnmbr) + chr(commands.GET_WIFI_NETWORKS) + networks)
        return

    # show devices connected to the access point
    elif level1 == commands.GET_CONNECTED_DEVICES:
        final_device_list = []
        stdout = subprocess.run(
            ["ip", "n", "show", "dev", "wlan0"], stdout=subprocess.PIPE, text=True
        )
        connected_devices = stdout.stdout.split("\n")
        i = len(connected_devices) - 1
        for n in range(len(connected_devices)):
            if (
                "REACHABLE" not in connected_devices[i]
                and "DELAY" not in connected_devices[i]
            ):
                connected_devices.pop(i)
            i -= 1

        stdout = subprocess.run(
            ["cat", "/var/lib/misc/dnsmasq.leases"], stdout=subprocess.PIPE, text=True
        )
        previous_connections = stdout.stdout.split("\n")[:-1]

        for i, connected_device in enumerate(connected_devices):
            connected_device_list = connected_device.split(" ")
            for j, previous_connection in enumerate(previous_connections):
                if connected_device_list[2] in previous_connection:
                    final_device_list.append(
                        ";".join(
                            [
                                connected_device_list[2],
                                previous_connection.split(" ")[3],
                            ]
                        )
                    )
        server.send(chr(commandnmbr) + chr(level1) + "\n".join(final_device_list))
        return

    # gather the information about the access point for the user
    elif level1 == commands.INIT_AP_SETTINGS:
        path = "/etc/NetworkManager/system-connections/GOcontroll-AP.nmconnection"
        with open(path, "r") as settings:
            file = settings.readlines()
            ssid_line = get_line(path, "ssid=")
            psk_line = get_line(path, "psk=")
            ssid = file[ssid_line].split("=")[1][:-1]
            psk = file[psk_line].split("=")[1][:-1]
        server.send(
            chr(commandnmbr) + chr(commands.INIT_AP_SETTINGS) + ssid + ":" + psk
        )

    # sconnect to a wifi network specified in the command argument
    elif level1 == commands.CONNECT_TO_WIFI:
        # seperate arg
        message_list = arg.split(":")
        # attempt to connect to a network with the given arguments
        result = subprocess.run(
            [
                "nmcli",
                "device",
                "wifi",
                "connect",
                message_list[0],
                "password",
                message_list[1],
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        # save the result
        resultstring = result.stdout
        # possible results:
        # Error: No network with SSID 'dfg' found.
        # Error: Connection activation failed: (7) Secrets were required, but not provided.
        # Device 'wlan0' successfully activated with 'uuid'
        if resultstring.find("successfully") != -1:
            connection_result = commands.WIFI_CONNECT_SUCCESS
        elif resultstring.find("Secrets") != -1:
            connection_result = commands.WIFI_CONNECT_FAILED_INC_PW
            subprocess.run(["nmcli", "connection", "delete", "id", message_list[0]])
        elif resultstring.find("SSID") != -1:
            connection_result = commands.WIFI_CONNECT_FAILED_INC_SSID
            subprocess.run(["nmcli", "connection", "delete", "id", message_list[0]])
        else:
            connection_result = commands.WIFI_CONNECT_FAILED_UNKNOWN
            subprocess.run(["nmcli", "connection", "delete", "id", message_list[0]])
        # give feedback to the app
        server.send(
            chr(commandnmbr) + chr(commands.CONNECT_TO_WIFI) + chr(connection_result)
        )

    # disconnect from a wifi network specified in the command argument
    elif level1 == commands.DISCONNECT_FROM_WIFI:
        # attempt to disconnect from specified network
        result = subprocess.run(
            ["nmcli", "connection", "delete", "id", arg],
            stdout=subprocess.PIPE,
            text=True,
        )
        # save the result
        resultstring = result.stdout
        # possible results:
        # Connection 'name' (uuid) succesfully deleted.
        # Error: unknown connection 'name'.\n
        # Error: cannot delete unknown connection(s): id 'name'
        if resultstring.find("successfully") != -1:
            disconnection_result = commands.WIFI_DISCONNECT_SUCCESS
        else:
            disconnection_result = commands.WIFI_DISCONNECT_FAILED
        # give feedback to the app
        server.send(
            chr(commandnmbr)
            + chr(commands.DISCONNECT_FROM_WIFI)
            + chr(disconnection_result)
        )

    # switch between access point or wifi receiver mode
    elif level1 == commands.SWITCH_WIRELESS_MODE:
        if arg == "ap":
            if not wifi.get_wifi():
                wifi.set_wifi(True)
                time.sleep(1)
            wifi.activate_ap()
            time.sleep(2)

            server.send(
                chr(commandnmbr) + chr(commands.SWITCH_WIRELESS_MODE) + "ap"
            )

        elif arg == "wifi":
            if not wifi.get_wifi():
                wifi.set_wifi(True)
                time.sleep(1)
            wifi.deactivate_ap()
            time.sleep(2)
            server.send(
                chr(commandnmbr) + chr(commands.SWITCH_WIRELESS_MODE) + "wifi"
            )

        elif arg == "off":
            if wifi.get_wifi():
                wifi.set_wifi(False)
            time.sleep(2)
            server.send(chr(commandnmbr) + chr(commands.SWITCH_WIRELESS_MODE) + "off")

        else:
            server.send(chr(commandnmbr) + chr(commands.SWITCH_WIRELESS_MODE) + "error")


##########################################################################################

# access point settings
# handles changing and displaying access point settings


def access_point_settings(commandnmbr, arg):
    level1 = ord(arg[0])
    arg = arg[1:]

    # apply changes the user made to the access point
    if level1 == commands.SET_AP_SETTINGS:
        arg = arg.split(":")
        name = arg[0]
        psk = arg[1]
        subprocess.run(
            ["nmcli", "con", "mod", "GOcontroll-AP", "802-11-wireless.ssid", name]
        )
        subprocess.run(["nmcli", "con", "mod", "GOcontroll-AP", "wifi-sec.psk", psk])
        reload = subprocess.run(
            ["nmcli", "con", "down", "GOcontroll-AP"], stdout=subprocess.PIPE, text=True
        )
        reload = reload.stdout
        if "succesfully" in reload:
            subprocess.run(["nmcli", "con", "up", "GOcontroll-AP"])
        server.send(chr(commandnmbr) + chr(commands.SET_AP_SETTINGS) + "done")

    # initialize the screen for the user
    elif level1 == commands.INIT_AP_SETTINGS:
        path = "/etc/NetworkManager/system-connections/GOcontroll-AP.nmconnection"
        with open(path, "r") as settings:
            file = settings.readlines()
            ssid_line = get_line(path, "ssid=")
            psk_line = get_line(path, "psk=")
            ssid = file[ssid_line].split("=")[1][:-1]
            psk = file[psk_line].split("=")[1][:-1]
        server.send(
            chr(commandnmbr) + chr(commands.INIT_AP_SETTINGS) + ssid + ":" + psk
        )
