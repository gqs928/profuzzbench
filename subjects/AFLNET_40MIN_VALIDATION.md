# AFLNet 40-minute validation

The targets below were built from the pinned upstream revisions listed in
[`UPSTREAM_VERSIONS.md`](UPSTREAM_VERSIONS.md) and fuzzed with AFLNet for 2,400
seconds per target. Each fuzzer container was limited to one CPU. The timing is
measured around the AFLNet process; coverage replay was skipped for this runtime
check.

| Target | AFLNet runtime (s) | Container exit | Unique crashes | Unique hangs |
|---|---:|---:|---:|---:|
| forked-daapd | 2400.035 | 0 | 0 | 0 |
| DCMTK | 2401.154 | 0 | 0 | 0 |
| dnsmasq | 2400.011 | 0 | 0 | 0 |
| TinyDTLS | 2400.040 | 0 | 0 | 0 |
| BFTPD | 2400.028 | 0 | 0 | 0 |
| LightFTP | 2401.169 | 0 | 0 | 0 |
| ProFTPD | 2400.013 | 0 | 0 | 0 |
| Pure-FTPd | 2400.012 | 0 | 0 | 1 |
| Live555 | 2400.019 | 0 | 0 | 0 |
| Kamailio | 2400.072 | 0 | 0 | 0 |
| Exim | 2401.083 | 0 | 0 | 1 |
| OpenSSH | 2400.009 | 0 | 0 | 0 |
| OpenSSL | 2400.020 | 0 | 0 | 1 |

## Hang follow-up

- Exim: AFLNet recorded one unique hang. Two direct replays returned normal SMTP
  responses; the hang did not reproduce.
- Pure-FTPd: the saved input completed a full direct replay and received FTP
  responses. It did not crash or leave the server persistently hung.
- OpenSSL: the saved input received no TLS response; the one-connection test
  server closed normally. No crash or persistent process hang was observed.

No target produced a unique crash in its 40-minute run. AFLNet's unique-hang
counts are retained above even where direct replay did not reproduce a persistent
server hang.
