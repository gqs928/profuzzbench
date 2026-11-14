MESSAGE sip:user@example.com SIP/2.0
Via: SIP/2.0/TCP client.example.com;branch=z9hG4bK74bf9
From: <sip:sender@example.com>;tag=9fxced76sl
To: <sip:user@example.com>
Call-ID: 3848276298220188511@client.example.com
CSeq: 1 MESSAGE
Content-Type: multipart/alternative;boundary="----=_Part_123"
Content-Length: 245

------=_Part_123
Content-Type: text/plain; charset=UTF-8

Plain text version of message
------=_Part_123
Content-Type: text/html; charset=UTF-8

<html><body>HTML version</body></html>
------=_Part_123--
