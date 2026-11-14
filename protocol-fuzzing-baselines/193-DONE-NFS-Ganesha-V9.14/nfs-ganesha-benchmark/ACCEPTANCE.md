# 图片验收映射

| 图片要求 | 本交付物 | 验收证据 |
| --- | --- | --- |
| 目标、依赖与模糊器版本固定；Docker 可重建 | `Dockerfile`、固定 Ubuntu digest 与 snapshot、固定源码归档及 SHA-256 | Docker 构建日志、镜像 ID/digest、版本记录 |
| 原版和测试版均能走通正常协议业务流程 | `protocol_smoke.py`、真实 MOUNTv3 和 NFSv3 客户端请求 | `protocol-smoke.json`，参考版与插桩版各 10 轮 |
| 有先后状态操作，种子进入业务状态 | `prepare_seeds.py` 先从 MNT 取得 filehandle，再生成 CREATE/LOOKUP/READDIR/REMOVE 与 CREATE/WRITE/READ/REMOVE 会话；另有独立 MOUNT 种子 | 种子清单、逐请求响应序列、十次因果种子回放 |
| AFLNet 状态有实际响应依据 | `nfs_aflnet.c` 和 `aflnet-nfs.patch` 解析 RPC accepted/denied 与 NFSv3 status | 解析器单元输出、`ipsm.dot` 和 `fuzzer_stats` |
| 覆盖率数据可复核，列出核心函数 | 独立 gcov 构建；NFSv3、MOUNTv3、FSAL_MEM 限定报告 | 多轮 `coverage.csv` 行/分支计数、逐函数 CSV、gcovr XML、回放命令 |
| 每轮可复位 | 每个输入由 AFLNet 启动独立服务进程；FSAL_MEM 状态不写入持久文件 | `clean.sh`、每条独立进程回放记录、稳定业务状态摘要 |
| 异常退出可观测 | AFLNet 目标进程的 crash/hang 目录；自动将 Ganesha 异常候选用十个全新服务进程独立回放；故障探针校准确定性崩溃记录与回放。NFS fuzzing 不启用把无响应误记为挂起的选项 | AFLNet 日志、`fuzzer_stats`、异常样本 SHA 与每次重放的响应/退出码、SIGABRT 独立回放报告 |
| 结果可复查 | 参数、时间、队列、状态图、覆盖率、日志和哈希一起保留 | `results/` 下的 JSON、CSV、XML、文本日志和打包 SHA-256 |

图片建议的完整验收顺序由 `acceptance-inner.sh` 自动执行：全新镜像构建、正常客户端 10 轮、同一种子 10 轮、AFLNet 运行 30 分钟、三轮独立覆盖率构建回放，以及故障探针记录与复现。缩短 AFLNet 时长的开发运行不会被标记为完整验收。
