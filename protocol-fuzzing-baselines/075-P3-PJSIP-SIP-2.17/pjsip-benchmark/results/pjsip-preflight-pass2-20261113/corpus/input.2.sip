SIP/2.0 200 OK
Via: SIP/2.0/SCTP server10.biloxi.com;branch=z9hG4bKnashds8;rport;received=192.0.2.1
Via: SIP/2.0/UDP bigbox3.site3.atlanta.com;branch=z9hG4bK77ef4c2312983.1;received=192.0.2.2
Via: SIP/2.0/UDP pc33.atlanta.com;branch=z9hG4bK776asdhds ;received=192.0.2.3
Route: <sip:proxy.sipprovider.com>
Route: <sip:proxy.supersip.com:5060>
Max-Forwards: 70
To: Bob <sip:bob@biloxi.com>;tag=a6c85cf
From: Alice <sip:alice@atlanta.com>;tag=1928301774
Call-ID: a84b4c76e66710@pc33.atlanta.com
CSeq: 314159 INVITE
Contact: <sips:bob@192.0.2.4>
Content-Type: application/sdp
Content-Length: 150

v=0
o=alice 53655765 2353687637 IN IP4 pc33.atlanta.com
s=-
t=0 0
c=IN IP4 pc33.atlanta.com
m=audio 3456 RTP/AVP 0 1 3 99
a=rtpmap:0 PCMU/8000
