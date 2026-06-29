import cmd
from contextlib import ExitStack
import errno
import glob
import os
from pathlib import Path
import sys
import traceback

import invoke
from tqdm import tqdm

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
        "run single command via ssh or spawn interactive ssh session: ssh [cmd]"
        try:
            if len(arg) > 0:
                get_conn(self.virtual_machine_spec).run(arg, warn=True)
            else:
                ssh_shell(self.virtual_machine_spec)
        except Exception:
            traceback.print_exc()

    def do_put(self, arg: str):
        "copy file(s) to vm: put [-r] local_path remote_path"

        args = arg.split()
        recursive = "-r" in args
        positional_args = [arg for arg in args if not arg.startswith("-")]

        def remote_home():
            conn = get_conn(self.virtual_machine_spec)
            if self.virtual_machine_spec["os"] == "windows":
                return Path(conn.run("echo %HOME%", hide="both").stdout.strip().replace("\\","/"))
            else:
                return Path(conn.run("echo -n $HOME", hide="both").stdout)

        arg_local = positional_args[0]

        arg_remote = positional_args[1]
        if arg_remote.startswith("~/"):
            arg_remote = remote_home() / arg_remote.removeprefix("~/")

        try:
            sftp = get_conn(self.virtual_machine_spec).sftp()

            def dir_exists(path: Path | str):
                if isinstance(path, str):
                    path = Path(path)

                old_cwd = sftp.getcwd()
                try:
                    sftp.chdir(str(path))
                    return True
                except IOError as err:
                    if err.errno == errno.ENOENT:
                        return False
                    raise err
                finally:
                    sftp.chdir(old_cwd)

            def mkdir(path: Path | str):
                if isinstance(path, str):
                    path = Path(path)

                if not dir_exists(path.parent):
                    mkdir(path.parent)

                if not dir_exists(path):
                    sftp.mkdir(str(path))

            if  not dir_exists(arg_remote):
                try:
                    mkdir(Path(arg_remote))
                except IOError as err:
                    if err.errno == errno.EACCES:
                        print(f"Permission denied: {arg_remote}")
                        return
                    raise err

            if recursive:
                files = glob.glob("**", root_dir=arg_local, recursive=recursive, include_hidden=True)

                for file in tqdm(files, unit="files"):
                    local_path = Path(arg_local) / file
                    target = Path(arg_remote) / file

                    if os.path.isdir(local_path):
                        if not dir_exists(target):
                            mkdir(target)
                    else:
                        sftp.put(local_path, str(target), confirm=False)
            else:
                sftp.put(arg_local, str(arg_remote))
        except Exception:
            traceback.print_exc()
