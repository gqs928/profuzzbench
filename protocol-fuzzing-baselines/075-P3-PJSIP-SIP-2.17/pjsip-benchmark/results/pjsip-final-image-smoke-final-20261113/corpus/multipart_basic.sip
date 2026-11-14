INVITE sip:bob@biloxi.com SIP/2.0
Via: SIP/2.0/UDP pc33.atlanta.com;branch=z9hG4bKnashds8
To: Bob <sip:bob@biloxi.com>
From: Alice <sip:alice@atlanta.com>;tag=1928301774
Call-ID: a84b4c76e66710
CSeq: 314159 INVITE
Contact: <sip:alice@pc33.atlanta.com>
Content-Type: multipart/mixed;boundary=boundary42
Content-Length: 301

--boundary42
Content-Type: application/sdp

v=0
o=alice 2890844526 2890844526 IN IP4 pc33.atlanta.com
s=-
c=IN IP4 pc33.atlanta.com
t=0 0
m=audio 49170 RTP/AVP 0
--boundary42
Content-Type: text/plain

This is a text message
--boundary42--
