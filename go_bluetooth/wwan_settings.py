import rfcommServerConstants as commands
import subprocess
import json
import server


def wwan_settings(commandnmbr, arg):
    level1 = ord(arg[0])
    arg = arg[1:]

    # initialize the screen for the user
    if level1 == commands.INIT_WWAN_SETTINGS:
        net_status = [str(check_connection(0.5))]
        mmcli_info = ["Info not available"]
        sim_number = ["Info not available"]
        pin = ["-"]
        apn = ["-"]
        stdout = subprocess.run(
            ["systemctl", "is-active", "go-wwan"], stdout=subprocess.PIPE, text=True
        )
        status = [stdout.stdout[:-1]]
        path = "/etc/NetworkManager/system-connections/GO-cellular.nmconnection"
        if status[0] == "active":
            try:
                pin_line = get_line(path, "pin=")
                apn_line = get_line(path, "apn=")
                with open(path, "r") as con:
                    file = con.readlines()
                    pin = [file[pin_line].split("=")[1][:-1]]
                    apn = [file[apn_line].split("=")[1][:-1]]
            except FileNotFoundError:
                subprocess.run(
                    [
                        "nmcli",
                        "con",
                        "add",
                        "type",
                        "gsm",
                        "ifname",
                        "cdc-wdm0",
                        "con-name",
                        "GO-cellular",
                        "apn",
                        "super",
                        "connection.autoconnect",
                        "yes",
                        "gsm.pin",
                        "0000",
                    ]
                )
                try:
                    pin_line = get_line(path, "pin=")
                    apn_line = get_line(path, "apn=")
                    with open(path, "r") as con:
                        file = con.readlines()
                        pin = [file[pin_line].split("=")[1][:-1]]
                        apn = [file[apn_line].split("=")[1][:-1]]
                except FileNotFoundError:
                    pin = ["-"]
                    apn = ["-"]
            modem = subprocess.run(
                ["mmcli", "--list-modems"], stdout=subprocess.PIPE, text=True
            )
            modem = modem.stdout
            if "/freedesktop/" in modem:
                modem_number = modem.split("/")[-1].split(" ")[0]
                try:
                    mmcli = subprocess.Popen(
                        ("mmcli", "-K", "--modem=" + modem_number),
                        stdout=subprocess.PIPE,
                    )
                    output = subprocess.check_output(
                        ("egrep", "model|signal-quality.value|imei|operator-name"),
                        stdin=mmcli.stdout,
                    )
                    mmcli.wait()
                    mmcli_info = output[:-1].decode("utf-8").split("\n")
                    for i, info in enumerate(mmcli_info):
                        mmcli_info[i] = info.split(":")[1][1:]
                except subprocess.CalledProcessError:
                    # print("unable to get information from modemmanager")
                    pass
            sim_command_res = subprocess.run(
                ["mmcli", "-i", "0", "-J"], stdout=subprocess.PIPE, text=True
            ).stdout
            if "error" not in sim_command_res:
                try:
                    # print(sim_command_res)
                    sim_number = [
                        json.loads(sim_command_res)["sim"]["properties"]["iccid"]
                    ]
                except:
                    pass
        status_array = net_status + status + mmcli_info + pin + apn + sim_number
        server.send(
            chr(commandnmbr) + chr(commands.INIT_WWAN_SETTINGS) + ":".join(status_array)
        )

    # turn cellular on or off
    elif level1 == commands.SWITCH_WWAN:
        arg = arg.split(":")
        if arg[0] == "false":
            # print("stopping go-wwan")
            subprocess.run(["systemctl", "stop", "go-wwan"])
            subprocess.run(["systemctl", "disable", "go-wwan"])
        else:
            if arg[1] == "false":
                # print("starting go-wwan")
                subprocess.run(["systemctl", "enable", "go-wwan"])
                subprocess.run(["systemctl", "start", "go-wwan"])
            else:  # service failed so needs to restart instead of start
                # print("restarting go-wwan")
                subprocess.run(["systemctl", "restart", "go-wwan"])
        server.send(chr(commandnmbr) + chr(commands.SWITCH_WWAN))

    # apply changes the user made to cellular settings
    elif level1 == commands.SET_WWAN_SETTINGS:
        arg = arg.split(":")
        # arg = [pin,apn]
        subprocess.run(
            ["nmcli", "con", "mod", "GO-cellular", "gsm.apn", arg[1], "gsm.pin", arg[0]]
        )
        reload = subprocess.run(
            ["nmcli", "con", "down", "GO-cellular"], stdout=subprocess.PIPE, text=True
        )
        reload = reload.stdout
        if "succesfully" in reload:
            subprocess.run(["nmcli", "con", "up", "GO-cellular"])
        server.send(chr(commandnmbr) + chr(commands.SET_WWAN_SETTINGS))
