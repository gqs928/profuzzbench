# Asterisk PJSIP/TCP 有状态模糊测试基准

本目录把 Asterisk SIP 服务端适配成固定目标、可重建、可重复回放的 AFLNet 基准。目标为 Asterisk 上游 22 分支的固定提交，输入是 PJSIP/TCP 报文流，服务只绑定容器内 `127.0.0.1:5060`。Docker 构建会生成参考版、AFL/ASan 插桩版和独立 gcov 覆盖率版；Asterisk 的 SIP 解析、注册、事务、会话、SDP 和拨号计划源码均保持上游原样。

## 目标范围

- **协议路径：** PJSIP/SIP over TCP。旧 `chan_sip` 未加载。
- **正常业务流程：** OPTIONS 能力查询、REGISTER 注册、带 SDP 的 INVITE 进入固定拨号计划，再由同一事务的 CANCEL 终止。独立重复回放使用完全相同的请求字节。
- **模糊器反馈：** AFLNet 以 SIP 响应首行的状态码形成状态图。适配解析器按 `Content-Length` 切分 TCP 流，使 SDP 正文中的伪方法行不会误切消息；缺失、超长或截断长度会作为尾部样本保留。每轮复位后等待 1 秒再发请求；运行时先回放 REGISTER→INVITE→CANCEL 状态种子，只把 `.bin` 文件放入 AFLNet 输入目录，清单 JSON 不作为网络输入。
- **隔离：** Docker 使用 `--network none`；信令只监听回环地址。此基准中的端点免认证，仅供本地测试，不能用于生产环境，也不要使用 `-p` 发布 SIP 端口。
- **未覆盖：** SIP/UDP、TLS、WebSocket、IAX、媒体/RTP 负载、外部身份认证、PSTN/DAHDI、真实电话终端和生产部署配置。

构建只运行 Asterisk 的 `bininstall` 安装目标，跳过会从独立站点下载的语音提示包；本基准的拨号流程不播放媒体，避免构建引入未锁定的外部文件。

为兼容 AFL/ASan 构建，`asterisk-afl-build.patch` 只调整 XML/XSLT 纯数据对象的生成器：这些对象不经过插桩，改由系统 Clang 生成，以免 AFL 编译器包装器把 ASan 运行时重复嵌入数据对象。补丁不改 Asterisk 的 SIP 协议处理代码；补丁散列会写入镜像版本清单。

## 构建和严格验收

需要可用的 Linux Docker 环境和能够访问固定 Ubuntu 软件源快照的网络。Asterisk、AFLNet 和 PJPROJECT 的源码归档均随包提供，并在构建中核对 SHA-256；Docker 软件包来自 Dockerfile 固定的软件源快照。

完整执行图片要求中的构建、10 轮对照回放、30 分钟模糊测试、队列覆盖率、异常样本复放和故障探针：

```sh
chmod +x ./*.sh
./acceptance.sh asterisk-sip-fuzz "$PWD/results/strict-acceptance"
```

严格验收会保存无缓存构建日志、镜像 ID、依赖包版本、每条种子的 SHA-256、参考版/AFL 版的 20 轮会话记录、AFLNet `fuzzer_stats` / `plot_data` / `ipsm.dot`、variable_paths 排查结果、30 分钟运行中被标记的每条变动路径样本各 10 次独立复播、队列与异常样本回放、gcovr 行/分支覆盖率、gcov 核心函数清单、临时故障注入的独立复现记录和最终 SHA-256 清单。通过后会生成包含基准源码和本次验收证据的 ZIP 交付包，历史诊断目录不会打入包内。

只做短时验收时：

```sh
./build.sh asterisk-sip-fuzz
./validate.sh asterisk-sip-fuzz "$PWD/results/preflight" 180s
```

单独运行 fuzz 时，输出目录必须是新的空目录：

```sh
docker run --rm --network none \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/results:/results" \
  asterisk-sip-fuzz bash /workspace/run.sh /results/sip-30m/aflnet 30m
```

再把队列和异常样本逐条送入全新 gcov Asterisk 进程：

```sh
docker run --rm --network none \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/results:/results" \
  asterisk-sip-fuzz bash /workspace/coverage-run.sh \
    /results/sip-30m/aflnet /results/sip-coverage 200
```

## 复现细节

- **固定源码：** Asterisk 稳定版 `23.5.0`，提交 `1da6eb34b3b23507e616863cf1e2c13c4f482fd7`；PJPROJECT `2.17`；AFLNet `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`。
- **固定种子：** OPTIONS、REGISTER/注销、REGISTER 后 OPTIONS、INVITE/CANCEL、REGISTER/INVITE/CANCEL、SDP、ACK、BYE、MESSAGE 和截断 Content-Length。生成器可重复运行，清单记录字节数、方法、请求数及 SHA-256。
- **进程复位：** AFLNet 使用 `-K`，每个输入都结束 Asterisk 子进程；`-c` 清理回调在目标子进程 fork 前运行，清空可写运行目录并重建配置，避免清理和 Asterisk 启动并发。协议验收逐轮确认服务进程退出且 TCP/5060 端口释放。
- **覆盖率：** 单独的 gcov 构建回放 AFLNet 保存的消息序列。报告筛选 Asterisk PJSIP 与 `chan_pjsip` 源文件，并列出实际覆盖行、分支和命中的函数。
- **异常观测：** 验收期间在 `/tmp` 临时编译独立 SIP 故障探针，用于验证 AFLNet 能保存并复现异常退出。探针不修改 Asterisk 源码，完成后删除。

协议状态说明见 [sip-state-mapping.md](sip-state-mapping.md)。固定输入及其散列见 [source-lock.json](source-lock.json) 和 [source-checksums.sha256](source-checksums.sha256)。
