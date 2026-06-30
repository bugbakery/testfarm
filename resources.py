from hosts import get_conn

def _lock_file(resource: str):
    return f"testfarm.{resource}.lock"

def acquire_resource_lock(host: str, resource: str):
    lock_file = _lock_file(resource)

    get_conn(host).run(f"""
        if [ ! -e {lock_file} ]; then
            touch {lock_file}
        else
            exit 1
        fi
    """, hide="both")

def release_resource_lock(host: str, resource: str):
    lock_file = _lock_file(resource)

    get_conn(host).run(f"rm -f {lock_file}", hide="both")
