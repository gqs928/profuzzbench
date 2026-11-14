#!/usr/bin/env python3
"""Replay AFLNet queue files on fresh STOMP TCP connections."""
import json, pathlib, socket, sys, time
root=pathlib.Path(sys.argv[1]); files=sorted(p for p in root.glob('**/queue/id:*') if p.is_file())
result={'queue_files':len(files),'connected':0,'frames':0,'timeouts':0,'resets':0,'errors':0}
for path in files:
    try:
        with socket.create_connection(('127.0.0.1',61613),timeout=3) as s:
            result['connected']+=1; s.settimeout(.8); s.sendall(path.read_bytes())
            deadline=time.monotonic()+1.2
            got=False
            while time.monotonic()<deadline:
                try:
                    data=s.recv(8192)
                    if not data: break
                    if b'\x00' in data: got=True; break
                except socket.timeout: result['timeouts']+=1; break
            if got: result['frames']+=1
    except ConnectionResetError: result['resets']+=1
    except (OSError,TimeoutError): result['errors']+=1
print(json.dumps(result,indent=2,sort_keys=True))
