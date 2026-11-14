# NFS-Ganesha 协议模糊测试基准

本目录把固定版本的 NFS-Ganesha V9.14 做成可重建、可重复回放的 NFSv3/TCP 模糊测试目标。配置只启用 `FSAL_MEM`，导出仅绑定容器回环地址；RPC 使用固定的 NFS/MOUNT 端口，不依赖 `rpcbind`、真实磁盘目录或宿主机服务。每条 AFLNet 用例启动一个新 Ganesha 进程，结束后进程内的内存文件系统随之销毁。

## 固定版本与改动范围

| 组件 | 固定版本 | 校验/依据 |
| --- | --- | --- |
| NFS-Ganesha | V9.14，`7af850559957b244e712280dd3590c4cbaedaae8` | `nfs-ganesha-V9.14.tar.gz` SHA-256 记在 `source/SHA256SUMS` |
| ntirpc 子模块 | `366b5c3c1f8cb4090df942ce57e9913be96406a9` | `ntirpc-*.tar.gz` SHA-256 记在 `source/SHA256SUMS` |
| AFLNet | `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732` | `aflnet-*.tar.gz` SHA-256 记在 `source/SHA256SUMS` |
| 构建镜像 | Ubuntu 20.04 digest 固定 | `Dockerfile` |
| Ubuntu 软件包 | Ubuntu Snapshot `20260928T000000Z` | `Dockerfile` 中固定快照地址 |

参考源码：[NFS-Ganesha V9.14](https://github.com/nfs-ganesha/nfs-ganesha/tree/V9.14)、[对应提交](https://github.com/nfs-ganesha/nfs-ganesha/commit/7af850559957b244e712280dd3590c4cbaedaae8)、[AFLNet](https://github.com/aflnet/aflnet/tree/0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732)。离线压缩包和补丁都在交付物中，构建过程不需要拉取 git 仓库。

`aflnet-nfs.patch` 将 ONC RPC record marker 切分、NFSv3/RPC 状态提取、NFS 协议注册和必要的网络读取调整接入 AFLNet。状态分层为 `0x10000 | NFSv3 status`、`0x20000 | RPC accept status`、`0x30000 | RPC reject status` 和 `0x40000`（格式错误）。这保留业务响应码，并避免 RPC 层和 NFS 层的相同数字被合并。构建关闭 rpcbind 注册，客户端直接访问固定端口；导出只开 TCP。AFL 编译器对 Ganesha 与动态 FSAL 执行边覆盖率插桩；插桩版不启用 ASan，因为上游以 `RTLD_DEEPBIND` 加载 FSAL 模块，与 ASan runtime 不兼容。补丁中的新增注释为中文；参考实现代码不作业务逻辑修改。

V9.14 的默认恢复后端要求对应安装前缀下预先存在 `var/lib/nfs/ganesha`。Dockerfile 为参考版、AFL 版和 gcov 版分别创建该目录；每条 fuzz 用例仍启动全新服务进程，NFSv3/FSAL_MEM 测量范围与目录预置无关。

## 快速运行

在有 Docker 的 Linux 主机上运行：

```bash
./build.sh
./acceptance.sh
```

`build.sh` 构建固定依赖的镜像。`acceptance.sh` 使用该镜像在隔离容器中跑完整验收，并将证据写到 `results/`。完整验收默认运行 AFLNet 30 分钟；可把秒数作为参数传入 `acceptance.sh`，小于 1800 秒的运行只适合开发调试，不满足图片中的 30 分钟验收项。

运行 `./package.sh` 会生成 ZIP 和 SHA-256 文件；交付包包含源码、补丁、种子生成/回放与覆盖率脚本，以及带 `evidence-manifest.json` 的完整运行证据。验收结论单独交付，其余正式验收结果随 ZIP 一并提供；没有完整证据清单的临时调试目录不会进入 ZIP。

也可以进入容器手动分步运行。NFS-Ganesha V9.14 在容器里使用 `AI_ADDRCONFIG` 解析 `Bind_addr`，所以要在 internal 网络中运行；普通 Docker `--network none` 缺少非回环 IPv4 地址，会使系统拒绝解析 `127.0.0.1`。

```bash
docker network create --internal nfs-ganesha-internal
docker run --rm --network nfs-ganesha-internal -v "$PWD:/workspace:ro" \
  -v "$PWD/results:/results" nfs-ganesha-fuzz \
  /workspace/acceptance-inner.sh 1800
```

`run.sh [秒数] [种子目录] [结果目录]` 可单独启动模糊测试。默认结果目录 `/results/fuzz-run`，默认时长 1800 秒。NFS 目标使用 1 秒单样本超时；`+` 允许 AFLNet 记录并跳过基线中的无响应边界样本。这里不启用 AFLNet 的 false-negative-reduction 模式，因为截断 RPC record 等协议边界输入本来就可能没有回复，把它们都计作挂起会污染挂起统计。目标进程的信号退出由 AFLNet 记录，故障探针会独立校验崩溃记录和回放。`clean.sh` 是 AFLNet 每个用例前调用的清理钩子。AFLNet 已经重启目标进程；FSAL_MEM 没有跨进程持久化文件，所以新进程就是干净初态，钩子不会删除用户数据或清理宿主目录。

## 正常流程与种子

`prepare_seeds.py` 先运行固定参考版，通过真实 MOUNTv3 `MNT` 回复取得根文件句柄，再生成 11 个请求种子。除根目录 `GETATTR`/`ACCESS`、不存在对象 `LOOKUP`、重复创建与错误边界样本外，还包含 `CREATE → LOOKUP → READDIR → REMOVE → LOOKUP(NOENT)` 和 `CREATE → WRITE → READ → REMOVE` 两条有序业务会话。WRITE/READ 使用真实 CREATE 回复中的文件句柄；参考版上独立进程回放 10 次验证该句柄在固定镜像和配置内可重复。`mount-root.bin` 单独发往 MOUNTv3 端口，参与种子回放和覆盖率；AFLNet 的初始语料只包含 NFSv3 请求，不把 MOUNT RPC 发到 NFS 端口。每个 `.bin` 都是按 TCP 发送的 ONC RPC record。

验收先用普通 RPC 客户端分别对参考版和 AFL 插桩版执行 `MNT → GETATTR → ACCESS → CREATE → WRITE → LOOKUP → READ → READDIR → REMOVE → LOOKUP(NOENT)`，每版新进程执行 10 次。随后每个种子都在对应协议端口独立重启服务回放；有因果关系的文件操作序列再重复 10 次，报告协议状态码、服务异常退出和日志路径。

## 覆盖率、异常和回放证据

完整运行在 `results/` 生成：

- `build-versions.txt`、`image-id.txt`、`image-digests.json`、归档 SHA-256 和 Docker 构建日志。
- `protocol-smoke/`：正常客户端的逐步请求、响应码、摘要和服务日志。
- `seed-replay/`：逐种子状态映射、请求序列、服务退出情况和独立日志。
- `fuzz/aflnet/queue/`、`replayable-queue/`、`replayable-crashes/`、`fuzzer_stats`、`ipsm.dot`、AFLNet 日志、运行参数、队列索引、时长和覆盖率统计。
- `coverage/run-*/coverage.csv`、`protocol-core-functions.csv`、`gcovr.xml`：gcov 独立构建分别清零 `.gcda` 后，对固定种子、最多 128 个 AFLNet 队列样本及全部崩溃样本逐个启动新进程回放；报告分别统计 NFSv3、MOUNTv3 handler 和 FSAL_MEM 的行、分支及函数命中。
- `fault-probe/`：单独构建的故障注入小服务用于校准 AFLNet 的异常退出发现与独立回放链路。它不属于 NFS-Ganesha，也不把人工触发的探针记作 Ganesha 漏洞；实际发现的 Ganesha 崩溃仍按原始服务进程退出码、日志和 `replayable-crashes/` 样本记录。
- `ganesha-anomaly-replay/`：将 AFLNet 保存的 Ganesha 崩溃/挂起候选还原为 RPC 线缆输入，在十个全新 AFL 插桩服务进程中独立回放，并逐次保存返回状态、退出码和日志；未复现的候选仍保留原样本与摘要，不计作已确认漏洞。

覆盖率的分母、分子和源码范围均保存在 CSV/XML 中，不使用只有一个 `.dot` 文件的状态截图代替覆盖率。逐函数 CSV 由 gcov 的函数调用明细生成；`ipsm.dot` 是 AFLNet 实际观测到的响应状态迁移图，`fuzzer_stats` 中保存 `variable_paths`、稳定性和位图覆盖率。每个输入由全新服务进程处理，清除 `.gcda` 后独立累积一次语料覆盖率，因此不同运行的 CSV 可直接比较。

## 验收约束与已知范围

此基准刻意限定在 Linux 上 NFSv3 over TCP、ONC RPC record marking、MOUNTv3 和内存 FSAL。它不覆盖 NFSv4、UDP、RDMA、TLS、NLM、真实 VFS/后端 FSAL，也不表示上游所有构建选项都已验证。NFSv3 的文件句柄从固定服务的真实 MOUNT 回复取得，重复性在同一镜像、配置和服务版本范围内验收。30 分钟模糊测试的发现结果属于一次运行证据；未发现崩溃不能证明没有漏洞。

图片中的验收映射见 `ACCEPTANCE.md`；源码归档、源码引用和补丁校验见 `source/` 与 `source/SHA256SUMS`。项目内新增脚本和代码注释采用中文。
