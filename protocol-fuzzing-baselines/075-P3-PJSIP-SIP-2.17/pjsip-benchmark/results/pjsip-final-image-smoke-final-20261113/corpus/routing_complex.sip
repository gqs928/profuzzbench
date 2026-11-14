INVITE sip:user@example.com SIP/2.0
Via: SIP/2.0/UDP proxy1.example.com;branch=z9hG4bK87asdks7
Via: SIP/2.0/UDP client.example.com;branch=z9hG4bKnashds8;received=192.0.2.1
Route: <sip:proxy1.example.com;lr>,<sip:proxy2.example.com;lr;transport=tcp>
Record-Route: <sip:proxy1.example.com;lr>,<sip:proxy2.example.com;lr>
From: Alice <sip:alice@atlanta.com>;tag=1234567
To: Bob <sip:user@example.com>
Call-ID: routing-test@atlanta.com
CSeq: 1 INVITE
Contact: <sip:alice@client.example.com;transport=udp>;+sip.instance="<urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf6>";expires=3600
Content-Length: 0

