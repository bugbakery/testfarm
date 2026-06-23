import argparse
from contextlib import ExitStack
from io import StringIO
import os
import sys
from time import sleep
from typing import IO, TextIO

from fabric import Connection
import invoke
from qemu import QemuVm
from virtual_machines import virtual_machines
from hosts import get_conn, wake

# def gen_mac_address():
#     r = os.urandom(3)
#     return f"52:54:00:{r.hex(sep=':')}" # use qemu prefix


def is_port_in_use(port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def find_next_free_port(port: int) -> int:
    p = port
    while is_port_in_use(p):
        p += 1
    return p


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="testfarm",
        description="spawn and enter into bugbakery testing VMs",
    )
    parser.add_argument("vm", choices=virtual_machines.keys())
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--vnc", action="store_true")
    parser.add_argument("--no-rdp", action="store_true")
    parser.add_argument("--no-ssh", action="store_true")
    parser.add_argument("--edit-base-image", action="store_true")
    args = parser.parse_args()
    virtual_machine_spec = virtual_machines[args.vm]
    verbose = args.verbose

    print(f"Starting Virtual Machine {args.vm}")

    vm_host = virtual_machine_spec["host"]
    wake(vm_host)

    vm_config = virtual_machine_spec["vm_config"]
    vm = QemuVm(
        **vm_config,
        memory="6G",
        cores=4,
        ephemeral=not args.edit_base_image,
        vnc_display=0 if args.vnc else None,
    )

    host_conn = get_conn(vm_host)

    with ExitStack() as stack:
        cmd = vm.build_cmd()
        if verbose:
            print(f"Running command: {cmd}")
        stack.enter_context(
            host_conn.sudo(
                cmd,
                password=host_conn.connect_kwargs["password"],
                asynchronous=True,
                out_stream=sys.stdout if verbose else None,
                err_stream=sys.stderr if verbose else None,
                pty=True,  # needed, so the command is killed properly when exiting
            )
        )

        ssh_port = find_next_free_port(3022)
        stack.enter_context(
            get_conn("jump").forward_local(
                ssh_port, remote_host=virtual_machine_spec["wireguard"], remote_port=22
            )
        )
        print(f"-> SSH proxied on localhost:{ssh_port}")

        if args.vnc:
            vnc_port = find_next_free_port(5900)
            stack.enter_context(host_conn.forward_local(vnc_port, remote_port=5900))
            print(f"-> VNC proxied on localhost:{vnc_port}")

        if not args.no_rdp:
            rdp_port = find_next_free_port(3389)
            stack.enter_context(
                get_conn("jump").forward_local(
                    rdp_port,
                    remote_port=3389,
                    remote_host=virtual_machine_spec["wireguard"],
                )
            )
            print(f"-> RDP proxied on localhost:{rdp_port}")
            if sys.platform == "darwin":
                print("-> Waiting for RDP to become available...")
                host_conn.run(
                    f"""
                    while ! nc -z {virtual_machine_spec["wireguard"]} 3389; do
                    sleep 0.5
                    done
                """,
                    hide=None if verbose else "both",
                )
                print("-> Launching RDP client... (password is 'admin')")
                invoke.run(
                    f"open 'rdp://full%20address=s%3Alocalhost%3A{rdp_port}&username=s%3Abugbakery&use%20redirection%20server%20name=i%3A1'",
                    hide="out",
                )
            else:
                print("-> Auto open RDP is currently only supported on macOS")

        class StdinWithCR:
            def read(self, i):
                a = sys.stdin.read(i)
                if a == "\n":
                    return "\r"
                return a

            def __getattr__(self, name):
                return getattr(sys.stdin, name)

        if not args.no_ssh:
            print("-> Opening ssh session...")
            conn = Connection(
                host=virtual_machine_spec["wireguard"],
                gateway=get_conn("jump"),
                user="admin",
                connect_kwargs={"password": "admin"},
            )

            if virtual_machine_spec["os"] == "windows":
                conn.run(
                    "set TERM=xterm-256color && cmd.exe",
                    pty=True,
                    in_stream=StdinWithCR(),
                )
            else:
                conn.shell()

        while True:
            sleep(10)
