import os
import socket

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def find_next_free_port(port: int) -> int:
    p = port
    while is_port_in_use(p):
        p += 1
    return p


def gen_mac_address():
    r = os.urandom(3)
    return f"52:54:00:{r.hex(sep=':')}" # use qemu prefix
