from qemu import PcieDevicePassthrough

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

virtual_machines = {
    "win11+intel/all": {
        "host": "desktop-intel",
        "os": "windows",
        "user": "admin",
        "password": "admin",
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
            "pci_devices": sum(intel_devices.values(), []),
            "mac_address": "52:54:00:00:00:01",
        },
        "wireguard": "10.100.1.241",
    },
    "ubuntu+intel/all": {
        "host": "desktop-intel",
        "os": "linux",
        "user": "bugbakery",
        "password": "admin",
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
            "pci_devices": sum(intel_devices.values(), []),
            "mac_address": "52:54:00:00:00:02",
        },
        "wireguard": "10.100.1.240",
    },
    "win11+intel/nvidia": {
        "host": "desktop-intel",
        "os": "windows",
        "user": "admin",
        "password": "admin",
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
            "mac_address": "52:54:00:00:00:03",
        },
        "wireguard": "10.100.1.239",
    },
    "ubuntu+intel/nvidia": {
        "host": "desktop-intel",
        "os": "linux",
        "user": "bugbakery",
        "password": "admin",
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
            "mac_address": "52:54:00:00:00:04",
        },
        "wireguard": "10.100.1.238",
    },
    "ubuntu+intel/npu": {
        "host": "desktop-intel",
        "os": "linux",
        "user": "bugbakery",
        "password": "admin",
        "vm_config": {
            "harddrive_file": "ubuntu-base.qcow2",
            "cpu_args": [
                "host",
                # hide kvm, to workaround nvidia driver blocking VMs
                # "kvm=off",
                # "hv_vendor_id=0",
                "hv_passthrough",
                "-hypervisor",
                "level=35",
                "+vmx,guest-phys-bits=39",
            ],
            "pci_devices": intel_devices["npu"],
            "mac_address": "52:54:00:00:00:05",
        },
        "wireguard": "10.100.1.237",
    },
    "win11+intel/igpu": {
        "host": "desktop-intel",
        "os": "windows",
        "user": "admin",
        "password": "admin",
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
            "pci_devices": intel_devices["igpu"],
            "mac_address": "52:54:00:00:00:06",
        },
        "wireguard": "10.100.1.236",
    },
}
