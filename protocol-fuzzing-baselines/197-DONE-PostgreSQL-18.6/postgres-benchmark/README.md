# PostgreSQL 前后端协议模糊测试基准

把 PostgreSQL 固定成一条命令即可重建、回放和复核的 AFLNet TCP 服务端目标。协议适配代码只负责请求切帧和响应状态反馈，不改 PostgreSQL 服务端业务逻辑。

## 固定目标与依赖

- PostgreSQL：官方 18.6 源码发布归档，文件 postgresql-18.6.tar.bz2；SHA-256 为 555610c24d53e4316da5b7d3fc25c279d96856d5e0e23ee308c328c5fa881d9f。来源是[上游仓库](https://github.com/postgres/postgres)的 REL_18_6 发布源码。
- AFLNet：提交 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732；归档和 SHA-256 随包提供。
- 容器：Ubuntu 20.04 基础镜像按 OCI digest 固定；构建依赖取自 20260928T000000Z Ubuntu Snapshot。-j2 限制并行编译内存。
- 构建三份相同配置的服务端：普通参考版、AFL 插桩版、GCC gcov 覆盖率版。AFL 插桩版不启用 ASan：PostgreSQL 18.6 后端在当前固定的 AFLNet ASan 运行时下会于进程初始化阶段段错；关闭 ASan 后，同一 AFL 插桩后端可正常启动，AFLNet 仍可采集分支和异常退出。
- AFLNet 补丁增加 PostgreSQL 解析/状态映射；因 PostgreSQL 没有服务端首包，适配器跳过无效等待，并在服务就绪后清零启动覆盖、在关机前保存请求覆盖，避免后台进程噪声淹没协议反馈；对启动期间被拒绝的连接使用新套接字重试，避免复用已失败套接字；另修复该版本在无 forkserver 模式下 `-K` 忙等僵尸子进程的问题和 SIGINT 中断时的 `waitpid` 误报。`source-checksums.sha256` 固定构建脚本、解析器、补丁、种子和两个源码归档，每次构建前自动核对。

PostgreSQL 18.6 于 2026-08-13 发布，PostgreSQL 18 支持协议 3.2。详情见[官方版本公告](https://www.postgresql.org/about/news/postgresql-186-1711-1615-1519-1424-and-19-beta-3-released/)及[协议文档](https://www.postgresql.org/docs/18/protocol.html)。

## 协议适配

postgres_aflnet.c 识别无类型长度字段的 Startup、SSL、GSS、Cancel 请求以及常规类型/长度消息。畸形或截断尾部仍作为 AFLNet 变异区域保留。后端响应会按认证、就绪事务状态、命令、行描述、数据行、扩展查询、COPY、错误、参数状态和协商结果生成固定状态 ID。状态与协议语义逐项列于 [postgres-state-mapping.md](postgres-state-mapping.md)。

seeds/ 有 13 条确定性协议会话，覆盖登录与数据库拒绝、简单 SQL 读写、事务失败后回滚、Parse/Bind/Describe/Execute/Sync、COPY 输入、SSLRequest 明文拒绝后启动、协议 3.2、空查询、多语句和消息长度边界。清单含每条种子的字节数、报文数、SHA-256 和中文用途说明。

## 一键构建和短时预检

需要 Linux、Docker BuildKit 和可访问的 Docker daemon。工作目录中执行：

    cd postgres-benchmark
    ./build.sh postgres-protocol-fuzz
    ./validate.sh postgres-protocol-fuzz "$PWD/results/preflight" 180s

build.sh 固定源码与依赖，构建后保存版本、镜像 ID、Docker 构建日志和输入文件哈希。validate.sh 用 psql 与原始 TCP 客户端检查正常登录和 SQL 读写、事务恢复、扩展查询、COPY、拒绝响应、SSLRequest、协议 3.2；参考版和插桩版各回放 10 次，并检查 AFLNet 状态图。

## 图片要求的严格验收

    ./acceptance.sh postgres-protocol-fuzz "$PWD/results/strict-acceptance" 1800s

严格验收会通过 Dockerfile 按固定版本构建镜像（可复用校验一致的构建层）、重放 13 条种子并验证业务状态、同一种子使用全新集群重复 10 次并比较响应轨迹、连续 AFLNet fuzz 30 分钟、逐条回放队列/崩溃/挂起样本、导出 PostgreSQL 协议核心代码行/分支/函数覆盖率，并独立运行一次故障探针检查 AFLNet 崩溃记录链路。开始 30 分钟计时前，脚本先给 AFLNet 180 秒完成多进程服务端种子校准。AFLNet 目标是编译插桩的 C 启动器：每轮先调用中文注释的 clean.sh 重建 PGDATA，再启动 PostgreSQL 并通过 pg_isready 确认服务就绪；AFLNet -K 结束本轮时，启动器会向 PostgreSQL 转发停止信号并回收服务进程。每条 fuzz 样本最多等待 10 秒。gcov 回放也先等 pg_isready，再用 fast 模式停库以便后端覆盖数据落盘；固定 Ubuntu 快照中的 gcovr 4.2 按 tcop 与 libpq 源码目录分别采集，函数覆盖百分比由 GCC gcov 记录汇总。最终生成按图片 8 项标准逐条判定的 acceptance-report.md / .csv，以及每份证据的 SHA-256 清单。

构建成功不等于严格验收通过。报告中某项缺少证据、AFLNet 状态图未到达核心状态或关键处理函数覆盖数为零时，验收脚本会返回失败。

## 打包

    ./package.sh "$PWD/results/postgres-protocol-benchmark.zip"

ZIP 同时包含构建所需的 PostgreSQL/AFLNet 源码归档、解析器、补丁、种子、脚本和中文说明；同目录会生成 ZIP 的 SHA-256 文件。

## 运行隔离与范围

容器使用 --network none，PostgreSQL 仅监听回环地址，测试认证使用固定的 trust 配置。每个种子或 fuzz 样本使用新建的 PostgreSQL 数据目录；查询和异常响应逐帧记录。故障探针是专门验证 AFLNet 记录/重放异常退出的测试程序；探针 SIGABRT 不代表 PostgreSQL 本身存在已知崩溃。

本基准不测吞吐量，也不覆盖 TLS 加密通道、SCRAM/OAuth 凭证生成、复制协议或取消请求的第二条连接。正常流程会测试 SSLRequest 返回明文拒绝后继续 Startup。
