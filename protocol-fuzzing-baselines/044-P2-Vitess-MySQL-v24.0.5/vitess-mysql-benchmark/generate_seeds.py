#!/usr/bin/env python3
"""Create deterministic MySQL classic-protocol COM_QUERY seeds."""
import argparse, hashlib, json
from pathlib import Path

def packet(payload, seq=0):
    n=len(payload)
    return bytes((n&255,(n>>8)&255,(n>>16)&255,seq&255))+payload

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='seeds'); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    queries={
      '01-select-one':'SELECT 1',
      '02-server-version':'SELECT VERSION()',
      '03-current-database':'SELECT DATABASE()',
      '04-show-databases':'SHOW DATABASES',
      '05-connection-id':'SELECT CONNECTION_ID()',
      '06-read-only-transaction':'START TRANSACTION READ ONLY',
      '07-syntax-error':'SELECT * FROM aflnet_missing_table',
      '08-empty-query':'',
    }
    manifest=[]
    for name,sql in queries.items():
        data=packet(b'\x03'+sql.encode('utf-8'))
        path=out/(name+'.mysql'); path.write_bytes(data)
        manifest.append({'file':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'sql':sql})
    (out.parent/(out.name+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'generated={len(manifest)} protocol=MySQL classic COM_QUERY')
if __name__=='__main__': main()
