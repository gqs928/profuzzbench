#!/usr/bin/env python3
"""Reproduce an AFLNet-generated DEBUG SEGFAULT sequence on ASan Redis."""
from __future__ import annotations
import hashlib, json, signal, socket, subprocess, sys, tempfile, time
from pathlib import Path

binary, config, sample, outdir = map(Path, sys.argv[1:])
outdir.mkdir(parents=True, exist_ok=True)
data=sample.read_bytes()
log_path=outdir/"debug-enabled-redis.log"
with tempfile.TemporaryDirectory(prefix="redis-debug-crash-repro-") as tmp, log_path.open("wb") as log:
    proc=subprocess.Popen([str(binary),str(config),"--dir",tmp],stdout=log,stderr=subprocess.STDOUT)
    sock=None
    try:
        limit=time.monotonic()+10
        while time.monotonic()<limit:
            if proc.poll() is not None: raise RuntimeError(f"Redis exited at startup: {proc.returncode}")
            try:
                sock=socket.create_connection(("127.0.0.1",6379),timeout=.25)
                sock.settimeout(.05); break
            except OSError: time.sleep(.025)
        if sock is None: raise RuntimeError("Redis did not start")
        sock.sendall(data)
        deadline=time.monotonic()+5
        received=bytearray()
        while time.monotonic()<deadline and proc.poll() is None:
            try:
                block=sock.recv(65536)
            except socket.timeout: continue
            except OSError: break
            if not block: break
            received.extend(block)
        code=proc.poll()
        if code is None:
            try: code=proc.wait(timeout=max(0,deadline-time.monotonic()))
            except subprocess.TimeoutExpired: raise RuntimeError("DEBUG SEGFAULT did not terminate Redis")
        log.flush()
        log_text=log_path.read_bytes()
        if code == 0: raise RuntimeError("Redis exited cleanly instead of crashing")
        if code != -signal.SIGSEGV and b"AddressSanitizer" not in log_text and b"runtime error:" not in log_text:
            raise RuntimeError(f"Redis exited abnormally but not as a recorded sanitizer/SIGSEGV crash: {code}")
        result={"sample":str(sample),"sample_sha256":hashlib.sha256(data).hexdigest(),"debug_enabled_config":str(config),"redis_returncode":code,"sigsegv":code == -signal.SIGSEGV,"received_before_crash_hex":bytes(received).hex(),"result":"pass"}
    finally:
        if sock is not None: sock.close()
        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)
(outdir/"debug-crash-replay.json").write_text(json.dumps(result,indent=2)+"\n")
print(f"PASS: AFLNet-generated input reproduced abnormal Redis termination ({result['redis_returncode']})")
