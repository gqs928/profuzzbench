#!/usr/bin/env python3
import argparse
import json
import socket

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=2525)
    ap.add_argument('--timeout', type=float, default=5)
    ap.add_argument('--output')
    args = ap.parse_args()
    commands = [b'EHLO baseline.invalid', b'MAIL FROM:<sender@fuzz.invalid>',
                b'RCPT TO:<user@fuzz.invalid>', b'DATA']
    replies = []
    expected_codes = [b'250', b'250', b'250', b'354']
    with socket.create_connection((args.host, args.port), timeout=args.timeout) as sock:
        sock.settimeout(args.timeout)
        greeting = sock.recv(4096)
        replies.append(greeting.decode('utf-8', 'replace'))
        if not greeting.startswith(b'220'):
            raise RuntimeError(f'SMTP greeting failed: {greeting!r}')
        for command, expected in zip(commands, expected_codes):
            sock.sendall(command + b'\r\n')
            reply = sock.recv(4096)
            replies.append(reply.decode('utf-8', 'replace'))
            if not reply:
                raise RuntimeError(f'connection closed after {command!r}')
            if not reply.startswith(expected):
                raise RuntimeError(f'{command!r} expected {expected!r} but received {reply!r}')
        body = b'Subject: smoke\r\n\r\nbody\r\n.\r\n'
        sock.sendall(body)
        reply = sock.recv(4096)
        replies.append(reply.decode('utf-8', 'replace'))
        if not reply.startswith(b'250'):
            raise RuntimeError(f'message enqueue/discard failed: {reply!r}')
        sock.sendall(b'QUIT\r\n')
        reply = sock.recv(4096)
        replies.append(reply.decode('utf-8', 'replace'))
        if not reply.startswith(b'221'):
            raise RuntimeError(f'QUIT failed: {reply!r}')
    result = {'status': 'pass', 'host': args.host, 'port': args.port,
              'commands': [x.decode('ascii', 'replace') for x in commands] +
                          ['Subject: smoke\\r\\n\\r\\nbody\\r\\n.','QUIT'], 'replies': replies}
    encoded = json.dumps(result, indent=2) + '\n'
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(encoded)
    else:
        print(encoded, end='')

if __name__ == '__main__':
    main()
