# Protocol fuzzing benchmark directories

The package contents below are expanded into ordinary folders so they can be browsed file by file on GitHub. Folder prefixes follow the order on sheet 4, “基准化推荐顺序”, of the supplied coverage matrix.

This publication contains recommendation ranks 1–79 except rank 5 (Kamailio was absent from the source archive), plus completed ranks 191–202. Ranks 80–190 were absent from the source archive.

The package ZIP files themselves are not copied into this directory tree. Each folder keeps the internal path layout and executable bits from its source package. Embedded .git metadata directories are omitted; they contain version-control internals rather than benchmark working files.

The 118.6 MB EMQX build tarball exceeds GitHub’s 100 MiB regular-file limit, so it is stored as two adjacent part files with a SHA-256 reconstruction note in the EMQX directory.

The source workbook, package checksums, original notes, and the expanded extraction manifest are in [the _metadata folder](./_metadata/).

| Order | Browse directory |
|---:|---|
| 1 | [001-P1-BIND9-DNS-9.20.30/](./001-P1-BIND9-DNS-9.20.30/) |
| 2 | [002-P1-OpenSIPS-SIP-4.0.3/](./002-P1-OpenSIPS-SIP-4.0.3/) |
| 3 | [003-P1-Kea-DHCPv4-3.2.1/](./003-P1-Kea-DHCPv4-3.2.1/) |
| 4 | [004-P2-open62541-OPC-UA-1.5.10/](./004-P2-open62541-OPC-UA-1.5.10/) |
| 6 | [006-P2-vsftpd-FTP-3.0.5/](./006-P2-vsftpd-FTP-3.0.5/) |
| 7 | [007-P2-EMQX-MQTT-6.3.2/](./007-P2-EMQX-MQTT-6.3.2/) |
| 8 | [008-P2-NanoMQ-MQTT-0.25.6/](./008-P2-NanoMQ-MQTT-0.25.6/) |
| 9 | [009-P2-VerneMQ-MQTT-2.2.1/](./009-P2-VerneMQ-MQTT-2.2.1/) |
| 10 | [010-P2-GStreamer-RTSP-1.28.8/](./010-P2-GStreamer-RTSP-1.28.8/) |
| 11 | [011-P2-MediaMTX-RTSP-1.21.3/](./011-P2-MediaMTX-RTSP-1.21.3/) |
| 12 | [012-P2-ZLMediaKit-RTSP-fb326572/](./012-P2-ZLMediaKit-RTSP-fb326572/) |
| 13 | [013-P2-Haraka-SMTP-3.4.0/](./013-P2-Haraka-SMTP-3.4.0/) |
| 14 | [014-P2-OpenSMTPD-SMTP-7.9.0p0/](./014-P2-OpenSMTPD-SMTP-7.9.0p0/) |
| 15 | [015-P2-TigerVNC-RFB-1.16.2/](./015-P2-TigerVNC-RFB-1.16.2/) |
| 16 | [016-P2-xrdp-RDP-0.10.6.1/](./016-P2-xrdp-RDP-0.10.6.1/) |
| 17 | [017-P2-tgt-iSCSI-1.0.98/](./017-P2-tgt-iSCSI-1.0.98/) |
| 18 | [018-P2-Courier-POP3-6.0.7/](./018-P2-Courier-POP3-6.0.7/) |
| 19 | [019-P2-Cyrus-POP3-3.12.4/](./019-P2-Cyrus-POP3-3.12.4/) |
| 20 | [020-P2-Dovecot-POP3-2.4.5/](./020-P2-Dovecot-POP3-2.4.5/) |
| 21 | [021-P2-Courier-IMAP-6.0.7/](./021-P2-Courier-IMAP-6.0.7/) |
| 22 | [022-P2-INN-NNTP-2.7.4/](./022-P2-INN-NNTP-2.7.4/) |
| 23 | [023-P2-Leafnode-NNTP-1.12.0/](./023-P2-Leafnode-NNTP-1.12.0/) |
| 24 | [024-P2-Ergo-IRC-2.19.1/](./024-P2-Ergo-IRC-2.19.1/) |
| 25 | [025-P2-UnrealIRCd-IRC-6.2.7.1/](./025-P2-UnrealIRCd-IRC-6.2.7.1/) |
| 26 | [026-P2-ejabberd-XMPP-26.09/](./026-P2-ejabberd-XMPP-26.09/) |
| 27 | [027-P2-Openfire-XMPP-5.1.2/](./027-P2-Openfire-XMPP-5.1.2/) |
| 28 | [028-P2-Prosody-XMPP-13.0.7/](./028-P2-Prosody-XMPP-13.0.7/) |
| 29 | [029-P2-Apache-Artemis-AMQP-2.57.0/](./029-P2-Apache-Artemis-AMQP-2.57.0/) |
| 30 | [030-P2-Apache-Qpid-Broker-J-AMQP-10.1.1/](./030-P2-Apache-Qpid-Broker-J-AMQP-10.1.1/) |
| 31 | [031-P2-RabbitMQ-AMQP-4.4.0/](./031-P2-RabbitMQ-AMQP-4.4.0/) |
| 32 | [032-P2-Apache-ActiveMQ-Classic-STOMP-6.4.0/](./032-P2-Apache-ActiveMQ-Classic-STOMP-6.4.0/) |
| 33 | [033-P2-Apache-Artemis-STOMP-2.57.0/](./033-P2-Apache-Artemis-STOMP-2.57.0/) |
| 34 | [034-P2-RabbitMQ-STOMP-4.4.0/](./034-P2-RabbitMQ-STOMP-4.4.0/) |
| 35 | [035-P2-389DS-LDAP-3.3.1/](./035-P2-389DS-LDAP-3.3.1/) |
| 36 | [036-P2-ApacheDS-LDAP-2.0.0.AM27/](./036-P2-ApacheDS-LDAP-2.0.0.AM27/) |
| 37 | [037-P2-OpenLDAP-LDAP-2.7.2/](./037-P2-OpenLDAP-LDAP-2.7.2/) |
| 38 | [038-P2-Netopeer2-NETCONF-2.8.21/](./038-P2-Netopeer2-NETCONF-2.8.21/) |
| 39 | [039-P2-CockroachDB-PostgreSQL-v26.2.11/](./039-P2-CockroachDB-PostgreSQL-v26.2.11/) |
| 40 | [040-P2-QuestDB-PostgreSQL-10.1.0/](./040-P2-QuestDB-PostgreSQL-10.1.0/) |
| 41 | [041-P2-MariaDB-MySQL-13.0.2/](./041-P2-MariaDB-MySQL-13.0.2/) |
| 42 | [042-P2-MySQL-MySQL-26.7.1/](./042-P2-MySQL-MySQL-26.7.1/) |
| 43 | [043-P2-TiDB-MySQL-v8.5.8/](./043-P2-TiDB-MySQL-v8.5.8/) |
| 44 | [044-P2-Vitess-MySQL-v24.0.5/](./044-P2-Vitess-MySQL-v24.0.5/) |
| 45 | [045-P2-MediaMTX-RTMP-v1.21.3/](./045-P2-MediaMTX-RTMP-v1.21.3/) |
| 46 | [046-P2-NGINX-RTMP-1.30.6-module-1.2.2/](./046-P2-NGINX-RTMP-1.30.6-module-1.2.2/) |
| 47 | [047-P2-SRS-RTMP-v6.0-r3/](./047-P2-SRS-RTMP-v6.0-r3/) |
| 48 | [048-P2-ZLMediaKit-RTMP-fb326572/](./048-P2-ZLMediaKit-RTMP-fb326572/) |
| 49 | [049-P2-Redpanda-Kafka-v26.2.6/](./049-P2-Redpanda-Kafka-v26.2.6/) |
| 50 | [050-P2-FerretDB-MongoDB-Wire-v2.7.0/](./050-P2-FerretDB-MongoDB-Wire-v2.7.0/) |
| 51 | [051-P2-MongoDB-Server-Wire-9.0.8/](./051-P2-MongoDB-Server-Wire-9.0.8/) |
| 52 | [052-P2-Apache-Cassandra-Native-5.0.9/](./052-P2-Apache-Cassandra-Native-5.0.9/) |
| 53 | [053-P2-ScyllaDB-Native-2026.3.5/](./053-P2-ScyllaDB-Native-2026.3.5/) |
| 54 | [054-P2-YugabyteDB-Cassandra-Native-2026.1.3.0/](./054-P2-YugabyteDB-Cassandra-Native-2026.1.3.0/) |
| 55 | [055-P2-Apache-ZooKeeper-Jute-3.9.7/](./055-P2-Apache-ZooKeeper-Jute-3.9.7/) |
| 56 | [056-P2-NATS-Core-2.15.3/](./056-P2-NATS-Core-2.15.3/) |
| 57 | [057-P3-FRRouting-BGP-10.7.1/](./057-P3-FRRouting-BGP-10.7.1/) |
| 58 | [058-P3-dcm4che-DICOM-5.35.2/](./058-P3-dcm4che-DICOM-5.35.2/) |
| 59 | [059-P3-pynetdicom-DICOM-3.0.4/](./059-P3-pynetdicom-DICOM-3.0.4/) |
| 60 | [060-P3-Knot-DNS-3.6.2/](./060-P3-Knot-DNS-3.6.2/) |
| 61 | [061-P3-PowerDNS-Recursor-DNS-5.4.9/](./061-P3-PowerDNS-Recursor-DNS-5.4.9/) |
| 62 | [062-P3-Unbound-DNS-1.26.2/](./062-P3-Unbound-DNS-1.26.2/) |
| 63 | [063-P3-GnuTLS-DTLS-3.8.13/](./063-P3-GnuTLS-DTLS-3.8.13/) |
| 64 | [064-P3-OpenSSL-DTLS-4.1.0/](./064-P3-OpenSSL-DTLS-4.1.0/) |
| 65 | [065-P3-wolfSSL-DTLS-5.9.4/](./065-P3-wolfSSL-DTLS-5.9.4/) |
| 66 | [066-P3-Apache-HTTP2-2.4.71/](./066-P3-Apache-HTTP2-2.4.71/) |
| 67 | [067-P3-Cloudflare-quiche-QUIC-0.30.0/](./067-P3-Cloudflare-quiche-QUIC-0.30.0/) |
| 68 | [068-P3-Google-QUICHE-QUIC-main-23e525e/](./068-P3-Google-QUICHE-QUIC-main-23e525e/) |
| 69 | [069-P3-LSQUIC-QUIC-4.11.1/](./069-P3-LSQUIC-QUIC-4.11.1/) |
| 70 | [070-P3-MsQuic-QUIC-v2.6.4/](./070-P3-MsQuic-QUIC-v2.6.4/) |
| 71 | [071-P3-ngtcp2-QUIC-1.26.0/](./071-P3-ngtcp2-QUIC-1.26.0/) |
| 72 | [072-P3-OpenSSL-QUIC-4.1.0/](./072-P3-OpenSSL-QUIC-4.1.0/) |
| 73 | [073-P3-Picoquic-QUIC-v2026.11.12.36f49b7/](./073-P3-Picoquic-QUIC-v2026.11.12.36f49b7/) |
| 74 | [074-P3-quic-go-QUIC-v0.65.0/](./074-P3-quic-go-QUIC-v0.65.0/) |
| 75 | [075-P3-PJSIP-SIP-2.17/](./075-P3-PJSIP-SIP-2.17/) |
| 76 | [076-P3-Impacket-SMB-0.13.1/](./076-P3-Impacket-SMB-0.13.1/) |
| 77 | [077-P3-Postfix-SMTP-3.11.7/](./077-P3-Postfix-SMTP-3.11.7/) |
| 78 | [078-P3-libssh-SSH-0.12.2/](./078-P3-libssh-SSH-0.12.2/) |
| 79 | [079-P3-BoringSSL-TLS-0.20261105.0/](./079-P3-BoringSSL-TLS-0.20261105.0/) |
| 191 | [191-DONE-uftpd-2.17/](./191-DONE-uftpd-2.17/) |
| 192 | [192-DONE-Asterisk-SIP-23.5.0/](./192-DONE-Asterisk-SIP-23.5.0/) |
| 193 | [193-DONE-NFS-Ganesha-V9.14/](./193-DONE-NFS-Ganesha-V9.14/) |
| 194 | [194-DONE-Cyrus-IMAP-3.12.4/](./194-DONE-Cyrus-IMAP-3.12.4/) |
| 195 | [195-DONE-Dovecot-2.4.5/](./195-DONE-Dovecot-2.4.5/) |
| 196 | [196-DONE-InspIRCd-4.12.0/](./196-DONE-InspIRCd-4.12.0/) |
| 197 | [197-DONE-PostgreSQL-18.6/](./197-DONE-PostgreSQL-18.6/) |
| 198 | [198-DONE-Redis-8.10.3/](./198-DONE-Redis-8.10.3/) |
| 199 | [199-DONE-Memcached-1.6.45/](./199-DONE-Memcached-1.6.45/) |
| 200 | [200-DONE-FreeRADIUS-3.2.10/](./200-DONE-FreeRADIUS-3.2.10/) |
| 201 | [201-DONE-Kafka-4.4.0/](./201-DONE-Kafka-4.4.0/) |
| 202 | [202-DONE-Mosquitto-2.1.2/](./202-DONE-Mosquitto-2.1.2/) |
