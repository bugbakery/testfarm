import cmd
from contextlib import ExitStack
import sys
import traceback

import invoke

from hosts import get_conn, wait_for_port


class StdinWithCR:
    def read(self, i):
        a = sys.stdin.read(i)
        if a == "\n":
            return "\r"
        return a

    def __getattr__(self, name):
        return getattr(sys.stdin, name)


def ssh_shell(virtual_machine_spec):
    print("-> Waiting for SSH to become available...")
    wait_for_port(virtual_machine_spec, 22)

    print("-> Opening ssh session...")
    conn = get_conn(virtual_machine_spec)

    if virtual_machine_spec["os"] == "windows":
        conn.run(
            "set TERM=xterm-256color && cmd.exe",
            pty=True,
            in_stream=StdinWithCR(),
            warn=True,
        )
    else:
        conn.run("/bin/bash", pty=True, env={"TERM": "xterm-256color"}, warn=True)


def open_rdp(virtual_machine_spec: dict, rdp_port: int, verbose: bool):
    if sys.platform == "darwin":
        print("-> Waiting for RDP to become available...")
        wait_for_port(virtual_machine_spec, 3389)

        password = virtual_machine_spec["password"]
        user = virtual_machine_spec["user"]
        print(f"-> Launching RDP client... (password is '{password}')")
        invoke.run(
            f"open 'rdp://full%20address=s%3Alocalhost%3A{rdp_port}&username=s%3A{user}&use%20redirection%20server%20name=i%3A1'",
            hide="out",
        )
    else:
        print("-> Auto open RDP is currently only supported on macOS")


class Repl(cmd.Cmd):
    intro = "Welcome to the testfarm vm shell.   Type help or ? to list commands.\n"
    prompt = "(vm) "

    def __init__(
        self,
        *,
        virtual_machine_spec: dict,
        rdp_port: int,
        verbose: bool,
        exit_stack: ExitStack,
    ):
        super().__init__()
        self.virtual_machine_spec = virtual_machine_spec
        self.rdp_port = rdp_port
        self.verbose = verbose
        self.exit_stack = exit_stack

    def do_expose(self, arg: str):
        "expose a local port to the vm: expose local_port [remote_port]"

        args = arg.split()
        if len(args) < 1:
            print("missing argument: local_port")
            return

        try:
            local_port = int(args[0])
            remote_port = int(args[1]) if len(args) > 1 else local_port

            self.exit_stack.enter_context(
                get_conn(self.virtual_machine_spec).forward_remote(
                    local_port=local_port, remote_port=remote_port
                )
            )
        except Exception:
            traceback.print_exc()

    def do_rdp(self, arg: str):
        "open rdp client"
        try:
            open_rdp(
                self.virtual_machine_spec, rdp_port=self.rdp_port, verbose=self.verbose
            )
        except Exception:
            traceback.print_exc()

    def do_ssh(self, arg: str):
        "spawn ssh session"
        try:
            ssh_shell(self.virtual_machine_spec)
        except Exception:
            traceback.print_exc()
