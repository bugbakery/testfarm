virtual_machines = {
    "win11+intel": {
        "host": "desktop-intel",
        "cmd": """
            qemu-system-x86_64 \
                -M q35,usb=on,acpi=on,hpet=off \
                -m 6G -cpu host,hv_relaxed,hv_frequencies,hv_vpindex,hv_ipi,hv_tlbflush,hv_spinlocks=0x1fff,hv_synic,hv_runtime,hv_time,hv_stimer,hv_vapic \
                -smp cores=4 \
                -enable-kvm \
                -drive file=win11-2.qcow2 \
                -snapshot \
                -nic bridge,br=br0,model=virtio-net-pci,helper=/run/wrappers/bin/qemu-bridge-helper \
                -monitor stdio \
                -vga qxl \
                -device usb-tablet \
                -device virtio-serial \
                -display vnc=:1,password=on,lossy=on
        """,
        "wireguard": "10.100.1.251"
    }
}
