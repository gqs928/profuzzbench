REFER sip:bob@biloxi.com SIP/2.0
Via: SIP/2.0/UDP agenta.atlanta.example.com;branch=z9hG4bK2293940223
From: <sip:alice@atlanta.example.com>;tag=7553452
To: <sip:bob@biloxi.com>;tag=923457
Call-ID: 436f6b7a3fa2@atlanta.example.com
CSeq: 1 REFER
Refer-To: <sip:carol@chicago.example.com?Replaces=98594362%40foo.com%3Bto-tag%3D25934%3Bfrom-tag%3D3413>
Refer-Sub: true
Referred-By: <sip:alice@atlanta.example.com>
Replaces: 98594362@foo.com;to-tag=25934;from-tag=3413
Contact: <sip:alice@atlanta.example.com>
Content-Length: 0

