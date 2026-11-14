#!/usr/bin/env python3
import argparse
import json
import socket

def read_reply(sock):
    lines=[]
    while True:
        line=b''
        while not line.endswith(b'\n'):
            chunk=sock.recv(1)
            if not chunk: raise RuntimeError('SMTP connection closed mid-reply')
            line += chunk
        lines.append(line.decode('ascii','replace').rstrip())
        if len(line) < 4 or line[3:4] != b'-': return '\n'.join(lines)

def command(sock, value, prefix):
    sock.sendall(value + b'\r\n')
    reply=read_reply(sock)
    if not reply.startswith(prefix.decode()):
        raise RuntimeError(f'{value!r}: expected {prefix!r}, got {reply!r}')
    return reply

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--host',default='127.0.0.1')
    ap.add_argument('--port',type=int,default=2525)
    ap.add_argument('--timeout',type=float,default=5)
    ap.add_argument('--output')
    args=ap.parse_args()
    transcript=[]
    with socket.create_connection((args.host,args.port),timeout=args.timeout) as s:
        s.settimeout(args.timeout)
        greeting=read_reply(s)
        if not greeting.startswith('220'): raise RuntimeError(f'bad greeting: {greeting!r}')
        transcript.append(greeting)
        for value,prefix in [(b'EHLO fuzzer.invalid',b'250'),
                             (b'MAIL FROM:<sender@fuzz.invalid>',b'250'),
                             (b'RCPT TO:<fuzzmail@fuzz.invalid>',b'250'),
                             (b'DATA',b'354')]:
            transcript.append(command(s,value,prefix))
        s.sendall(b'Subject: baseline\r\n\r\nbody\r\n.\r\n')
        delivered=read_reply(s)
        if not delivered.startswith('250'): raise RuntimeError(f'mail queue failed: {delivered!r}')
        transcript.append(delivered)
        transcript.append(command(s,b'QUIT',b'221'))
    result={'status':'pass','target':'OpenSMTPD 7.9.0p0','host':args.host,'port':args.port,
            'transcript':transcript}
    encoded=json.dumps(result,indent=2)+'\n'
    if args.output:
        with open(args.output,'w',encoding='utf8') as f: f.write(encoded)
    else: print(encoded,end='')

if __name__=='__main__': main()
