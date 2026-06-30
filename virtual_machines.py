from contextlib import contextmanager

from qemu import PcieDevicePassthrough
from resources import acquire_resource_lock, release_resource_lock

intel_devices = {
    "gtx780": [
        PcieDevicePassthrough(
            host_address="81:00.0", x_vga=True, multifunction=True
        ),  # gtx-780 gpu
        PcieDevicePassthrough(host_address="81:00.1"),  # gtx-780 audio
    ],
    "igpu": [
        PcieDevicePassthrough(
            host_address="00:02.0",
            x_vga=True,
            multifunction=True,
            romfile="ARL_MTL_GOPv22_igd.rom",
        )
    ],
    "npu": [PcieDevicePassthrough(host_address="00:0b.0")],
}


mac_pool = {
    "52:54:00:00:00:01": "10.100.1.241",
    "52:54:00:00:00:02": "10.100.1.240",
    "52:54:00:00:00:03": "10.100.1.239",
    "52:54:00:00:00:04": "10.100.1.238",
    "52:54:00:00:00:05": "10.100.1.237",
    "52:54:00:00:00:06": "10.100.1.236",
}


def _get_mac_address_from_pool(host: str):
    for mac, ip in mac_pool.items():
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
                "+vmx,guest-phys-bits=39",
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
                # hide kvm, to workaround nvidia driver blocking VMs
                # "kvm=off",
                # "hv_vendor_id=0",
                # "hv_passthrough",
                # "-hypervisor",
                # "level=35",
                "+vmx,guest-phys-bits=39",
            ],
        },
    },
}
