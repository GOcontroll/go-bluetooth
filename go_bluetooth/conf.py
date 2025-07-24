import hashlib
import logging

import netifaces

logger = logging.getLogger(__name__)

conf = None

# features
features = {
    "verify_device": False,
    "update_controller": False,
    "file_transfer": False,
    "controller_settings": False,
    "wireless_settings": False,
    "ap_settings": False,
    "ethernet_settings": False,
    "controller_programs": False,
    "wwan_settings": False,
    "can_settings": False,
    "controller_configuration": False,
    "module_settings": False,
    "reboot_controller": False,
    "controller_communication_menu": False,
    "controller_monitoring": False,
    "usb_settings": False,
    "nbiot_settings": False,
    "gps_settings": False,
    "lin_settings": False,
}


def parse_boolean(boolean: str) -> bool:
    if boolean.lower() in ["y", "yes", "true"]:
        return True
    elif boolean.lower() in ["n", "no", "false"]:
        return False
    else:
        raise ValueError


def parse_conf(conf_file):
    global features
    conf_dict = {}
    for line in conf_file:
        if line.startswith("#"):
            continue
        option = line.split("=", 1)
        if len(option) == 2:
            try:
                conf_dict[option[0].strip().lower()] = parse_boolean(option[1].strip())
            except ValueError:
                conf_dict[option[0].strip().lower()] = option[1].strip()
    for key in features.keys():
        feature = conf_dict.get(key, False)
        if isinstance(feature, bool):
            features[key] = feature
    return conf_dict


def get_conf() -> dict:
    global conf
    if conf is not None:
        return conf
    try:
        with open("/etc/go_bluetooth.conf", "r") as conf_file:
            conf = parse_conf(conf_file)
            return conf
    except FileNotFoundError:
        conf = create_default_conf()
        return conf


def create_default_conf():
    with open("/etc/go_bluetooth.conf", "x") as conf_file:
        mac = netifaces.ifaddresses("end0")[netifaces.AF_LINK][0]["addr"]
        default_hash = hashlib.sha256(mac.encode()).hexdigest()
        default_conf = f"""
#set pass_hash with a sha256 of your passkey, the default value is the hash of the ethernet mac address
pass_hash={default_hash}
verify_device=true
update_controller=false
file_transfer=false
controller_settings=true
wireless_settings=true
ap_settings=true
ethernet_settings=true
controller_programs=true
wwan_settings=true
can_settings=true
controller_configuration=true
module_settings=true
reboot_controller=true
controller_communication_menu=true
controller_monitoring=false
usb_settings=false
nbiot_settings=false
gps_settings=false
lin_settings=false
"""
        conf_file.write(default_conf)
        return parse_conf(default_conf)


def modify_conf(key: str, val: str):
    try:
        conf = get_conf()
    except FileNotFoundError:
        create_default_conf()
    conf = get_conf()
    conf[key] = val
    write_conf(conf)


def write_conf(conf: dict):
    with open("/etc/go_webui.conf", "w") as conf_file:
        for key, value in conf.items():
            if key in ["pass_hash"]:
                conf_file.write(f"{key}={value}\n")
            pass


def get_features():
    global features
    return features
