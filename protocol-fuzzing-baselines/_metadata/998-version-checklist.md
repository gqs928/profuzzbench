# 协议实现最新稳定版本核验清单

核验基准日期：2026-11-03。稳定版本依据为各项目上游发布页或发行归档。版本一致的项目复用其完整证据；升级项目按锁定版本重新构建或验收。Kafka 特别核对被测 Broker 的实际版本与锁文件一致。

| 推荐顺序 | 协议/实现 | 原已完成基准版本 | 本次版本 | 上游依据 | 处理摘要 |
|---:|---|---|---|---|---|
| 191 | FTP / uftpd | 2.17 | 2.17 | https://github.com/troglobit/uftpd/releases | 版本一致；复核完整 30 分钟记录 |
| 192 | SIP / Asterisk | 22 系列 | 23.5.0 | https://www.asterisk.org/downloads/asterisk/all-asterisk-versions/ | 更新锁定源码及依赖，完整重建与验收 |
| 193 | NFS / NFS-Ganesha | V6.5 | V9.14 | https://github.com/nfs-ganesha/nfs-ganesha/releases | 更新 Ganesha/ntirpc 锁定版本，完整重建与验收 |
| 194 | IMAP / Cyrus IMAP | 3.12.4 | 3.12.4 | https://github.com/cyrusimap/cyrus-imapd/releases | 版本一致；复核完整 30 分钟验收 |
| 195 | IMAP / Dovecot | main 快照 | 2.4.5 | https://github.com/dovecot/core/releases | 切换至稳定发行版并重建、验收 |
| 196 | IRC / InspIRCd | 4.10.1 | 4.12.0 | https://github.com/inspircd/inspircd/releases | 新版本构建、30 分钟运行及全队列回放 |
| 197 | PostgreSQL / PostgreSQL | 18.6 | 18.6 | https://www.postgresql.org/docs/release/ | 版本一致；补齐正式全时长验收与独立交付脚本 |
| 198 | Redis/RESP / Redis | 8.10.1 | 8.10.3 | https://download.redis.io/releases/ | 锁定新归档并重新构建、运行和三轮回放 |
| 199 | Memcached / Memcached | 1.6.45 | 1.6.45 | https://memcached.org/downloads | 版本一致；复核完整验收证据 |
| 200 | RADIUS / FreeRADIUS | 3.2.10 | 3.2.10 | https://github.com/FreeRADIUS/freeradius-server/releases | 版本一致；复核完整验收证据 |
| 201 | Kafka protocol / Apache Kafka | 4.2.2 | 4.4.0 | https://kafka.apache.org/downloads/ | 旧镜像的 4.2.2 证据作废；锁定官方 4.4.0 发行归档并重新验收 |
| 202 | MQTT / Mosquitto | 2.1.2 | 2.1.2 | https://mosquitto.org/download/ | 版本一致；复核 2.1.2 完整验收 |

详细运行结论、适配变更和证据位置分别见 12 个独立 ZIP 的 `RESULTS.md`、验收报告或对应目录。全体版本与工作簿最后两列对应；Kafka 上游页把 4.4.0 列为 Supported release：[Apache Kafka 下载页](https://kafka.apache.org/downloads/)。
