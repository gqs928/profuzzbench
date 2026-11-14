# Cyrus IMAP 基准测试结果

本报告分别记录短时完整验收和 30 分钟模糊测试。两项运行使用同一固定版本的 Cyrus IMAP 3.12.4 / AFLNet 镜像，但运行时长和证据各自独立统计。

## 1. 完整验收

从仓库根目录运行：

```sh
./full-acceptance.sh cyrus-imap-fuzz "$PWD/results/imap-validation-complete" 60s
```

**结果：通过，8 项验收条件全部通过。**本轮从源码重建固定目标，完成 20 次协议 smoke 会话、9 个种子的 3 轮逐条回放（共 27 次），并将 11 个响应状态映射到实际 IMAP 响应。三次独立短时 AFLNet 运行均未发现唯一崩溃或挂起。固定语料 gcov 覆盖率为行覆盖 16.9%、分支覆盖 11.7%；三次重置回放的覆盖率波动小于 0.1 个百分点。

逐项结论见 `results/imap-validation-complete/acceptance-status.md` 和 `results/imap-validation-complete/acceptance-report.json`；逐次运行数据和校验值也保存在该目录。受控崩溃可观测性验证使用独立测试夹具，不属于 Cyrus 缺陷。

## 2. 30 分钟长跑

按照 README 中的隔离 Docker 命令，使用当时已存在且通过固定源码归档校验的 `cyrus-imap-fuzz` 镜像运行：

```sh
docker run --rm --hostname localhost --network none \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/results:/results" \
  cyrus-imap-fuzz bash /workspace/run.sh /results/imap-30m 30m
```

- 宿主机实测运行 **1,801 秒**（2026-10-01 03:30:24–04:00:25，-04:00 时区）。
- AFLNet 的 `fuzzer_stats` 中 `last_update - start_time` 为 **1,800 秒**。此 AFLNet 2.56b 版本没有原生 `run_time` 字段；推算值和宿主机起止时间记录在 `results/imap-30m/runtime-verification.txt` 与 `.json`。
- Fuzzer 统计：1,541 次执行、76 条路径、76 个 queue 输入、稳定性 92.99%、bitmap 覆盖率 17.02%；IPSM 图有 16 个状态和 39 条转换。
- 未记录 Cyrus 崩溃或挂起（`unique_crashes=0`、`unique_hangs=0`），没有需要复现的样本。独立 fault-probe 夹具不计入这些数字。
- Coverage 回放处理全部 **76/76** 个 queue 输入，回放错误为 0。行覆盖率为 13,102/76,797（**17.1%**），分支覆盖率为 6,245/52,479（**11.9%**）；记录到 139 个新的 `.gcda` 文件。

### 超时说明

`run.sh` 使用 `timeout --signal=INT --kill-after=10s 30m` 包装 AFLNet。达到 30 分钟后，`timeout` 会发送 SIGINT；AFLNet 随后输出通用提示 “Testing aborted by user” 和 “Stopped during the first cycle, results may be incomplete”。本次确实是按设定时限结束：`fuzzer_stats` 时间戳跨度为 1,800 秒，宿主机实测为 1,801 秒；脚本将 AFLNet 超时状态 124 作为预期结束处理，并以 Docker 状态 0 退出。这不是人工提前中止，也不是 Cyrus 崩溃。`cycles_done=0` 表示截止时 AFLNet 尚未完成一轮完整语料遍历，因此结果是固定时长的运行快照，不代表完成了完整语料周期。

长跑详情见 `results/imap-30m/long-run-report.md`。Fuzz 日志、queue、`fuzzer_stats`、`plot_data`、`ipsm.dot` 和校验清单位于 `results/imap-30m/`；Coverage HTML、summary、回放日志、`coverage-provenance.txt` 和校验清单位于 `results/imap-30m-coverage/`。

## 历史证据说明

`results/imap-validation-final2/` 保留了有用的历史协议和 fuzzer 诊断，但其中的 gcov 覆盖率不能作为有效验收证据。旧回放设置了 `CYRUS_GCOV_PREFIX`，而服务器启动器读取的是 `CYRUS_PREFIX`，因此可能启动 AFL/ASan 构建。修正后的 `coverage_replay.py` 会选择并校验 gcov 构建路径；`coverage-run.sh` 在没有新的 `.gcda` 文件时会拒绝生成报告。

基准目标是固定版本的 Cyrus IMAP 3.12.4 明文 IMAP 服务。独立崩溃可观测性夹具从未链接到 Cyrus。
