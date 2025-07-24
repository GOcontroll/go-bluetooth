import glob
import subprocess
from multiprocessing import Pool

import rfcommServerConstants as commands
import server


def controller_configuration(commandnmbr, arg):
    level1 = ord(arg[0])
    arg = arg[1:]

    if level1 == commands.INIT_CONTROLLER_CONFIGURATION:
        try:
            with open("/lib/gocontroll/modules", "r") as modules:
                info = modules.readline()
        except FileNotFoundError:
            server.send(chr(commandnmbr) + chr(level1) + "-\n")
            return
        modules = info.split("\n")[0].split(":")
        firmwares = []
        module_types = []
        module_hw_versions = []
        for module in modules:
            if module:
                arr = module.split("-")
                module_types.append("-".join(arr[0:3]))
                module_hw_versions.append(arr[3])
                firmwares.append(module)
            else:
                module_types.append("-")
                module_hw_versions.append("-")
                firmwares.append("-")
        message_out = []
        # firmwares = list(dict.fromkeys(firmwares))
        message_out.append(":".join(firmwares))
        message_out.append(":".join(module_types))
        message_out.append(":".join(module_hw_versions))
        message_out = "\n".join(message_out)
        server.send(chr(commandnmbr) + chr(level1) + message_out)

    if level1 == commands.ACQUIRE_MODULE_INFORMATION:
        subprocess.run(["go-modules", "scan"])
        server.send(chr(commandnmbr) + chr(level1) + "done")


def module_settings(commandnmbr, arg):
    level1 = ord(arg[0])
    arg = arg[1:]

    if level1 == commands.INIT_MODULE_SETTINGS:
        mod_type = arg.split(":")
        mod_slot = mod_type[1]
        mod_type = mod_type[0]
        available_firmwares = glob.glob(
            "/lib/firmware/gocontroll/" + mod_type + "*.srec"
        )
        with open("/lib/gocontroll/modules", "r") as modules:
            info = modules.readline().split(":")
        current_firmware = info[int(mod_slot) - 1]
        current_firmware = ".".join(current_firmware.split("-")[-3:])
        for i, firmware in enumerate(available_firmwares):
            firmware = firmware.split(".")[0]
            firmware = firmware.split("-")[-3:]
            available_firmwares[i] = ".".join(firmware)
        available_firmwares = list(dict.fromkeys(available_firmwares))
        server.send(
            chr(commandnmbr)
            + chr(level1)
            + ":".join(available_firmwares)
            + ":"
            + current_firmware
        )

    if level1 == commands.SET_NEW_FIRMWARE:
        error_array = []
        matching_modules = []
        new_firmware = arg
        with open("/lib/gocontroll/modules", "r") as modules:
            info = modules.readline().split(":")
        module_hw_code = "-".join(new_firmware.split("-")[0:4])
        new_firmware_version = "-".join(new_firmware.split("-")[-3:]).split(".")[0]
        for i, mod in enumerate(info):
            if module_hw_code in mod:
                if new_firmware_version not in mod:
                    matching_modules.append([i + 1, new_firmware])
        number_of_updates = len(matching_modules)
        if number_of_updates > 0:
            with Pool() as p:
                results = p.map(upload_firmware, matching_modules)
                # print(results)
            for result in results:
                if "error" in result[1]:
                    error_array.append(f"{result[0]}:{result[1][:-1]}")
            if len(error_array) > 0:
                server.send(
                    chr(commandnmbr)
                    + chr(commands.ERROR_UPLOADING_FIRMWARE)
                    + "\n".join(error_array)
                )
            else:
                server.send(
                    chr(commandnmbr)
                    + chr(commands.NEW_FIRMWARE_UPLOAD_COMPLETE)
                    + "done"
                )
                subprocess.run(["go-modules", "scan"])
        else:
            server.send(
                chr(commandnmbr) + chr(commands.NO_MODULES_TO_UPDATE) + "cancelled"
            )


def upload_firmware(args):
    slot = args[0]
    new_firmware = args[1]
    stdout = subprocess.run(
        ["go-modules", "overwrite", str(slot), new_firmware],
        stdout=subprocess.PIPE,
        text=True,
    )
    return [slot, stdout.stdout]
