#!/usr/bin/env python3
from pathlib import Path

def length(n):
    if n < 128: return bytes([n])
    b=n.to_bytes((n.bit_length()+7)//8,'big')
    return bytes([0x80|len(b)])+b

def tlv(tag, value): return bytes([tag])+length(len(value))+value

def integer(tag, value):
    b=value.to_bytes(max(1,(value.bit_length()+7)//8),'big')
    if b[0]&0x80: b=b'\x00'+b
    return tlv(tag,b)

def msg(mid, op): return tlv(0x30, integer(0x02,mid)+op)

# Anonymous simple bind keeps the benchmark self-contained and avoids credentials.
bind=msg(1,tlv(0x60,integer(0x02,3)+tlv(0x04,b'')+tlv(0x80,b'')))
# RootDSE base-object search is available on a fresh directory instance.
search_body=(tlv(0x04,b'')+tlv(0x0a,b'\x00')+tlv(0x0a,b'\x00')+
             integer(0x02,0)+integer(0x02,0)+tlv(0x01,b'\x00')+
             tlv(0x87,b'objectClass')+tlv(0x30,b''))
search=msg(2,tlv(0x63,search_body))
base=Path(__file__).parent/'seeds';base.mkdir(exist_ok=True)
(base/'anonymous-bind-search.ldap').write_bytes(bind+search)
(base/'bind.ldap').write_bytes(bind)
print(f'wrote {len(bind)}-byte bind and {len(search)}-byte rootDSE search')
