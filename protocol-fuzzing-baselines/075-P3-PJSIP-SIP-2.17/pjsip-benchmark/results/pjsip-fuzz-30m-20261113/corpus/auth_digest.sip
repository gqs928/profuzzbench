REGISTER sip:registrar.example.com SIP/2.0
Via: SIP/2.0/UDP client.example.com:5060;branch=z9hG4bKnashds7
From: Bob <sip:bob@example.com>;tag=456248
To: Bob <sip:bob@example.com>
Call-ID: 843817637684230@client.example.com
CSeq: 1826 REGISTER
Authorization: Digest username="bob", realm="example.com", nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", uri="sip:registrar.example.com", qop=auth, nc=00000001, cnonce="0a4f113b", response="6629fae49393a05397450978507c4ef1", opaque="5ccc069c403ebaf9f0171e9517f40e41"
Contact: <sip:bob@client.example.com>
Content-Length: 0

