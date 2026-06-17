from fabric import Connection
import invoke
from functools import lru_cache
from time import time
from tqdm import tqdm

hosts = {
    "jump": {
        "public": "beta.transcribee.net",
        "wireguard": "10.100.0.1",
        "user": "root",
    },
    "mac-mini": {
        "wireguard": "10.100.0.3",
        "user": "admin",
    },
    "desktop-router": {
        "wireguard": "10.100.1.2"
    },
    "desktop-intel": {
        "wireguard": "10.100.1.253",
        "mac": "34:5a:60:05:0b:85",
        "user": "admin",
        "password": "admin",
        "boot_time": 35,
    }
}

@lru_cache
def get_conn(host):
    host = hosts[host]
    args = {}
    if "public" in host:
        args["host"] = host["public"]
    else:
        args["gateway"] = get_conn("jump")
        args["host"] = host["wireguard"]
    if "user" in host:
        args["user"] = host["user"]
    if "password" in host:
        args["connect_kwargs"] = dict(password=host["password"])
    return Connection(**args)


def is_reachable(host):
    host = hosts[host]
    try:
        if "public" in host:
            return invoke.run(f"ping -c1 -W0.5 {host['public']}", hide="out").ok
        else:
            return get_conn("jump").run(f"ping -c1 -W0.5 {host['wireguard']}", hide="out").ok
    except invoke.exceptions.UnexpectedExit:
        return False


def wake(host):
    if is_reachable(host):
        print(f"-> host {host} is already running")
    else:
        print(f"-> booting host {host}...")
        cmd = f"curl -X POST http://{hosts["desktop-router"]["wireguard"]}/wake/{hosts[host]["mac"]}"
        get_conn("jump").run(cmd, hide="both")
        start_time = time()
        duration = hosts[host].get("boot_time", None)
        progress_bar = tqdm(total=duration, bar_format="{bar}{elapsed}<{remaining}")
        while not is_reachable(host):
            progress_bar.update(time() - start_time - progress_bar.n)
        progress_bar.close()
        duration = time() - start_time
        print(f"booting took {duration:.01f}s")
    return
