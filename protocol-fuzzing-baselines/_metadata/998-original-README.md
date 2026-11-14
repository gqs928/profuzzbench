# 12 个协议实现最新稳定版本基准交付

核验日期：2026-11-03。交付覆盖工作簿中推荐顺序的全部 12 个已完成项。每个编号 ZIP 是独立的协议基准单元，含对应实现版本、适配代码、构建与运行脚本、验收报告及可复核证据。共同的基准化经验汇总在外层交付包根目录的 `基准化经验库.md`，不会重复塞进各协议 ZIP。

| 顺序 | 协议/实现 | 本次核验版本 | 独立交付包 |
|---:|---|---:|---|
| 191 | FTP / uftpd | 2.17 | `01-uftpd-2.17.zip` |
| 192 | SIP / Asterisk | 23.5.0 | `02-Asterisk-SIP-23.5.0.zip` |
| 193 | NFS / NFS-Ganesha | V9.14 | `03-NFS-Ganesha-V9.14.zip` |
| 194 | IMAP / Cyrus IMAP | 3.12.4 | `04-Cyrus-IMAP-3.12.4.zip` |
| 195 | IMAP / Dovecot | 2.4.5 | `05-Dovecot-2.4.5.zip` |
| 196 | IRC / InspIRCd | 4.12.0 | `06-InspIRCd-4.12.0.zip` |
| 197 | PostgreSQL / PostgreSQL | 18.6 | `07-PostgreSQL-18.6.zip` |
| 198 | Redis/RESP / Redis | 8.10.3 | `08-Redis-8.10.3.zip` |
| 199 | Memcached / Memcached | 1.6.45 | `09-Memcached-1.6.45.zip` |
| 200 | RADIUS / FreeRADIUS | 3.2.10 | `10-FreeRADIUS-3.2.10.zip` |
| 201 | Kafka protocol / Apache Kafka | 4.4.0 | `11-Kafka-4.4.0.zip` |
| 202 | MQTT / Mosquitto | 2.1.2 | `12-Mosquitto-2.1.2.zip` |

更新后的工作簿在 `协议模糊测试基准覆盖矩阵_基准化推荐顺序.xlsx`；表内保留全部其他行，仅在 12 个已完成项更新复核说明与末两列完成状态/基准版本。`协议版本核验清单.md` 汇总上游版本依据与本次处理，`基准化经验库.md` 集中保存可用于自动化框架的协议经验。`SHA256SUMS.txt` 可用于核对最终文件。
