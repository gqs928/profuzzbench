#!/usr/bin/env python3
import socket
from pathlib import Path

def read_exact(f, n):
    data=f.read(n)
    if len(data)!=n: raise RuntimeError(f'expected {n} bytes, got {len(data)}')
    return data

def recv_ldap_frame(f):
    head=read_exact(f,2)
    if head[0]!=0x30: raise RuntimeError(f'bad LDAP outer tag: {head.hex()}')
    first=head[1]; length=first; raw=b''
    if length&0x80:
        n=length&0x7f
        if n==0 or n>4: raise RuntimeError('invalid BER length width')
        b=read_exact(f,n); raw+=b; length=int.from_bytes(b,'big')
    return head+raw+read_exact(f,length)

def read_tlv(data, offset):
    if offset + 2 > len(data): raise RuntimeError('truncated LDAP BER TLV')
    tag=data[offset]; first=data[offset+1]; pos=offset+2
    if first & 0x80:
        width=first & 0x7f
        if width == 0 or width > 4 or pos+width > len(data): raise RuntimeError('invalid LDAP BER length')
        length=int.from_bytes(data[pos:pos+width], 'big'); pos+=width
    else: length=first
    end=pos+length
    if end > len(data): raise RuntimeError('LDAP BER value exceeds frame')
    return tag, data[pos:end], end

def parse_message(frame):
    tag, content, end=read_tlv(frame, 0)
    if tag != 0x30 or end != len(frame): raise RuntimeError('invalid LDAPMessage sequence')
    msgid, _, pos=read_tlv(content, 0)
    if msgid != 0x02: raise RuntimeError('LDAPMessage is missing messageID')
    return read_tlv(content, pos)[:2]

def parse_result_code(operation):
    tag, value, _=read_tlv(operation, 0)
    if tag != 0x0a or not value: raise RuntimeError('LDAP response is missing resultCode')
    return int.from_bytes(value, 'big', signed=True)

def main():
    data=(Path(__file__).parent/'seeds/anonymous-bind-search.ldap').read_bytes()
    # Parse generated BER into consecutive complete LDAPMessage frames.
    frames=[]; off=0
    while off<len(data):
        if data[off]!=0x30: raise RuntimeError('seed does not start with LDAPMessage')
        i=off+1; first=data[i]; i+=1
        if first&0x80:
            n=first&0x7f; length=int.from_bytes(data[i:i+n],'big'); i+=n
        else: length=first
        end=i+length; frames.append(data[off:end]); off=end
    if len(frames)!=2: raise RuntimeError(f'expected bind + search, got {len(frames)}')
    with socket.create_connection(('127.0.0.1',1389),timeout=10) as s:
        s.settimeout(10); f=s.makefile('rb')
        s.sendall(frames[0]); bind=recv_ldap_frame(f)
        bind_tag, bind_op=parse_message(bind)
        if bind_tag!=0x61 or parse_result_code(bind_op)!=0: raise RuntimeError(f'bind failed: {bind.hex()}')
        s.sendall(frames[1]); seen_done=False
        for _ in range(16):
            response=recv_ldap_frame(f)
            op_tag, op=parse_message(response)
            if op_tag==0x65:
                if parse_result_code(op)!=0: raise RuntimeError(f'search failed: {response.hex()}')
                seen_done=True; break
        if not seen_done: raise RuntimeError('SearchResultDone not received')
    print('LDAP smoke passed: anonymous BindResponse success and RootDSE SearchResultDone success')
if __name__=='__main__': main()
