# InspIRCd 4.12.0 基准化验收报告

运行日期：2026-11-03（UTC）。目标源码固定为上游 commit `78159a35a6dba909c654a96ae92d8cb3340c8646`，AFLNet 固定为 `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`。镜像 ID 为 `sha256:a5e5d0861d3383b97ff7f64594fae13e87cd61b394419f81dc56c2cf6dd6a51f`；源码归档与补丁哈希见 `build-logs/build-versions.txt`。

## 验收结果

- 普通参考版和 AFL 插桩版通过注册、PING/PONG、VERSION、JOIN/NAMES、TOPIC、PART 协议流程。
- 相同 IRC 频道会话在 10 个新 gcov 服务进程中重复回放成功，规范化响应/状态完全一致；行和分支覆盖波动分别为 0.1 和 0.1 个百分点。
- 60 秒预检产生 66 次执行、3 条路径；IPSM/覆盖率回放成功，核心 VERSION、NICK、USER、QUIT、JOIN、TOPIC handler 均有执行行覆盖。
- 受控异常探针由测试专用 `LD_PRELOAD` shim 将一位变异输入变为 `PING Y`，AFLNet 记录 1 个探针 crash，`aflnet-replay` 在全新服务进程中复现 SIGABRT。它不属于真实 fuzz 缺陷。
- 正式运行时长 1800 秒（05:59:39–06:29:39 UTC）：`execs_done=1687`、`paths_total=79`、`variable_paths=79`、`stability=71.31%`、`bitmap_cvg=37.82%`、`unique_crashes=0`、`unique_hangs=0`。AFLNet 以预期的 timeout/INT 结束（exit 124）。
- 正式队列 79/79 个输入均在独立 gcov 服务进程中回放，服务异常退出为 0。最终全项目 gcov 汇总为行覆盖 14.9%（5032 行）、分支覆盖 6.9%（3998 分支）；报告在 `irc-30m/cov_html/index.html`，逐样本覆盖时间序列在 `irc-30m/cov_over_time.csv`。

AFLNet stability 与 4.10.1 的历史 30 分钟运行（73.01%、37.35% bitmap、0 crash/hang）接近；协议重复性及覆盖回放均通过。该稳定性读数反映当前 IRC/AFLNet 服务重启方式下的位图变化，不应替代独立协议 transcript 与 gcov 重复性检查。

## 证据路径

- `inspircd-4.12.0-validation/`：协议 smoke、10 次新进程重复性、短时 AFLNet、核心处理函数覆盖检查、受控异常记录与独立回放。
- `inspircd-4.12.0-30m/irc-30m/`：正式 30 分钟队列、fuzzer 统计、IPSM、逐队列 gcov 回放和 HTML 报告。
- `build-logs/`：完整构建日志、版本清单、构建输入 SHA-256 和镜像 ID。
