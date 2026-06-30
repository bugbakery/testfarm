from contextlib import contextmanager

from qemu import PcieDevicePassthrough
from resources import acquire_resource_lock, release_resource_lock

# use fixed pci addresses on all devices to prevent collisions when other devices are attached before the igpu
intel_devices = {
    "igpu": [
        # params from https://github.com/LongQT-sea/intel-igpu-passthru#other-linux-distributions-qemukvm
        PcieDevicePassthrough(
            host_address="00:02.0",
            x_igd_lpc=True,
            id="hostpci0",
            bus="pci.0",
            addr="02.0", # has to use this address to prevent errors
            romfile="ARL_MTL_GOPv22_igd.rom",
        )
    ],
    "gtx780": [
        # gpu
        PcieDevicePassthrough(
            host_address="81:00.0",
            x_vga=True,
            multifunction=True,
            bus="pci.0",
            addr="03.0",
        ),
        # audio
        PcieDevicePassthrough(
            host_address="81:00.1",
            bus="pci.0",
            addr="03.1",
        ),
    ],
    "npu": [
        PcieDevicePassthrough(
            host_address="00:0b.0",
            bus="pci.0",
            addr="0b.0",
        )
    ],
}


mac_pool = {
    "desktop-intel": {
        "52:54:00:00:00:01": "10.100.1.241",
        "52:54:00:00:00:02": "10.100.1.240",
        "52:54:00:00:00:03": "10.100.1.239",
        "52:54:00:00:00:04": "10.100.1.238",
        "52:54:00:00:00:05": "10.100.1.237",
        "52:54:00:00:00:06": "10.100.1.236",
    }
}


def _get_mac_address_from_pool(host: str):
    for mac, ip in mac_pool[host].items():
        try:
            acquire_resource_lock(host, mac)
            return mac, ip
        except Exception:
            pass

    raise Exception("Could not get mac address from pool")


@contextmanager
def use_mac_address_from_pool(host: str):
    mac, ip = _get_mac_address_from_pool(host)
    try:
        yield mac, ip
    finally:
        release_resource_lock(host, mac)


virtual_machines = {
    "win11+intel": {
        "host": "desktop-intel",
        "os": "windows",
        "user": "admin",
        "password": "admin",
        "available_devices": intel_devices,
        "vm_config": {
            "harddrive_file": "win11-nvidia-main.qcow2",
            "cpu_args": [
                "host",
                # hide kvm, to workaround nvidia driver blocking VMs
                "kvm=off",
                "hv_vendor_id=0",
                "hv_passthrough",
                "-hypervisor",
                "level=35",
                "+vmx",
                "guest-phys-bits=41",
            ],
        },
    },
    "ubuntu+intel": {
        "host": "desktop-intel",
        "os": "linux",
        "user": "bugbakery",
        "password": "admin",
        "available_devices": intel_devices,
        "vm_config": {
            "harddrive_file": "ubuntu-base.qcow2",
            "cpu_args": [
                "host",
                "guest-phys-bits=41",
            ],
        },
    },
}
