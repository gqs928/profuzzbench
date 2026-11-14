#!/usr/bin/env python3
"""Validate ActiveMQ Classic STOMP 1.2 login, queue subscribe, send and delivery."""
import socket, time, uuid
HOST, PORT = '127.0.0.1', 61613

class FrameReader:
    def __init__(self, sock): self.sock, self.buf = sock, bytearray()
    def read(self, timeout=10):
        self.sock.settimeout(timeout)
        while b'\x00' not in self.buf:
            part=self.sock.recv(4096)
            if not part: raise RuntimeError(f'connection closed before STOMP frame: {bytes(self.buf)!r}')
            self.buf.extend(part)
            if len(self.buf)>1_000_000: raise RuntimeError('oversized STOMP frame')
        frame, _, tail=self.buf.partition(b'\x00'); self.buf=bytearray(tail); return bytes(frame).lstrip(b'\r\n')

def send_frame(sock, command, headers=None, body=b''):
    headers = headers or {}
    sock.sendall((command+'\n'+'\n'.join(f'{k}:{v}' for k,v in headers.items())+'\n\n').encode()+body+b'\x00')

def main():
    dest='/queue/bench-smoke-'+uuid.uuid4().hex
    with socket.create_connection((HOST, PORT), timeout=10) as s:
        reader=FrameReader(s)
        send_frame(s,'STOMP',{'accept-version':'1.2','host':'localhost','login':'admin','passcode':'admin'})
        connected=reader.read()
        if not connected.startswith(b'CONNECTED\n') and not connected.startswith(b'CONNECTED\r\n'):
            raise RuntimeError(f'expected CONNECTED, got {connected[:200]!r}')
        send_frame(s,'SUBSCRIBE',{'id':'smoke-1','destination':dest,'ack':'auto','receipt':'sub-1'})
        receipt=reader.read()
        if not receipt.startswith(b'RECEIPT\n') or b'receipt-id:sub-1' not in receipt:
            raise RuntimeError(f'subscribe receipt failed: {receipt[:200]!r}')
        send_frame(s,'SEND',{'destination':dest,'content-type':'text/plain'},b'smoke-payload')
        seen=[]
        for _ in range(3):
            msg=reader.read()
            seen.append(msg)
            if msg.startswith(b'MESSAGE\n') and b'smoke-payload' in msg: break
        if not any(m.startswith(b'MESSAGE\n') and b'smoke-payload' in m for m in seen):
            raise RuntimeError(f'message was not delivered: {[m[:150] for m in seen]!r}')
        send_frame(s,'DISCONNECT',{'receipt':'bye'})
    print('stomp_1_2_connect=PASS')
    print('stomp_subscribe_send_delivery=PASS')

if __name__ == '__main__': main()
