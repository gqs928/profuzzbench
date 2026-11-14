#!/usr/bin/env python3
"""Replay AFLNet MySQL classic-protocol queue cases through the auth proxy."""
import json, pathlib, socket, struct, sys, time

def frames(data):
    pos=0
    while pos+4<=len(data):
        n=data[pos]|data[pos+1]<<8|data[pos+2]<<16
        if pos+4+n>len(data): break
        yield data[pos+3],data[pos+4:pos+4+n]
        pos+=4+n

def main():
    if len(sys.argv)!=3: raise SystemExit('usage: replay_queue.py AFLNET_OUT PROXY_PORT')
    root=pathlib.Path(sys.argv[1]); port=int(sys.argv[2]); files=sorted(p for p in root.glob('**/queue/id:*') if p.is_file())
    out={'queue_files':len(files),'connected':0,'connection_errors':0,'timeouts':0,'response_bytes':0,'response_packets':0,'ok_packets':0,'error_packets':0,'eof_packets':0,'result_header_packets':0,'samples':[]}
    for path in files:
        data=bytearray()
        try:
            with socket.create_connection(('127.0.0.1',port),timeout=5) as s:
                out['connected']+=1; s.settimeout(.35); s.sendall(path.read_bytes()); deadline=time.monotonic()+1.5
                while time.monotonic()<deadline:
                    try:
                        b=s.recv(65536)
                        if not b: break
                        data.extend(b)
                    except socket.timeout: out['timeouts']+=1; break
        except OSError: out['connection_errors']+=1
        fs=list(frames(data)); markers=[p[0] for _,p in fs if p]
        out['response_bytes']+=len(data); out['response_packets']+=len(fs)
        out['ok_packets']+=markers.count(0x00); out['error_packets']+=markers.count(0xff); out['eof_packets']+=markers.count(0xfe)
        out['result_header_packets']+=sum(1 for x in markers if 0<x<0xfb)
        out['samples'].append({'file':path.name,'bytes_received':len(data),'response_packets':len(fs),'error_packets':markers.count(0xff),'eof_packets':markers.count(0xfe)})
    (root/'queue-replay.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='samples'},indent=2))
if __name__=='__main__': main()
