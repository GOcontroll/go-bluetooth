import subprocess

import rfcommServerConstants as commands
import server


def controller_programs(commandnmbr, arg):
    level1 = ord(arg[0])
    arg = arg[1:]

    # initialize the screen for the user
    if level1 == commands.INIT_CONTROLLER_PROGRAMS:
        statusses = []
        services = arg.split(":")
        for service in services:
            stdout = subprocess.run(
                ["systemctl", "is-active", service], stdout=subprocess.PIPE, text=True
            )
            status = stdout.stdout[:-1]
            statusses.append(status)
        server.send(
            chr(commandnmbr)
            + chr(commands.INIT_CONTROLLER_PROGRAMS)
            + ":".join(statusses)
        )

    # apply change to a service
    elif level1 == commands.SET_CONTROLLER_PROGRAMS:
        data = arg.split(":")
        service = data[-1]
        new_states = data[:-1]
        if len(data) > 2:
            for new_state in new_states:
                stdout = subprocess.run(
                    ["systemctl", new_state, service], stderr=subprocess.PIPE, text=True
                )
                stdout = stdout.stderr
                print("test")
                if "Failed" in stdout:
                    server.send(
                        chr(commandnmbr)
                        + chr(commands.SET_CONTROLLER_PROGRAMS)
                        + "0:"
                        + stdout.split(":")[1]
                        + ":"
                        + service
                    )
                    return
            server.send(
                chr(commandnmbr) + chr(commands.SET_CONTROLLER_PROGRAMS) + "1::"
            )
            return
        server.send(
            chr(commandnmbr)
            + chr(commands.SET_CONTROLLER_PROGRAMS)
            + "0:Message received was incorrect.:"
            + service
        )
