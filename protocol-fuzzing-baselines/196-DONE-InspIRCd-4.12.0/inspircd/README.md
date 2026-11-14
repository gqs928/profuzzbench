# InspIRCd 4.12.0 IRC 协议模糊测试基准包

这是继 Memcached ASCII/TCP 基准包之后搭建的 ProFuzzBench 风格目标。测试对象为 InspIRCd 4，通过 TCP/6667 提供明文 IRC 服务；服务只在本机回环地址监听，并运行在独立 Docker 容器中。

## 已自动化的内容

- `Dockerfile` 固定 Ubuntu 20.04 镜像摘要、InspIRCd commit 和 AFLNet commit，并分别构建普通参考版、AFL 插桩 ASan 版和 gcov 覆盖率版。两个固定版本的 Git 源码归档随压缩包提供，构建时会先校验 SHA-256，不再从 GitHub 拉取源码；Ubuntu 软件包仍需要可用的镜像源/网络。APT 下载配置了 5 次重试，并使用 BuildKit 缓存保存已下载的软件包，遇到临时 HTTP 错误时重建不用从零下载。构建会把 InspIRCd 源码树中可识别的 UTF-8 文本文件 CRLF 统一转成 LF，避免补丁匹配失败、解释器带 `\\r` 或模板生成带回车的 `GNUmakefile` 文件名。
- InspIRCd 可执行文件安装在各源码目录的 `run/bin/inspircd`；配置、模块和运行数据位于对应的 `run/` 目录下。
- `aflnet-irc.patch` 为 AFLNet 及两个回放工具增加 IRC 协议选择器。适配器以 CRLF 切分客户端命令，并把三位数字回复和常见服务器命令映射为稳定状态 ID。
- `inspircd-shutdown.patch` 只调整 `Cleanup()` 中 FakeClient 与其 Server 的销毁顺序，避免 `FakeClient->Cull()` 读取已释放的 Server；4.12.0 上游已包含 `DoSafeUnload()` 的服务对象指针修复，因此不再重复打补丁。补丁不改 IRC 请求处理或响应行为。reference、AFL 和 gcov 三个构建都应用同一补丁，哈希写入 `build-versions.txt`。
- 构建镜像时会运行 `parser-test.c`，检查 IRC 请求边界切分和响应状态映射。
- `protocol_smoke.py` 分别对未插桩参考版和插桩版测试注册、PING/PONG、VERSION、JOIN/NAMES、TOPIC、PART 等正常协议流程，并检查插桩版退出清理阶段没有 ASan/UBSan 报告。
- `repeatability.py` 在全新 gcov 服务进程上重复回放频道业务种子 10 次：先等 `001` 确认 `NICK/USER` 注册完成，再按原种子顺序发送各条命令并等待对应协议响应，避免未注册时把后续频道命令一股脑发出。它检查状态序列、归一化响应是否一致，以及行/分支覆盖率波动是否不超过 0.5 个百分点；保存种子、每次原始响应字节、回放说明及原始/归一化哈希；只归一化数字回复 `003` 中动态生成的服务器创建时间。
- `coverage_replay.py` 将 AFLNet 队列中的用例回放到独立 gcov 版本，生成覆盖率随时间变化的 CSV 和详细 HTML 报告；`coverage_check.py` 检查注册、频道等核心命令处理函数是否有执行覆盖。
- `validate.sh` 串联正常协议测试、10 次新进程重复回放、短时 AFLNet 状态反馈、IPSM 图检查、队列回放覆盖率检查，以及单独的受控异常记录/独立回放检查。
- `crash_injection.py` 使用单独的 LD_PRELOAD 测试 shim 验证 AFLNet 是否能记录异常，并由 `aflnet-replay` 在新服务进程中独立复现。它只用于验收异常观测链路，不修改 InspIRCd 源码，也不代表上游本身存在这个崩溃。

2026-11-03 在 InspIRCd 4.12.0 上完成了严格验收：参考版与插桩版协议 transcript 一致；同一频道会话在 10 个全新 gcov 进程中的规范化响应一致，行/分支覆盖波动均为 0.1 个百分点；30 分钟正式运行得到 1,687 次执行、79 条路径、0 个真实 crash/hang，AFLNet stability=71.31%、bitmap=37.82%；正式队列 79/79 个输入均在独立 gcov 进程中回放。六个核心 IRC handler 均有执行覆盖。受控异常探针另行记录并独立复现了测试 shim 触发的 SIGABRT，不计为真实目标缺陷。完整数据见 `results/inspircd-4.12.0-validation/` 和 `results/inspircd-4.12.0-30m/`；新机器复现仍需保存对应的镜像与运行证据。

## 在 Kali 中构建

先将压缩包解压，在终端进入 `inspircd-benchmark` 目录，再运行：

```bash
chmod +x ./*.sh
./build.sh inspircd-fuzz --network=host --build-arg MAKE_OPT=-j1
```

源码已经随包提供，因此 AFLNet/InspIRCd 的 GitHub 连接超时不会再卡住源码获取步骤。Dockerfile 使用 Docker 内置 BuildKit 前端，避免额外在线拉取 Dockerfile frontend。APT 通过 Docker BuildKit 缓存保留索引和 `.deb`，同时对索引与包下载各重试 5 次。若最终仍报 HTTP 503，通常是快照服务暂时不可用；稍后用同一命令重试即可复用缓存。若报域名解析失败，则检查 Kali/Docker 到 Ubuntu snapshot 软件源的 DNS；不要往 Dockerfile 写死 DNS 地址，也不要长期复用旧 IP。

构建日志、版本/源码清单、镜像 ID，以及 Dockerfile、补丁、适配器和两个源码归档的 SHA-256 保存在 `build-logs/`。清单会记录上游固定 commit 和源码归档哈希。

## 快速验证

```bash
./validate.sh inspircd-fuzz "$PWD/inspircd-validation" 60s
```

预期证据包括：`protocol-smoke/` 下的通信记录、`repeatability/` 下 10 次全新进程回放结果、`smoke/fuzzer_stats`、`smoke/ipsm.dot` 及其渲染文件 `smoke/ipsm.plain`、`smoke/cov_over_time.csv`、`smoke/cov_html/index.html`、`crash-injection/` 下的受控异常样本与独立回放日志、模糊测试与覆盖率日志，以及 `build-versions.txt`。

## 启动 30 分钟模糊测试

快速验证通过后，可运行：

```bash
mkdir -p results
docker run --rm -v "$PWD:/workspace:ro" -v "$PWD/results:/results" inspircd-fuzz bash /workspace/run.sh aflnet /results/irc-30m '' 30m
```

运行器使用 AFLNet 的 `-P IRC -E` 状态反馈、`-R` 区域变异和 `-K` 每用例服务清理；服务以前台模式启动，并使用隔离的配置和运行目录。

## 验证异常记录与独立回放

此步骤仅验证“异常能被记录、样本能独立回放”这条工具链。脚本用有效的 `PING X\r\n` 作为无害种子，它会产生可识别的 PONG 状态；一次 bit-flip 将 `X` 变成 `Y`，得到 `PING Y\r\n`。仅在该测试进程中加载的 shim 看到完整触发请求后调用 `abort()`，不会改写源码或镜像。该受控异常必须单独标注，不能算作 30 分钟真实模糊测试发现的崩溃。完整版 `validate.sh` 会自动运行此步骤；若只需单独复测，可用下面的命令。

先确保 `TCP/6667` 空闲，并给结果目录一个全新路径，然后运行：

```bash
mkdir -p results
docker run --rm -v "$PWD:/workspace:ro" -v "$PWD/results:/results" \
  inspircd-fuzz python3 /workspace/crash_injection.py /results/crash-injection 180
```

通过条件是脚本报告 `PASS`，AFLNet 的 `fuzzer_stats` 中 `unique_crashes` 大于零，且新启动的服务在 `aflnet-replay` 回放后以 `SIGABRT` 退出；`crash-injection.json`、`replayable-crashes/` 和日志目录构成证据。失败时保留整个结果目录及错误日志，不要把“脚本已创建”写成验收通过。

## 版本固定与协议模型

- InspIRCd v4.12.0：`78159a35a6dba909c654a96ae92d8cb3340c8646`
- benchmark cleanup patch：`inspircd-shutdown.patch`（用于规避上游退出路径的迭代器释放后解引用；不改协议处理）
- ProFuzzBench AFLNet：`0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`
- IRC 请求帧：一条以 CRLF 结束的客户端命令；未完成的末尾数据作为一个畸形输入区域保留。
- 状态 ID：初始状态为 `0`；数字回复映射为 `1000 + 数字`；已识别服务器命令使用从 `2001` 开始的稳定 ID；未识别命令使用确定性哈希映射到固定范围。

InspIRCd 官方配置文档说明可通过 `<bind>` 配置客户端监听器；本基准仅在回环地址的 TCP/6667 上监听。参见 [v4 配置文档](https://docs.inspircd.org/4/configuration/) 和 [源码安装指南](https://docs.inspircd.org/4/installation/source/)。
