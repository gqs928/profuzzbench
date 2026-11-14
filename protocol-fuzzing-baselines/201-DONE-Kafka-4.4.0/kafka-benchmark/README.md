# Apache Kafka 协议模糊测试基准

本基准把 Apache Kafka Broker 做成固定版本、可重建、可复位、可回放的 Kafka 原生二进制协议目标。默认目标为 Kafka `4.4.0`，上游提交 `1156b2752aaa28eafc0b4c4d387e63356793268d`；AFLNet 固定到 `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`。被测 Broker 使用 Apache 官方 4.4.0 二进制发行版并以 SHA-512 锁定；对应官方源码归档用于 JaCoCo 源码映射，不在本地重新 Gradle 编译 Kafka。构建使用 Ubuntu 24.04 软件包快照、OpenJDK 21、JaCoCo `0.8.13`，并记录依赖版本、源码版本、构建输入哈希和镜像 ID。

## 目标和插桩

- 服务端为真实 Kafka JVM Broker，使用单节点 KRaft、PLAINTEXT/TCP `127.0.0.1:9092`；控制器也只绑定容器回环地址。容器使用 `--network none`，不发布主机端口。
- AFLNet 解析器按 Kafka 四字节大端长度前缀切分请求帧。畸形、超长或截断尾部仍作为可变区域发送给 Broker。`ipsm.dot` 以请求种子约定的 correlation id 识别 ApiVersions、Metadata、Produce、Fetch、ListOffsets 和 FindCoordinator 阶段，具体映射见 [kafka-state-mapping.md](kafka-state-mapping.md)。
- AFLNet 的覆盖反馈来自加载在 Kafka JVM 内的 JVMTI 代理：仅记录 `kafka.server.KafkaApis` 的分派入口，以及 ApiVersions、TopicMetadata、Produce、Fetch 四类请求处理方法是否执行，不累计调用次数。这样把反馈限定在协议业务入口，排除 JVM 后台线程的调度波动。JaCoCo 不参与 30 分钟 fuzz 执行；队列回放时单独开启 JaCoCo（`org/apache/kafka/*,kafka/*`），生成更广泛的 Broker 请求解析/网络服务核心代码行和分支覆盖率。官方发行包模式以 `libs/` 下 Kafka runtime JAR 作为 JaCoCo classfiles，并以同版本官方源码归档的 Java/Scala 目录映射源码行号，不要求存在 Gradle `build/classes`。该方法覆盖机制适配了 JVM 目标，不能解释为 Kafka 本身经过 `afl-clang-fast` 原生编译。
- `clean.sh` 从构建时生成的 KRaft 初始快照恢复日志与主题状态。启动脚本在每个样本进程内先恢复快照，再启动 Broker 并等待端口就绪；这样复位发生在服务启动前。AFLNet 对每个输入使用新 Broker/JVM 进程，成本高于纯原生目标。
- Kafka 启动器是经 AFLNet 插桩的 ELF 包装器，通过 `exec` 启动 `start-kafka.sh`，满足 AFLNet 对 ELF 目标的检查，同时保留同一进程号、AFL 共享内存和 Kafka JVM 行为。
- AFLNet 以 500 毫秒有效 socket 超时读取持久 Kafka 连接，避免无效 `timeval` 让响应读取无限阻塞。每个样本结束时，AFLNet 向一次性 Broker 发送 SIGTERM 并等待进程退出；AFL 将该正常终止信号识别为成功样本。下一样本从 KRaft 快照恢复。Kafka JVM 仅进行三次快速覆盖校准，独立十轮业务回放负责验证正常协议行为。

## 构建和短验收

首次构建需要 Docker、可联网获取 Apache 官方 Kafka 4.4.0 二进制/源码发行归档与 JaCoCo Maven 工件。两个 Kafka 归档均以 Apache 发布页提供的 SHA-512 固定校验；二进制归档作为实际 Broker，源码归档仅用于 JaCoCo 行覆盖源码映射。源码 commit 仍记录在 `source-lock.json` 中。Ubuntu 24.04 的 amd64 OCI manifest 与配置摘要也已固定；默认先拉取并校验基础镜像。若该精确镜像已通过可信渠道导入本机 Docker，可设置 `BUILD_PULL=false` 复用本地副本，但构建前仍会校验镜像内容摘要。进入本目录运行：

```sh
chmod +x ./*.sh
./build.sh apache-kafka-fuzz-bench
./validate.sh apache-kafka-fuzz-bench "$PWD/results/preflight" 120s
```

构建流程不在本机重新编译 Kafka；它校验并展开官方 4.4.0 二进制发行版，构建 AFLNet 与轻量覆盖代理。只有虚拟机达到可用内存门槛后再通过 `--no-cache` 强制重建容器层。

严格验收仅接受 `KAFKA_BUILD_MODE=full`：该流程重新构建 fuzz harness 和代理，并以 Apache SHA-512 校验过的 4.4.0 官方二进制及源码归档为目标。历史 overlay 镜像是 Kafka 4.2.2，脚本会拒绝它，不能复用旧版本结果。

为保护资源较少的虚拟机，Kafka 官方发行包免去本机 Gradle 编译；AFLNet/代理构建使用单 worker，Broker JVM 最大堆为 384 MiB。验收容器默认硬限为 1 个 CPU、1 GiB 内存，并禁用容器 swap。4 vCPU 虚拟机中，单个验收容器最多使用约四分之一总 CPU 和 1 GiB 内存。可以用 `KAFKA_CPU_LIMIT=2` 提高运行速度，或用 `KAFKA_MEMORY_LIMIT=768m` 降低内存占用；两项配置会用于预检、30 分钟 fuzz、覆盖回放和故障探针。短预检只回放 `api-versions.bin` 和 `metadata-produce.bin` 两粒种子，样本硬超时 45 秒，并要求 AFL 校准覆盖稳定度至少 90%；正式 fuzz 使用完整语料和 120 秒样本硬超时。时长到达后最多等待 150 秒退出并写完统计。`run-parameters.txt` 与验收根目录的 `resource-limits.txt` 会记录配额。

构建前会读取 Linux `MemAvailable`；低于 1024 MiB 时会在 Docker 操作前退出。建议给虚拟机配置至少 4 GiB 内存，并确保构建开始前有 1 GiB 可用内存。

`validate.sh` 会通过无代理参考 Broker 和开启 JVMTI/JaCoCo 代理的 Broker，各执行至少 10 轮相同的 ApiVersions → Metadata → Produce → Fetch 客户端会话，并比较 correlation id 与 API 错误结果；每轮还使用 Kafka 官方 `kafka-console-producer.sh` 和 `kafka-console-consumer.sh` 写读两条消息。随后执行 120 秒短时 AFLNet fuzz，确认首个真实响应状态和有效执行数；完整四阶段状态图由 30 分钟正式验收判定。结果保存在所选输出目录。

## 按图片完成严格验收

```sh
KAFKA_BUILD_MODE=full KAFKA_CPU_LIMIT=1 KAFKA_MEMORY_LIMIT=1g \
  ./acceptance.sh apache-kafka-fuzz-bench "$PWD/results/strict-acceptance"
```

该命令校验 Apache 官方归档、构建 4.4.0 目标镜像，再执行 10 次协议稳定性回放、30 分钟 AFLNet fuzz、AFL 队列和崩溃样本的逐条独立 Broker 回放、JaCoCo 覆盖率导出，以及隔离故障探针的保存样本复现。最终 `ACCEPTANCE-REPORT.md` 按图片中的八项逐项判定，并生成 `SHA256SUMS` 与仅包含本次结果的 ZIP 交付包。只有全部项目有证据且 30 分钟运行真实结束后才报告通过。

## 语料和范围

`prepare_seeds.py` 可重复生成种子和 SHA-256 清单。有效会话涵盖 API 版本协商、预建主题元数据、写消息、读消息、偏移查询和协调器查找；另外包含未知 API key、不支持的版本与截断长度帧。`fuzz-topic` 是构建时创建的固定单分区主题。

本基准覆盖明文 Kafka Broker TCP 请求解析与处理、网络通道、主题元数据、Produce/Fetch 等业务路径。它不覆盖 TLS/SASL、跨节点复制、Kafka Connect、Streams、吞吐量、生产环境安全配置或客户端库本身。故障探针是验收 AFLNet 崩溃保存/独立重放能力的临时 TCP 服务，不表示在 Kafka 中植入故障，也不把探针崩溃记作 Kafka 漏洞。

上游项目与版本依据：[Apache Kafka 仓库](https://github.com/apache/kafka)、[4.4.0 固定提交](https://github.com/apache/kafka/commit/1156b2752aaa28eafc0b4c4d387e63356793268d)、[Kafka 协议说明](https://kafka.apache.org/protocol/)。
