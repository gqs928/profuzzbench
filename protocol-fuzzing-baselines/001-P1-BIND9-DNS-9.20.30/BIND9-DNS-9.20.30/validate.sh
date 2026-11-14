#!/usr/bin/env bash
set -euo pipefail

out=${1:-/work/results/validation}
mkdir -p "$out"
/opt/bind-afl/sbin/named -g -c /work/named.conf -n 1 -U 1 >"$out/named.log" 2>&1 &
named_pid=$!
cleanup() {
  kill -TERM "$named_pid" 2>/dev/null || true
  wait "$named_pid" 2>/dev/null || true
}
trap cleanup EXIT

python3 - "$out/service-smoke.json" <<'PY'
import json, socket, struct, sys, time
out = sys.argv[1]
def encode_name(name):
    return b''.join(bytes([len(x)])+x.encode() for x in name.split('.'))+b'\0'
def make_query(ident, tcp=False):
    msg=struct.pack('!HHHHHH',ident,0x0100,1,0,0,0)+encode_name('www.example.test')+struct.pack('!HH',1,1)
    return struct.pack('!H',len(msg))+msg if tcp else msg
def wait_server():
    for _ in range(100):
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.settimeout(.2)
            s.sendto(make_query(0x2040),('127.0.0.1',5353)); data,_=s.recvfrom(4096); s.close()
            if len(data)>=12 and data[0:2]==b'\x20\x40' and data[2]&0x80: return
        except OSError: time.sleep(.1)
    raise SystemExit('BIND did not answer the UDP smoke query')
wait_server()
records=[]
for proto in ('udp','tcp'):
    qid=0x2041 if proto=='udp' else 0x2042
    payload=make_query(qid,proto=='tcp')
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM if proto=='udp' else socket.SOCK_STREAM) as s:
        s.settimeout(3)
        if proto=='udp':
            s.sendto(payload,('127.0.0.1',5353)); data,_=s.recvfrom(4096)
        else:
            s.connect(('127.0.0.1',5353)); s.sendall(payload)
            head=s.recv(2)
            if len(head)!=2: raise SystemExit('DNS/TCP length prefix missing')
            size=struct.unpack('!H',head)[0]; chunks=b''
            while len(chunks)<size:
                block=s.recv(size-len(chunks))
                if not block: break
                chunks+=block
            data=chunks
    ok=len(data)>=12 and data[:2]==struct.pack('!H',qid) and bool(data[2]&0x80)
    records.append({'transport':proto,'response_bytes':len(data),'rcode':data[3]&15 if len(data)>=4 else None,'pass':ok})
    if not ok: raise SystemExit(f'{proto} DNS response did not match the query')
open(out,'w').write(json.dumps({'protocol':'DNS','bind_version':'9.20.30','results':records},indent=2)+'\n')
PY

test "$(/opt/bind-afl/sbin/named -V 2>&1 | head -1 | grep -c 'BIND 9.20.30')" -eq 1
kill -0 "$named_pid"
