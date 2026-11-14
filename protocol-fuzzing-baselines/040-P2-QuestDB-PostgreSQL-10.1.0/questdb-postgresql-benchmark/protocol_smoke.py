#!/usr/bin/env python3
"""Minimal PostgreSQL frontend/backend wire smoke test."""
import argparse, socket, struct, sys

def packet(kind, payload): return kind + struct.pack("!I", len(payload) + 4) + payload
def exact(sock, n):
    data = bytearray()
    while len(data) < n:
        part = sock.recv(n - len(data))
        if not part: raise ConnectionError("peer closed before complete PostgreSQL frame")
        data.extend(part)
    return bytes(data)
def frame(sock):
    kind = exact(sock, 1); length = struct.unpack("!I", exact(sock, 4))[0]
    if length < 4 or length > 16*1024*1024: raise ValueError(f"invalid backend frame length {length}")
    return kind, exact(sock, length - 4)
def startup(user, database):
    params = b"user\0"+user.encode()+b"\0database\0"+database.encode()+b"\0client_encoding\0UTF8\0application_name\0aflnet-smoke\0\0"
    body = struct.pack("!I", 196608) + params
    return struct.pack("!I", len(body)+4) + body
def run(host, port, user, database, sql, timeout):
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout); sock.sendall(startup(user, database))
        kinds=[]; rows=errors=0
        while True:
            kind,payload=frame(sock); kinds.append(kind.decode("ascii","replace"))
            if kind == b"R":
                code=struct.unpack("!I", payload[:4])[0]
                if code == 3: sock.sendall(packet(b"p", b"quest\0"))
                elif code == 5: raise RuntimeError("unexpected MD5 authentication challenge")
                elif code != 0: raise RuntimeError(f"unsupported authentication request {code}")
            elif kind == b"E": errors+=1
            elif kind == b"D": rows+=1
            elif kind == b"Z": break
        sock.sendall(packet(b"Q", sql.encode()+b"\0"))
        while True:
            kind,payload=frame(sock); kinds.append(kind.decode("ascii","replace"))
            if kind == b"E": errors+=1
            elif kind == b"D": rows+=1
            elif kind == b"Z": break
        return {"backend_message_types":kinds,"data_rows":rows,"error_responses":errors,
                "query_completed":"C" in kinds,"ready_for_query":kinds[-1]=="Z"}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--host",default="127.0.0.1"); ap.add_argument("--port",type=int,default=8812)
    ap.add_argument("--user",default="admin"); ap.add_argument("--database",default="qdb"); ap.add_argument("--sql",default="SELECT 1")
    ap.add_argument("--timeout",type=float,default=5); ap.add_argument("--quiet",action="store_true"); a=ap.parse_args()
    try:
        r=run(a.host,a.port,a.user,a.database,a.sql,a.timeout)
        if not r["query_completed"] or not r["ready_for_query"]: raise RuntimeError(f"query did not complete cleanly: {r}")
        if not a.quiet: print(r)
        return 0
    except Exception as e:
        if not a.quiet: print(f"PostgreSQL-wire smoke failed: {e}",file=sys.stderr)
        return 1
if __name__=="__main__": raise SystemExit(main())
