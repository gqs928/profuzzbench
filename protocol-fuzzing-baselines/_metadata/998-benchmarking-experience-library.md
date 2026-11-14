# 协议实现基准化经验库

本文件将 12 个已完成协议的经验集中管理。每个协议交付单元单独保存源码锁、适配器、构建/运行脚本和验收证据；本经验库不嵌入单个协议包。

## 1. uftpd 2.17（FTP）

- FTP 命令解析器本身无需改写；关键适配是把服务生命周期改为“一条 AFLNet 用例对应一个目标进程”。原版按连接 `fork()`，会让崩溃落在孙进程且父进程状态跨用例残留。去掉 fork 时应保留每会话独立的事件上下文，并一起移除依赖父子进程组的 `setpgid()`，否则服务清理信号可能误杀 AFLNet。
- 种子需使用真实 CRLF，覆盖多命令会话、认证、主动/被动数据通道、文件操作和最小命令；使用字典提升命令词命中率。
- v2.17 30 分钟记录：13,339 execs、221 paths、0 crash/hang。证据来自 `uftpd-results-30m/`。框架经验：协议处理代码不必变更，生命周期适配与协议 parser 要分层。

## 2. Asterisk 23.5.0（SIP/TCP）

- 从 Asterisk 22 系列更新到 23.5.0 时，锁定 Asterisk 源码 commit、PJPROJECT 2.17 和 AFLNet commit，三种构建变体都用同一组固定依赖；仅比对标签不足以复现构建，需把源码归档哈希写入 build lock。
- 用 OPTIONS、REGISTER、带 SDP 的 INVITE/CANCEL 构造完整事务，再加入截断长度和错误正文种子。先用普通版与插桩版各重复 10 次会话，逐响应比较 transcript 和端口复位，再启动长测。
- 状态反馈保留 SIP 的 100/200/487 等实际响应；目标可能很慢，运行耗时和每样本 timeout 要单独记录。短时预检与正式 30 分钟数据分开保存。
- 23.5.0 正式运行 1,800 秒：797 execs、29 paths、29 variable paths、95.43% stability、46.41% bitmap、0 crash/hang。29/29 queue 样本 gcov 回放成功、0 异常退出；PJSIP 核心覆盖 5,570/26,994 行、1,933/22,413 分支、命中 431 个函数。29 组变动路径各复播 10 次（290 次），670 个响应均可比对且端口释放。可复用规则：服务重启型 SIP 目标需用独立进程重复业务对话，不用 AFL 位图稳定度代替 transcript 一致性。

## 3. NFS-Ganesha V9.14（NFSv3/TCP）

- V9.14 构建时固定 ntirpc 子模块 commit 与归档哈希；`AI_ADDRCONFIG` 在只有 loopback 的 `--network none` 环境可能拒绝解析 `127.0.0.1`，应使用仅容器可见的 internal bridge 网络，不要因此开放宿主机端口。
- 采用 FSAL_MEM 与固定 NFS/MOUNT 端口，可避免真实磁盘、rpcbind 和外部服务状态；每条用例运行新服务进程，让内存文件系统随进程清理。
- AFLNet 适配需先按 ONC RPC record marker 切片，再区分 RPC accept/reject 与 NFSv3 status。给层级状态使用不重叠 ID 前缀，避免相同数字状态被合并。因 FSAL 使用 RTLD_DEEPBIND，ASan runtime 不兼容时应保留 LLVM 边覆盖并记录原因。
- V9.14 增加了安装前缀内的默认恢复目录要求；参考版、AFL 版与 gcov 版均需预先创建 `var/lib/nfs/ganesha`，否则服务在首次启动前会失败。容器内网桥也保留在配置中，以满足 `AI_ADDRCONFIG` 的地址解析行为。
- 正式运行 1,800 秒：8,717 execs、97 paths、96 variable paths、84.47% stability、17.29% bitmap、2 crash candidates 和 9 hang candidates。11 个异常候选各以新进程复放 10 次，0 个确认复现；单独的测试故障探针则按预期复现 SIGABRT，不计入自然 fuzz 缺陷。队列覆盖回放 3 轮、每轮 110 个样本均完成；NFSv3/MOUNTv3/FSAL_MEM 范围覆盖 1,161/4,698 行（24.71%）、367/2,825 分支（12.99%），78/353 个函数有覆盖。
- 可复用规则：协议层级状态要做命名空间隔离；容器网络选项和版本新增运行时目录都应纳入验收矩阵；AFL 候选需以独立进程重复复放后再判定为可复现异常。

## 4. Cyrus IMAP 3.12.4（IMAP）

- 30 分钟记录：1,541 execs、76 paths、0 crash/hang；76/76 queue 覆盖回放成功，行覆盖 17.1%、分支覆盖 11.9%。完整验收包括 20 次协议 smoke、9 个种子各 3 轮回放和三轮短 fuzz。
- 认证、邮箱选择和邮箱数据是状态化输入的前置条件；相同 transcript 的逐轮核对与 gcov 计数波动是两种不同稳定性证据，应分别保存。
- 可复用规则：IMAP 语料以同连接内状态转换组织，用户/邮箱目录需在每轮前确定性重建。

## 5. Dovecot 2.4.5（IMAP）

- 将移动的 main snapshot 改为稳定发布标签 2.4.5，并固定 commit、UCD 18.0.0 数据校验值、AFLNet 和 Ubuntu snapshot。版本号应来自稳定标签，不能从 main 分支的版本字符串推断。
- 普通服务回放需要受限启动器和确定的邮箱目录；模糊阶段切换到固定服务账户/root launcher 时要防止权限代理截断 AFL forkserver。Clang 10 ASan 运行时无法启动目标子服务时保留 AFL 插桩并把该限制写入 lock 和报告。
- 正式运行 1,800 秒：1,609 execs、32 paths/variable paths、88.62% stability、16.10% bitmap、0 natural crash/hang。20/20 参考版与 AFL 版协议 smoke 通过，固定 login-mailbox 种子 10 次回放稳定；gcov 回放 32 条队列，IMAP 行覆盖 2,340/22,265（10.51%）、分支 908/8,761（10.36%）、关键函数 105/225。回放含 10 条完整应答、22 条部分结束，其中 5 次标签等待超时，服务端非零退出为 0；需把此限制与覆盖统计一并保留。
- 验收脚本的故障探针容器必须显式以 root 启动，因为其临时 setuid 助手需要 root；否则会在探针实际运行前因 EUID 检查失败。30 秒探针只完成 34 次执行、未命中注入；不能由“进程可启动”推断故障观测链路有效。完整 1,800 秒探针执行 2,111 次，AFLNet 记录 2 个 crash 且均可回放；测试源码补丁在退出前已撤回，注入标记仍只存在于临时测试二进制中。
- 可复用规则：特权服务应把服务控制封装为参数固定的 launcher，并分别验证协议回放身份与 fuzzer 身份；注入探针同时检查注入标记、崩溃样本和补丁撤回状态。

## 6. InspIRCd 4.12.0（IRC）

- 从 4.10.1 更新后，源码 tar 顶层目录变化需要在解包时显式 `--strip-components=1`；旧清理补丁有一段已被新版本上游修复，应只保留仍需要的变更，不要强行套用旧 patch。
- 30 分钟记录：1,687 execs、79 paths、0 crash/hang；79/79 queue 回放成功，覆盖行 14.9%、分支 6.9%。频道会话需覆盖注册、PING/PONG、JOIN/NAMES、TOPIC、PART 等 handler。
- 受控崩溃只能作为观测链路探针，必须与自然 fuzz 的真实 crash 数分列；本轮探针由临时 shim 注入，不属于 InspIRCd 缺陷。
- 可复用规则：版本适配自动化先检查 tar 目录布局和 patch hunk 是否仍适用，再构建；对状态图检查真实协议响应节点。

## 7. PostgreSQL 18.6（PostgreSQL 前后端协议）

- 当前稳定版已固定为官方 REL_18_6 源码归档，哈希必须随 lock 保存。目标消息既有带类型的常规帧，也有 Startup/SSL/GSS/Cancel 等无类型首包；截断尾部保留给目标，而不是丢弃。
- PostgreSQL 后端派生多进程，AFL 插桩应在服务 ready 后清零启动覆盖、停库前保存请求覆盖；每轮重建 PGDATA，并在停止时回收后端，避免初始化噪声和僵尸进程污染结果。
- ASan runtime 与当前后端初始化不兼容时可禁用 ASan，但需保留 AFL 边覆盖、崩溃观测和独立故障探针，报告不能把“未启用 ASan”隐去。
- 正式运行 1,800 秒：921 execs、38 paths、24 variable paths、96.83% stability、28.86% bitmap、0 natural crash/hang。13/13 初始种子重放、10 次稳定会话对照通过；38/38 队列覆盖回放完成，服务器异常退出 0。tcop 覆盖行/分支 651/1,508（43.2%/23.8%），libpq 330/2,172（15.2%/8.1%），命中 7 个关键处理函数。独立探针样本可复现预期 SIGABRT，测试探针与自然 fuzz 数据分列。
- 原包缺失 README、校验清单和构建输入列表引用的 `package.sh`；先补齐可验证验收报告后打包脚本，并把新脚本纳入 SHA-256 校验，再开始重建。
- 可复用规则：多进程服务器应在业务就绪边界重置覆盖，并在故障注入前后区分生产构建与探针构建；自动交付前应执行 README 指定的所有本地入口并核对文件存在性。

## 8. Redis 8.10.3（RESP2/RESP3）

- 从 8.10.1 更新到 8.10.3 后，重新锁定官方归档与 SHA-256，并重新构建普通、AFL/ASan、gcov 三套目标；版本文字替换不能替代重跑统计。
- RESP parser 需覆盖嵌套 aggregate、RESP3 streamed aggregate/bulk、inline 请求、长度边界和 AUTH 状态。每次覆盖回放启动新 Redis 并用临时数据目录，避免数据库状态泄漏。
- 历史 8.10.1 记录的位图 stability 偏低但后两轮业务 response trace、核心命令覆盖一致；记录时应同时保留 AFL 原始波动和独立复放结论，不能只报一个稳定度数字。
- 8.10.3 正式运行 1,800 秒：4,589 execs、206 paths/variable paths、85.06% stability、13.06% bitmap、0 crash/hang。RESP2/RESP3 smoke 与 reference/ASan 对照通过；206/206 队列样本在新 Redis 临时目录上完成三轮覆盖回放，服务端退出 0，三轮文件行/分支均为 9,114/77,070（11.8%）和 3,575/54,343（6.6%），11 个核心命令函数 CSV 完全相同。18 条畸形/截断输入未收到 RESP，应答函数无回放错误，服务端均由 harness 正常关闭；该行为单列而非算作崩溃。
- 异常探针经验：AFLNet `-C` 保存的一个 Redis 8.10.3 变异 SIGSEGV 候选，在 ASan 目标的独立回放中未能于 5 秒内导致进程退出，因此保留候选并标为未复现；不要因为 fuzz 输出目录名叫 `replayable-crashes` 就视为确认缺陷。另用固定有效 AUTH → DEBUG SEGFAULT 种子，临时启用 DEBUG 后独立复现 -11，单独证明检测链路正常。自然 fuzz 的 0 crash/0 hang 与这两项探针证据分栏报告。
- 可复用规则：协议状态重放与原始插桩位图是两个验收指标；RESP 输入即使无应答也要区分“服务端异常退出”与“正常关闭前没有响应”，并用多轮覆盖回放核实函数覆盖稳定性。

## 9. Memcached 1.6.45（ASCII/TCP）

- 目标范围只含 ASCII/TCP，未把 UDP 或 binary protocol 混入同一结果。AFLNet parser 按 CRLF 命令分帧，并按声明字节数保留存储命令 body；错误长度/截断 body 作为原始尾部区域。
- 30 分钟验收记录：1,538 execs、106 paths、0 crash/hang、稳定度 92.61%；十次新进程重放比较完整响应哈希。核心文件 `memcached.c`、`proto_text.c`、`proto_parser.c`、`items.c` 均有行覆盖。
- 可复用规则：范围写清楚到传输与文本/二进制协议；每次请求后的缓存状态需借助独立服务进程重置。

## 10. FreeRADIUS 3.2.10（RADIUS/TCP）

- 30 分钟记录：1,624 execs、44 paths、0 crash/hang；参考版和 AFL 版 10 次 PAP/Accounting transcript 相同，队列 44 项已独立回放。协议状态至少区分 Access-Accept、Access-Reject 和 Accounting-Response。
- 对半径长度字段做帧边界检查，合法认证/拒绝与记账请求均需进入种子集；隔离受控 crash probe 和真实 fuzz 结果。
- 可复用规则：多传输模式要选定并明确，本次 RADIUS/TCP 数据不能推断 UDP 结果；业务状态标签按响应码映射。

## 11. Apache Kafka 4.4.0（二进制协议）

- 先校验实际运行目标，而不是只看工作树的 source-lock：旧 overlay 镜像实际仍是 Kafka 4.2.2，尽管锁文件已更新为 4.4.0；应从运行镜像读取 `build-versions.txt` 并用 Broker `--version` 复核，不匹配时旧统计全部作废。
- 在资源受限 VM 上，使用 Apache 官方 4.4.0 二进制归档作为实际 Broker、官方源码归档作 JaCoCo 源码映射；两份归档均固定 SHA-512，版本、commit、JDK、Scala、AFLNet 和 JVM agent 一并记录。这样跳过慢速 Gradle 冷编译，但仍用真实发行 Broker 测试，不把锁文件版本当作运行版本。
- Kafka 状态反馈来自 JVMTI 中 `KafkaApis` 处理方法命中；JaCoCo 行/分支覆盖单独在干净 Broker 上回放队列。官方发行包没有 Gradle `build/classes`，字节码在 runtime JAR 中；本次发现 `KafkaApis.class` 位于 `kafka_2.13-4.4.0.jar`，JaCoCo 的 `--classfiles` 应读取发行包 `libs/` 下 Kafka JAR，源码行号则从同版本源码归档的 Java/Scala 目录映射。框架需同时支持“构建输出目录”和“已编译发行归档”两类 classfile 来源。
- Kafka 每个 AFL 样本都冷启动一个 JVM；正式 30 分钟运行仅完成 156 次执行、10 条路径，最高 RSS 191 MiB、最慢样本约 17.5 秒。短测到时返回 timeout 状态码时，要先检查 `fuzzer_stats` 是否已完整落盘和有效执行数，不能仅按 wrapper 退出码判失败。正式运行记录 1,800 秒、100% 稳定度、0 自然 crash/hang。
- 10/10 队列输入逐一由新 Broker 回放，错误 0、异常退出 0。`KafkaApis` 覆盖 300/2,507 行（11.97%）、95/1,302 分支（7.3%）；参考和插桩版本的 10 轮客户端 transcript 一致，Kafka 官方 producer/consumer 写读成功。隔离探针另存一条可独立复现的 SIGABRT 样本；它证明异常观察链路有效，不计为 Kafka 漏洞。
- 可复用规则：昂贵 JVM 服务将目标重置/启动成本写入运行参数，分别报告协议 transcript、JVMTI 状态命中和 JaCoCo 行分支；从发行归档构建覆盖率报告时，由包管理清单发现 JAR，不假设源码目录含编译产物；构建、预检和正式 fuzz 的镜像 ID、build version 要逐一比对。

## 12. Mosquitto 2.1.2（MQTT/TCP）

- 2.1.2 新增 `libcommon/` 和 cJSON 依赖；三套变体都要按 libcommon/lib/src 顺序构建。只测 MQTT/TCP 时关闭默认 HTTP API；gcov 汇总要纳入新源目录。
- MQTT 3.1.1 与 5.0 种子覆盖 CONNECT、SUBSCRIBE、PUBLISH、UNSUBSCRIBE、PINGREQ、DISCONNECT、截断和错误长度。30 分钟结果为 5,882 execs、145 paths、0 crash、2 个 hang 候选；两条都在普通版与 ASan 版复放为无响应后关闭连接、broker 仍存活，不能记为目标崩溃。
- 145/145 queue 覆盖回放成功，覆盖行 23.9%、分支 14.1%。可复用规则：版本升级后重新发现 gcov 目录；AFL hang 候选要用独立实例、观察响应/进程状态后分类。

## 面向自动基准化框架的通用规则

1. 版本发现后锁定稳定 tag/commit、源码归档校验值、子模块、编译器/工具链、基础镜像和系统包快照；主分支字符串不能代替稳定发行版。
2. 从构建系统发现目标源目录和新增依赖，生成普通/AFL/gcov 变体矩阵；对新默认功能按基准范围显式开关。
3. 每个目标分别声明帧边界、状态提取和目标复位策略；网络层、RPC/协议层状态编号分域，畸形尾部按目标的错误处理路径保留。
4. 在长 fuzz 前跑 parser 单测、真实协议 smoke、普通/插桩响应对照、固定种子多次新进程回放和短时状态图检查。
5. 正式运行后对 queue/crash/hang 逐条独立回放并导出覆盖率；记录范围、跳过原因、退出码、响应、覆盖变异与环境资源。
6. 分开报告 fuzzer 分类与缺陷复现。受控异常探针需在报告中标明“测试夹具”，不计入自然 fuzz 的 crash/hang 数。

## 证据索引

本文件集中交付全部 12 项协议的基准化经验；单个协议 ZIP 不包含重复经验条目。
