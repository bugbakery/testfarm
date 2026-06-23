from qemu import PcieDevicePassthrough

intel_devices = {
    "gtx780": [
        PcieDevicePassthrough(
            host_address="81:00.0", x_vga=True, multifunction=True
        ),  # gtx-780 gpu
        PcieDevicePassthrough(host_address="81:00.1"),  # gtx-780 audio
    ],
    "igpu": [],
    "npu": [],
}

virtual_machines = {
    "win11+intel": {
        "host": "desktop-intel",
        "os": "windows",
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
            "pci_devices": intel_devices["gtx780"],
            "mac_address": "52:54:00:00:00:01",
        },
        "wireguard": "10.100.1.241",
    },
    "ubuntu+intel": {
        "host": "desktop-intel",
        "os": "linux",
        "vm_config": {
            "harddrive_file": "ubuntu-base.qcow2",
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
            "pci_devices": intel_devices["gtx780"],
            "mac_address": "52:54:00:00:00:02",
        },
        "wireguard": "10.100.1.240",
    },
    "3": {
        "host": "desktop-intel",
        "vm_config": {
            "mac_address": "52:54:00:00:00:03",
        },
        "wireguard": "10.100.1.239",
    },
    "4": {
        "host": "desktop-intel",
        "vm_config": {
            "mac_address": "52:54:00:00:00:04",
        },
        "wireguard": "10.100.1.238",
    },
    "5": {
        "host": "desktop-intel",
        "vm_config": {
            "mac_address": "52:54:00:00:00:05",
        },
        "wireguard": "10.100.1.237",
    },
    "6": {
        "host": "desktop-intel",
        "vm_config": {
            "mac_address": "52:54:00:00:00:06",
        },
        "wireguard": "10.100.1.236",
    }
}
