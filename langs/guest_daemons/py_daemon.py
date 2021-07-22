import importlib.util
import json
import socket
import sys
import time
import traceback
from typing import Any, Generator

SERVER: socket.socket = None  # type: ignore
GENERATOR: Generator[str, Any, None] = None  # type: ignore


def run_client():
    global SERVER
    port = int(sys.argv[1])
    SERVER = socket.create_connection(("127.0.0.1", port))
    SERVER.sendall(_encode({"type": "connect", "lang": "Python"}))

    while True:
        try:
            _daemon_loop()
        except BrokenPipeError:  # Server has closed
            SERVER.close()
            break
        except:
            tb = traceback.format_exc()
            crash_message = {"type": "crash", "result": tb}
            SERVER.sendall(_encode(crash_message))


def _daemon_loop() -> None:
    global SERVER, GENERATOR
    raw = SERVER.recv(1024)
    if raw:
        json_data = _decode(raw)
        gen_param = None
        if json_data["type"] == "call_func":
            script = _get_script(json_data["func_path"])
            GENERATOR = script.reserved_name()  # type: ignore
        elif json_data["type"] == "ditlang_callback":
            gen_param = json_data["result"]

        try:
            gen_result = GENERATOR.send(gen_param)
            exe_message = _encode({"type": "exe_ditlang", "result": gen_result})
            SERVER.sendall(exe_message)
        except StopIteration:
            finish_message = _encode({"type": "finish_func", "result": None})
            SERVER.sendall(finish_message)
    else:
        SERVER.sendall(_encode({"type": "heart"}))
    time.sleep(0.001)  # Prevent pinning the CPU


def _get_script(path: str):
    name = path[path.rfind("/") + 1 :]
    spec = importlib.util.spec_from_file_location(name, path)
    script = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(script)  # type: ignore
    return script


def _encode(message: dict):
    return json.dumps(message).encode()


def _decode(message: bytes):
    return json.loads(message.decode())


run_client()
