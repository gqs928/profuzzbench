# Pinned upstream protocol implementations

The target images pin the latest stable upstream releases available on 2026-10-27.
LightFTP and TinyDTLS use their latest upstream mainline snapshots because no newer
stable release is published for either target. Git-based sources are pinned to full
commit hashes in their Dockerfiles; release archives are verified by SHA-256. The
Pth and libfaketime helper dependencies retain their existing pins. The patches in
each subject directory adapt ProFuzzBench's deterministic input handling,
instrumentation, or server lifecycle to that source revision.

| Protocol target | Upstream version | Pinned revision | Source |
|---|---:|---|---|
| forked-daapd | 29.3 | `d6fb3edf5831de38134ebd92fcf09a730ddd37aa` | [GitHub](https://github.com/ejurgensen/forked-daapd) |
| DCMTK | 3.7.1 | `108acdae424d6999b2e398243938d8c563315ecf` | [GitHub](https://github.com/DCMTK/dcmtk) |
| dnsmasq | 2.93 | SHA-256 `cc967771abdafeb43d10db18932d6b59fd4bed2c69c22acf8cb96aff6920d55f` | [Official release archive](https://thekelleys.org.uk/dnsmasq/dnsmasq-2.93.tar.gz) |
| TinyDTLS | Eclipse upstream snapshot (2026-10-19) | `5b05dd673b036ce7e10df8feaa1a827d578f907a` | [GitHub](https://github.com/eclipse-tinydtls/tinydtls) |
| BFTPD | 6.7 | SHA-256 `40317957c3667fded7541ff4b0f44328573827ef0315519a44ca1b627f5eafb2` | [SourceForge release archive](https://sourceforge.net/projects/bftpd/files/bftpd/bftpd-6.7/bftpd-6.7.tar.gz/download) |
| LightFTP | upstream master snapshot (2026-10-19; after 2.3.1) | `a7af93ab0bbf9df6aba3e987c0d4180a5bef5253` | [GitHub](https://github.com/hfiref0x/LightFTP) |
| ProFTPD | 1.3.9e | `fc3f908a0d07fa3b17fbe1e3054b7520806bc75a` | [GitHub](https://github.com/proftpd/proftpd) |
| Pure-FTPd | 1.0.54 | `3fe02789c4f0e5756f3f612e32edee9aa5d49455` | [GitHub](https://github.com/jedisct1/pure-ftpd) |
| Live555 | 2026-10-24 | SHA-256 `5d6244604b364251d0c0b0fc87a849488958802245b1473eaaf55eaaef5a838b` | [Official release archive](https://download.live555.com/live.2026.10.24.tar.gz) |
| Kamailio | 6.1.5 | `aab4e3d6d157bdf09bd7a6512cfec70a4f2b5477` | [GitHub](https://github.com/kamailio/kamailio) |
| Exim | 4.100.1 | `fb7ccaa78db25a5816a3c4413d2e6caa44aaf822` | [Official Git](https://code.exim.org/exim/exim) |
| OpenSSH | 10.6p1 | `a8c72b842423f0774f542d3c2197247c3dd28d74` | [GitHub portable](https://github.com/openssh/openssh-portable) |
| OpenSSL | 4.1.0 | `2f4e3a5fec05394068cfa7379890ab552483a8a6` | [GitHub](https://github.com/openssl/openssl) |
| PJSIP helper (Kamailio image) | 2.17 | `5a457451fa2712ba18e12b01738e8ff3af2b26fd` | [GitHub](https://github.com/pjsip/pjproject) |

## Adaptation notes

- DCMTK now uses its `OFString` configuration path API; AFL/StateAFL compiler
  selection is passed to the build-directory CMake invocation.
- forked-daapd now installs its `libprotobuf-c` development and compiler packages,
  required by the current bundled librespot-c configure step; obsolete parser
  generation targets were removed because the current Automake build handles them.
- dnsmasq gets a deterministic SURF PRNG state, and all variants build from the
  checksum-verified official release archive.
- TinyDTLS now uses its upstream Autotools build and registers SIGUSR1 for coverage
  shutdown.
- BFTPD and Live555 downloads are checksum-verified. Live555's AFLNet, AFlnwe,
  and StateAFL builds use LLVM's trace-pc-guard instrumentation and remove a
  legacy LLVM command-line option no longer accepted by Ubuntu 22.04's LLVM 14.
  StateAFL's statically linked tracer uses non-PIE linking; the coverage image
  also applies the deterministic RTSP adaptation and shutdown hook.
- LightFTP now builds from `src/Release`; the updated runtime reads its port from
  `fftp.conf`, so the target config pins it to 2200. Its TLS config points to the
  `my.key` file included in ProFuzzBench's certificate bundle.
- Exim's random-seed and message-ID patches were reduced to current source sites;
  the default test config is patched before install, and PCRE2 development files
  are installed for the current configure script; Local/Makefile explicitly
  selects the OpenSSL TLS backend.
- OpenSSH now links against the OpenSSL 4.1.0 `lib64` installation path, matching
  the headers and runtime libraries used by its pinned dependency.
- OpenSSL 4.1.0 builds all generated headers before compiling its app target;
  the public headers are generated from `.h.in` templates in this release. The
  deterministic random helper is copied into the upstream `fuzz/` tree before
  applying the ProFuzzBench adaptation in both the AFL and StateAFL images.
