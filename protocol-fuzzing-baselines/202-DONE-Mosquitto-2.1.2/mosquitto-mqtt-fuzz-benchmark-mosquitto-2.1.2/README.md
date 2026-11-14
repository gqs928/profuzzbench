# Mosquitto MQTT 有状态模糊测试基准

本基准用于评测 Eclipse Mosquitto 的 MQTT/TCP broker 路径。AFLNet 会变异 MQTT 控制报文序列，并使用服务端响应报文类型作为状态反馈。目标基于 Eclipse 官方最新稳定源码归档 Mosquitto 2.1.2，分别构建普通 broker、AFL/ASan 插桩 broker 和 gcov 覆盖率 broker。官方发布源码归档包含在本包内并通过 SHA-256 校验，因此构建镜像时无需联网下载 Mosquitto 或 AFLNet。

协议适配器使用 MQTT 固定报头和 Remaining Length 字段拆分请求报文。截断报文或包含五字节长度编码的错误报文会作为一个尾部区域整体保留。冒烟测试语料覆盖 MQTT 3.1.1 和 MQTT 5.0 的 CONNECT、SUBSCRIBE、PUBLISH、UNSUBSCRIBE、PINGREQ 和 DISCONNECT 流程。MQTT 帧格式和 Remaining Length 依据 OASIS MQTT 3.1.1 控制报文格式；Mosquitto 支持 MQTT 3.1、3.1.1 和 5.0。

## 在 Kali 的 Codex 工作区运行

将 `mosquitto-mqtt-fuzz-benchmark-mosquitto-2.1.2.zip` 复制到 Kali，在 Codex 已打开的工作区中解压，然后在该目录的集成终端执行：

~~~
unzip mosquitto-mqtt-fuzz-benchmark-mosquitto-2.1.2.zip
cd mosquitto-mqtt-fuzz-benchmark-mosquitto-2.1.2
chmod +x ./*.sh
./acceptance.sh mosquitto-fuzz-v212 "$PWD/results/mqtt-validation" 60s
~~~

构建镜像时会编译并运行 MQTT 解析器测试。独立脚本 `parser-check.sh` 是可选步骤，在 Kali 上运行它需要 C 编译器。

固定版本的 AFLNet 源码归档中，补丁目标文件使用 CRLF 换行。Docker 构建会先将这五个文件统一转换为 LF，再应用 `aflnet-mqtt.patch`，以确保不同环境下的补丁上下文检查结果一致。

`mosquitto.conf` 不设置 `daemon`：Mosquitto 默认在前台运行，并且会拒绝配置文件中的该选项。2.1.2 默认 `max_packet_size` 为 2,000,000 字节；原基准配置保留 `message_size_limit 1048576`，用于限制 PUBLISH payload。前者限制完整 MQTT 报文，后者限制发布 payload，不能为了消除提示而直接互换。覆盖率复放器把单条输入上限设为 2,000,000 字节，超出的队列样本会被明确标为跳过。Mosquitto 2.1.2 仍接受原有 `per_listener_settings false` 配置，但会在日志中提示该选项已弃用；本次保持单监听器行为与旧基准一致。

AFL/ASan 版本通过 make 命令行参数传入 `CC=.../afl-clang-fast`。Mosquitto 的 `WITH_ASAN=yes` 会把仅通过环境变量设置的 `CC` 覆盖为普通 `clang`。构建会检查 `__afl_area_ptr` 符号，确认目标确实经过 AFL 插桩。

`acceptance.sh` 会构建固定版本镜像并运行预检，将 Docker 输出、构建标识、镜像 ID 和输入哈希保存在 `build-logs/`。AFLNet、Mosquitto 及其源码归档均为本地输入。镜像使用带日期的 Ubuntu 软件包快照、最多五次 APT 重试，并启用 BuildKit 软件包缓存。构建使用 Docker 默认网络，不需要 BuildKit 的 host-network entitlement。如果软件源镜像暂时出错，重试同一命令即可复用已缓存的下载内容。

`validate.sh` 会在容器中启动普通 broker 和插桩 broker，并禁用容器网络。它保存每种协议版本和构建各十次的独立运行记录、完整 MQTT 报文、broker 日志、AFLNet 统计、状态图、构建标识和 SHA-256 清单。验收要求 MQTT 状态图至少包含两个状态和一条转换。

验收通过后，可运行较长时间的 fuzz：

~~~
mkdir -p results
docker run --rm --network none \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/results:/results" \
    mosquitto-fuzz-v212 bash /workspace/run.sh /results/mqtt-30m 30m
~~~

broker 只在隔离容器内监听 `127.0.0.1`。不要通过 Docker `-p` 发布 1883 端口；fuzzer 和 broker 通过容器内的 loopback 通信。

fuzz 结束后，将队列回放到独立的 gcov broker，以收集行覆盖率和分支覆盖率：

~~~
docker run --rm --network none \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/results:/results" \
  mosquitto-fuzz-v212 bash /workspace/coverage-run.sh \
    /results/mqtt-30m /results/mqtt-coverage 0
~~~

该命令会回放队列中的每个输入，并在 AFLNet 队列和统计文件旁生成 gcovr HTML 与文本摘要。固定版本的 Ubuntu 软件包提供 gcovr 4.2，该版本使用 `--print-summary` 参数。覆盖率数据分别从 Mosquitto 的 `libcommon/`、`lib/` 和 `src/` 构建目录收集，再合并为报告；未编入 broker 目标的 C++ wrapper 目录会排除。

## 测试范围与证据

- MQTT 3.1.1 和 MQTT 5.0，明文 TCP/1883。
- 使用 AFLNet 状态反馈、AFL 插桩、ASan 和独立 gcov 构建，测试 Mosquitto broker 请求处理路径。
- 种子包含有效的分版本会话、错误的 PING 标志和截断的 Remaining Length 字段。
- 本基准不覆盖 TLS、WebSockets、bridge、插件、身份验证或吞吐量测试。
- 短时 `validate.sh` 通过表示构建、正常协议交互、干净进程回放和状态反馈路径均已验收；它本身不代表发现了安全问题，也不代表已完成长时间 fuzz。

最终构建、短时验收、长时 fuzz、异常复核及覆盖率结果见 `evidence/RESULTS.md`；逐次日志、队列和报告保存在 `results/`。

## 固定输入

- Mosquitto 2.1.2 官方源码发布包，SHA-256 `fd905380691ac65ea5a93779e8214941829e3d6e038d5edff9eac5fd74cbed02`。
- ProFuzzBench AFLNet，commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`。
- Ubuntu 20.04 基础镜像按 digest 固定，并使用 Ubuntu Snapshot Service 时间戳 `20260928T000000Z`。
- 构建前和镜像内部都会校验 `source-checksums.sha256`。

上游仓库将 Mosquitto 描述为支持 MQTT 5.0、3.1.1 和 3.1 的 broker：[Eclipse Mosquitto](https://github.com/eclipse-mosquitto/mosquitto)。协议适配器实现 OASIS MQTT 规范中的 1 至 4 字节 Remaining Length 编码：[MQTT 3.1.1 规范](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/cs01/mqtt-v3.1.1-cs01.html)。`max_packet_size` 与 `message_size_limit` 的边界说明见 [Mosquitto 配置文档](https://mosquitto.org/man/mosquitto-conf-5.html)。

镜像构建期间，`prepare_seeds.py` 会以可复现方式生成种子输入。语料包括 MQTT 3.1.1 和 MQTT 5.0 会话，以及错误帧格式用例。生成的二进制文件位于容器内的 `/home/ubuntu/experiments/in-mqtt`。
