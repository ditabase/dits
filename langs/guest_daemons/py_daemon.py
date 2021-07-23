import importlib.util
import json
import socket
import sys
import time
import traceback

SERVER: socket.socket = None  # type: ignore
GENERATOR_STACK = []


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
    global SERVER, GENERATOR_STACK
    raw = SERVER.recv(1024)
    if raw:
        json_data = _decode(raw)
        gen_param = None
        if json_data["type"] == "call_func":
            script = _get_script(json_data["func_path"])
            gen = script.reserved_name()  # type: ignore
            GENERATOR_STACK.append(gen)
        elif json_data["type"] == "ditlang_callback":
            gen_param = json_data["result"]
            gen = GENERATOR_STACK[-1]
        elif json_data["type"] == "return_keyword":
            # The function ended with a return keyword,
            # this message is just letting us know.
            return _finish()
        else:
            raise ValueError("Unknown message type")

        try:
            gen_result = gen.send(gen_param)
            exe_message = _encode({"type": "exe_ditlang", "result": gen_result})
            SERVER.sendall(exe_message)
        except StopIteration:
            _finish()
    else:
        SERVER.sendall(_encode({"type": "heart"}))
    time.sleep(0.001)  # Prevent pinning the CPU


def _finish() -> None:
    GENERATOR_STACK.pop()
    finish_message = _encode({"type": "finish_func", "result": None})
    SERVER.sendall(finish_message)


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
