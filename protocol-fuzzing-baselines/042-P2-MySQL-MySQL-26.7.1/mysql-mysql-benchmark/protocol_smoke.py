#!/usr/bin/env python3
"""Smoke-test SQL responses through the loopback MySQL auth proxy."""
import argparse, json, socket

def packet(payload):
    n=len(payload); return bytes((n&255,(n>>8)&255,(n>>16)&255,0))+payload

def exact(sock,n):
    out=bytearray()
    while len(out)<n:
        part=sock.recv(n-len(out))
        if not part: raise ConnectionError('proxy closed before a complete MySQL packet')
        out.extend(part)
    return bytes(out)

def recv_packet(sock):
    h=exact(sock,4); n=h[0]|h[1]<<8|h[2]<<16
    if n>0xffffff: raise ValueError('invalid MySQL packet length')
    return h[3],exact(sock,n)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--host',default='127.0.0.1'); ap.add_argument('--port',type=int,required=True); ap.add_argument('--sql',default='SELECT 1'); ap.add_argument('--timeout',type=float,default=5); ap.add_argument('--quiet',action='store_true'); a=ap.parse_args()
    try:
        with socket.create_connection((a.host,a.port),timeout=a.timeout) as s:
            s.settimeout(.35); s.sendall(packet(b'\x03'+a.sql.encode()+b'\0'))
            frames=[]
            while len(frames)<128:
                try: frames.append(recv_packet(s))
                except socket.timeout: break
            if not frames: raise RuntimeError('no SQL response packets')
            errors=sum(1 for _,p in frames if p[:1]==b'\xff')
            result={'sql':a.sql,'response_packet_count':len(frames),'sequence_ids':[q for q,_ in frames],
                    'packet_markers':[p[0] if p else None for _,p in frames], 'error_packets':errors,
                    'has_result_or_ok':any(p and p[0] in (0x00,0x01,0xfb,0xfe) for _,p in frames)}
            if errors or not result['has_result_or_ok']: raise RuntimeError(f'SQL response not clean: {result}')
            if not a.quiet: print(json.dumps(result,indent=2))
    except Exception as exc:
        if not a.quiet: print(f'MySQL protocol smoke failed: {exc}')
        return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
