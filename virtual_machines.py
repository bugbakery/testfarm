from qemu import PcieDevicePassthrough

virtual_machines = {
    "win11+intel": {
        "host": "desktop-intel",
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
            "pci_devices": [
                PcieDevicePassthrough(
                    host_address="81:00.0", x_vga=True, multifunction=True
                ),  # gtx-780 gpu
                PcieDevicePassthrough(host_address="81:00.1"),  # gtx-780 audio
            ],
        },
        "wireguard": "10.100.1.251",
    }
}
