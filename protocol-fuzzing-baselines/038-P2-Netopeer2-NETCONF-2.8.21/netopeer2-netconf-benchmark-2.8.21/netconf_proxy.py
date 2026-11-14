#!/usr/bin/env python3
"""Bridge AFLNet's clear-text NETCONF stream to Netopeer2's SSH subsystem."""
import os
import select
import socket
import subprocess

HOST = os.environ.get("NETCONF_PROXY_HOST", "0.0.0.0")
PORT = int(os.environ.get("NETCONF_PROXY_PORT", "1830"))
SSH_PORT = int(os.environ.get("NETCONF_SSH_PORT", "830"))
KEY = os.environ.get("NETCONF_CLIENT_KEY", "/opt/benchmark/configs/client_key")


def bridge(client):
    argv = ["ssh", "-T", "-p", str(SSH_PORT), "-s", "-i", KEY,
            "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
            "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR", "root@127.0.0.1", "netconf"]
    child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, bufsize=0)
    try:
        streams = [client, child.stdout]
        while child.poll() is None:
            readable, _, _ = select.select(streams, [], [], 0.5)
            for source in readable:
                if source is client:
                    data = client.recv(65536)
                    if not data:
                        return
                    child.stdin.write(data)
                else:
                    data = os.read(child.stdout.fileno(), 65536)
                    if not data:
                        return
                    client.sendall(data)
    finally:
        try:
            child.stdin.close()
        except OSError:
            pass
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((HOST, PORT))
        listener.listen(128)
        while True:
            client, _ = listener.accept()
            with client:
                try:
                    bridge(client)
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass


if __name__ == "__main__":
    main()
