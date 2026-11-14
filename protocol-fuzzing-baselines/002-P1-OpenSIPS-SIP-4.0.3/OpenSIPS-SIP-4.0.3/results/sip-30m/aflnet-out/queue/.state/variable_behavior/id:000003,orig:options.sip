OPTIONS sip:service@example.test SIP/2.0
Via: SIP/2.0/UDP 127.0.0.1:5062;branch=z9hG4bKbench-OPTIONS;rport
Max-Forwards: 70
From: <sip:fuzzer@example.test>;tag=bench
To: <sip:service@example.test>
Call-ID: options@benchmark.example
CSeq: 1 OPTIONS
Content-Length: 0

