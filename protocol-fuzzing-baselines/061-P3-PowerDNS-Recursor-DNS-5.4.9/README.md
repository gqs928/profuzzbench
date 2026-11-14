# PowerDNS Recursor 5.4.9 — DNS/TCP baseline

This profile targets the official PowerDNS Recursor 5.4 stable train, pinned to 5.4.9 (released 2026-10-26), the latest stable patch verified on 2026-11-12. The official 5.5 train remains prerelease. Installation uses PowerDNS's signed `noble-rec-54` repository and asserts the exact Debian package and executable versions.

The target loads an immutable local `fuzz.test` auth-zone, so corpus traffic does not depend on external DNS. The fuzzer sends DNS-over-TCP streams with RFC 7766 two-byte length prefixes to port 5300. Recursor may also bind UDP on that port; this profile sends and measures TCP only. TLS, DNSSEC signing, zone transfer, dynamic update, forwarding, and external recursion are outside the profile.

The AFLNet `DNS_TCP` adapter segments each length-prefixed request and maps response QR/opcode/AA/TC/RCODE fields to stable states. PowerDNS documents that records served from `auth_zones` do not set the DNS AA bit, so readiness and smoke checks require the expected response ID, QR, RCODE, and answer count rather than requiring AA. The AFLNet build applies a generic fix for its unterminated `-N` endpoint copy and requires 64 repeated valid endpoint parses. The target is not compiler-instrumented; AFLNet's helper bitmap is not PowerDNS source coverage.

Each testcase restarts the isolated Recursor process while keeping the zone file immutable. This preserves the process-reset boundary and should be reported with the resulting execution throughput.

Upstream: [5.4 changelog](https://doc.powerdns.com/recursor/changelog/5.4.html), [supported release trains](https://doc.powerdns.com/recursor/appendices/EOL.html), [official package repository](https://repo.powerdns.com/), [YAML auth-zone settings](https://doc.powerdns.com/recursor/yamlsettings.html), [RFC 7766](https://www.rfc-editor.org/rfc/rfc7766).
