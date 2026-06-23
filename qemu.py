from dataclasses import dataclass


@dataclass
class PcieDevicePassthrough:
    host_address: str
    multifunction: bool = False
    x_vga: bool = False


class QemuVm:
    def __init__(
        self,
        *,
        cpu_args: list[str],
        memory: str,
        cores: int,
        harddrive_file: str,
        ephemeral: bool,
        mac_address: str,
        vnc_display: int | None = None,
        pci_devices: list[PcieDevicePassthrough] = [],
    ) -> None:
        self.cpu_args = cpu_args
        self.memory = memory
        self.cores = cores
        self.harddrive_file = harddrive_file
        self.ephemeral = ephemeral
        self.mac_address = mac_address
        self.vnc_display = vnc_display
        self.pci_devices = pci_devices

    def build_cmd(self):
        cmd = "qemu-system-x86_64-uefi"
        cmd += " -enable-kvm"
        cmd += " -M q35,usb=on,acpi=on,hpet=off"
        cmd += f" -drive file={self.harddrive_file}"
        cmd += " -monitor stdio"
        cmd += " -device usb-tablet"
        cmd += " -device virtio-serial"
        # cmd += " -device virtserialport,chardev=qga0,name=org.qemu.guest_agent.0"

        cmd += f" -m {self.memory}"
        cmd += f" -cpu {','.join(self.cpu_args)}"
        cmd += f" -smp cores={self.cores}"

        cmd += f" -device virtio-net-pci,netdev=user0,mac={self.mac_address}"
        cmd += " -netdev bridge,helper=/run/wrappers/bin/qemu-bridge-helper,id=user0,br=br0"

        if self.ephemeral:
            cmd += " -snapshot"

        if self.vnc_display is not None:
            cmd += f" -display vnc=:{self.vnc_display},password=off,lossy=on"
        else:
            cmd += " -display none"

        for d in self.pci_devices:
            device_arg = f" -device driver=vfio-pci,host={d.host_address}"

            if d.x_vga:
                device_arg += ",x-vga=on"

            if d.multifunction:
                device_arg += ",multifunction=on"

            cmd += device_arg

        return cmd
