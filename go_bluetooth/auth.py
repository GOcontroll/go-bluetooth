import hashlib

import rfcommServerConstants as commands
import server

current_passkey = ""
trust_device = False


def set_passkey(key: str):
    global current_passkey
    current_passkey = key


def get_passkey() -> str:
    global current_passkey
    return current_passkey


def verify_device(commandnmbr, arg):
    level1 = ord(arg[0])
    arg = arg[1:]

    if level1 == commands.DEVICE_VERIFICATION_ATTEMPT:
        split_arg = arg.split(":")
        device_id = split_arg[-1]
        entered_key = ":".join(split_arg[:-1]).lower()
        entered_hash = hashlib.sha256(entered_key.encode()).hexdigest()
        if get_passkey() == entered_hash:
            trust_device = True
            with open("/etc/bluetooth/trusted_devices.txt", "a") as add_trusted_device:
                add_trusted_device.write(device_id + "\n")
            request_verification(commands.DEVICE_VERIFICATION_SUCCESS)
        else:
            request_verification(commands.DEVICE_VERIFICATION_INCORRECT_PASSKEY)

    elif level1 == commands.DEVICE_VERIFICATION_EXCHANGE_KEY:
        try:
            with open("/etc/bluetooth/trusted_devices.txt", "r") as trusted_devices:
                if trusted_devices.read().find(arg) != -1:
                    trust_device = True
                    request_verification(commands.DEVICE_VERIFICATION_SUCCESS)
                else:
                    request_verification(commands.DEVICE_VERIFICATION_MISSING)
        except FileNotFoundError:
            request_verification(commands.DEVICE_VERIFICATION_MISSING)


# part of the verification structure but is called from multiple places
def request_verification(char):
    server.send(chr(commands.VERIFY_DEVICE) + chr(char))
