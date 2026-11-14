INVITE sip:user@foo SIP/2.0
from: Hi I'm Joe <sip:joe.user@bar.otherdomain.com>;tag=123457890123456To: Fellow User <sip:user@foo.bar.domain.com>
Call-ID: 12345678901234567890@bar
Content-Length: 0
CSeq: 123456 INVITE
Contact: <sip:joe@bar> ; q=0.5;expires=3600,sip:user@host;q=0.500  ,sip:user2@host2
Content-Type: text/html ; charset=ISO-8859-4Route: <sip:bigbox3.site3.atlanta.com;lr>,
  <sip:server10.biloxi.com;lr>Record-Route: <sip:server10.biloxi.com>,
  <sip:bigbox3.site3.atlanta.com;lr>
v: SIP/2.0/SCTP bigbox3.site3.atlanta.com;branch=z9hG4bK77ef4c230
Via: SIP/2.0/UDP pc33.atlanta.com;branch=z9hG4bKnashds8
 ;received=192.0.2.1
Via: SIP/2.0/UDP 10.2.1.1, SIP/2.0/TCP 192.168.1.1
Organization: Max-Forwards: 70
X-Header: 
P-Associated-URI:

