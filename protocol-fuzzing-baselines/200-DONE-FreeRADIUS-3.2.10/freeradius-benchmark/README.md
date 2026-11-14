# FreeRADIUS RADIUS/TCP 状态模糊测试基准

本目录把 FreeRADIUS 做成可固定版本、可重建、可复位、可回放的 AFLNet 目标。目标版本为 FreeRADIUS `release_3_2_10`（提交短号 `9071ea0`），AFLNet 固定到 `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`。源码包、基础镜像、Ubuntu 软件源快照、依赖包版本和本地补丁都记录并校验 SHA-256。

## 协议和改动范围

被测输入是 FreeRADIUS 原生 RADIUS/TCP 报文流，监听 `127.0.0.1:1812`。RADIUS 的 Code、Identifier、Length、Authenticator 和属性仍由 FreeRADIUS 原有代码处理。AFLNet 侧新增报文切分与响应状态解析器：按 16 位网络序 Length 切包，并把 Access-Accept、Access-Reject、Accounting-Response 等状态送入状态图。

基准同时保留 UDP/1812 认证和 UDP/1813 记账，使用原生 PAP 文件用户和 detail 记账模块。参考版和 AFL 插桩版会完成相同的 UDP 与持久 TCP 会话。测试配置只绑定容器回环地址，使用固定本地测试用户 `alice` 和共享密钥 `testing123`；不得将该配置暴露到容器外。

唯一的 FreeRADIUS 源码构建补丁把可选模块集合收窄到 `rlm_detail`、`rlm_files`、`rlm_pap`，以固定构建和运行时依赖。TCP/RADIUS 解析、认证、记账和请求处理源码不改。覆盖率构建使用相同补丁和配置。AFLNet 补丁仅注册 RADIUS 请求边界与响应状态解析器。

种子由 `prepare_seeds.py` 可重复生成，`seeds-manifest.json` 记录每个种子的长度、请求数和 SHA-256；`seeds/` 目录只放 AFLNet 实际读取的二进制种子。种子包含成功/失败 PAP、Accounting-Start、Accounting-Stop、认证与记账组合，以及拒绝后重试成功的多包会话。每个 AFL 测试用例都会重启服务进程并清除 detail 记账目录。

## 构建和复验

需要可用的 Linux Docker 环境。首次构建会联网获取固定 Ubuntu 快照的软件包；FreeRADIUS 和 AFLNet 源码归档已随包提供，并在构建前校验哈希。

```sh
chmod +x ./*.sh
./build.sh freeradius-radius-fuzz
./validate.sh freeradius-radius-fuzz "$PWD/results/preflight" 90s
```

`validate.sh` 使用参考版与插桩版各执行至少 10 个全新会话，比较完整响应 transcript，并检查 UDP/TCP 认证、拒绝、记账、AFLNet 队列和 RADIUS 状态图。

状态回放将响应轮询设为 1500 毫秒，以覆盖 FreeRADIUS 默认约 1 秒的认证拒绝延迟；目标端配置不关闭该延迟。
覆盖率独立回放每个样本最多等待 1.5 秒，让认证拒绝响应完成后再复位进程并导出覆盖率数据。

按图片建议执行完整验收（无缓存构建、10 次稳定回放、30 分钟模糊测试、队列/异常样本覆盖率回放和故障可观测性探针）：

```sh
./acceptance.sh freeradius-radius-fuzz "$PWD/results/strict-acceptance"
```

完整验收会产生 `ACCEPTANCE-REPORT.md`、`build-versions.txt`、`fuzzer_stats`、`plot_data` / CSV、`ipsm.dot`、AFL 队列与崩溃样本、逐样本独立回放记录、协议核心覆盖率 TXT/HTML/JSON/CSV 和 SHA256SUMS。AFLNet 的异常样本长度前缀会在回放前还原为 RADIUS 报文流。故障探针在 `/tmp` 临时编译一个会对标记属性主动异常退出的 RADIUS/TCP 小服务，用来确认 AFLNet 能记录异常并由保存样本独立复现；探针源码和二进制在验证后删除，不修改或保留对 FreeRADIUS 的故意异常补丁。

验收通过后，`package.sh` 会在当前目录的上一级生成带 SHA-256 的交付 ZIP，包含源码归档、构建脚本、语料和验收证据。

## 覆盖范围与限制

- 覆盖 RADIUS/TCP 的认证、拒绝、记账请求、连续报文切分、属性边界与畸形长度；状态定义见 [radius-state-mapping.md](radius-state-mapping.md)。
- 保留并对照 RADIUS/UDP 的常规 PAP 认证与记账流程。
- 不覆盖 TLS/RadSec、EAP、代理上游、动态授权、数据库/LDAP 后端、DHCP 或生产部署策略。
- 该包是协议处理基准，不是吞吐量基准；默认只在隔离容器内监听回环地址。

上游仓库：[FreeRADIUS/freeradius-server](https://github.com/FreeRADIUS/freeradius-server)。版本选择依据上游 3.2 支持分支和签名发布版；4.0 在该上游快照仍标注为未正式发布。
