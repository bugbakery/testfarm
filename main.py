import argparse
from contextlib import ExitStack
import sys

from qemu import QemuVm
from virtual_machines import virtual_machines
from hosts import get_conn, is_reachable, wake
from repl import Repl
from net import find_next_free_port


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
    parser.add_argument("--skip-boot-check", action="store_true")
    parser.add_argument("-c", "--command")
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

    try:
        cmd = vm.build_cmd()
        if verbose:
            print(f"Running command: {cmd}")
        vm_cmd_result = host_conn.sudo(
            cmd,
            password=host_conn.connect_kwargs["password"],
            asynchronous=True,
            out_stream=sys.stdout if verbose else None,
            err_stream=sys.stderr if verbose else None,
            pty=True,  # needed, so the command is killed properly when exiting
        )
        with ExitStack() as stack:
            if not args.skip_boot_check:
                print("-> Waiting for VM to boot...")
                while not is_reachable(virtual_machine_spec):
                    pass

            if not args.no_ssh:
                ssh_port = find_next_free_port(2022)
                stack.enter_context(
                    get_conn("jump").forward_local(
                        ssh_port,
                        remote_host=virtual_machine_spec["wireguard"],
                        remote_port=22,
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
                        remote_host=virtual_machine_spec["wireguard"],
                        remote_port=3389,
                    )
                )
                print(f"-> RDP proxied on localhost:{rdp_port}")

            if args.command:
                get_conn(virtual_machine_spec).run(args.command)
                exit(0)

            Repl(
                rdp_port=rdp_port,
                virtual_machine_spec=virtual_machine_spec,
                verbose=verbose,
                exit_stack=stack,
            ).cmdloop()

    finally:
        print("-> Stopping vm...")
        vm_cmd_result.runner.kill()
