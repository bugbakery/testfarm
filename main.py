import argparse
from virtual_machines import virtual_machines
from hosts import get_conn, wake

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
    host_conn = get_conn(vm_host)
    host_conn.run("hostname",)
