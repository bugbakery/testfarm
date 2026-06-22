import argparse
import os
from time import sleep
from qemu import QemuVm
from virtual_machines import virtual_machines
from hosts import get_conn, wake

def gen_mac_address():
    r = os.urandom(3)
    return f"52:54:00:{r.hex(sep=':')}" # use qemu prefix


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="testfarm",
        description="spawn and enter into bugbakery testing VMs",
    )
    parser.add_argument('vm', choices=virtual_machines.keys())
    args = parser.parse_args()
    virtual_machine_spec = virtual_machines[args.vm]

    print(f"Starting Virtual Machine {args.vm}")

    vm_host = virtual_machine_spec["host"]
    wake(vm_host)
    with get_conn("jump").forward_local(3389, remote_host=virtual_machine_spec["wireguard"]):
        vm_config = virtual_machine_spec["vm_config"]
        mac_address = gen_mac_address()
        vm = QemuVm(**vm_config, memory="6G", cores=4, ephemeral=True, mac_address=mac_address)
        cmd = vm.build_cmd()

        host_conn = get_conn(vm_host)

        print(f"Running command: {cmd}")
        host_conn.run(cmd, asynchronous=True)
        while True:
            sleep(10)
