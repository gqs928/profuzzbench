#!/usr/bin/env python3
"""Replay BER LDAP queue inputs and count complete LDAPMessage responses."""
import json,pathlib,socket,sys,time,os
root=pathlib.Path(sys.argv[1]);host=os.environ.get('LDAP_HOST','127.0.0.1');port=int(os.environ.get('LDAP_PORT','1389'))
r={'queue_files':0,'connected':0,'responses':0,'no_response':0,'no_response_files':[],'timeouts':0,'resets':0,'errors':0}
def exact(s,n):
 b=b''
 while len(b)<n:
  q=s.recv(n-len(b))
  if not q:raise EOFError
  b+=q
 return b
def recv_frame(s):
 h=exact(s,2)
 if h[0]!=0x30:raise ValueError('invalid LDAP outer tag '+h.hex())
 first=h[1];raw=b''
 if first&0x80:
  k=first&0x7f
  if not k or k>4:raise ValueError('invalid BER length width')
  raw=exact(s,k);length=int.from_bytes(raw,'big')
 else:length=first
 return h+bytes([first])+raw+exact(s,length)
for p in sorted(root.glob('**/queue/id:*')):
 if not p.is_file():continue
 r['queue_files']+=1;got=0
 try:
  with socket.create_connection((host,port),timeout=3) as s:
   r['connected']+=1;s.sendall(p.read_bytes());deadline=time.monotonic()+1.2
   while time.monotonic()<deadline:
    s.settimeout(max(.01,deadline-time.monotonic()))
    try:recv_frame(s);got+=1;r['responses']+=1
    except socket.timeout:r['timeouts']+=1;break
    except EOFError:break
 except ConnectionResetError:r['resets']+=1
 except (OSError,ValueError,EOFError):r['errors']+=1
 if got==0:r['no_response']+=1;r['no_response_files'].append(p.name)
print(json.dumps(r,indent=2,sort_keys=True))
