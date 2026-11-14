SIP/2.0 401 Unauthorized
Via: SIP/2.0/UDP client.example.com:5060;branch=z9hG4bKnashds7
From: Bob <sip:bob@example.com>;tag=456248
To: Bob <sip:bob@example.com>;tag=84756
Call-ID: 843817637684230@client.example.com
CSeq: 1826 REGISTER
WWW-Authenticate: Digest realm="example.com", nonce="84a7de9a8a9c", algorithm=MD5, qop="auth"
Proxy-Authenticate: Digest realm="proxy.example.com", nonce="89a7ce1234ab", algorithm=SHA-256, qop="auth,auth-int"
Content-Length: 0

