# NanoMQ 0.25.6 MQTT/TCP 基准验收

**状态：已完成正式基准；稳定性与覆盖深度受限。** 本报告区分已验证的运行信号与不能据此推断的结论。正式轮没有报告 crash/hang，不等于目标不存在缺陷。

## 范围与来源

- 目标：NanoMQ 0.25.6，单节点、匿名访问、明文 MQTT/TCP，监听容器内 `127.0.0.1:1883`。
- 协议范围：MQTT 3.1.1 与 MQTT 5.0。TLS、WebSocket、HTTP API、持久化、集群和桥接不在本轮范围内。
- 上游源码 commit：`926179ec41adbb8dbc0a191746ea78d91d53c463`；源码归档 SHA-256：`1f008a001e024dde3e407435f36dd26dae57c8ecbed415a6d9633d5ecbf1ba04`。
- AFLNet commit：`0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`；归档 SHA-256：`251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d`。
- 固定子模块：NanoNNG `ebd4b8424735f72652b625f9167663683164aafd`、l8w8jwt `ee445f6ea334aac03daa9cbc1efea630f7744aba`、nftp-codec `e14f1811b21cc0301f758e3317c730f96e96a604`。
- 构建基础镜像：`ghcr.io/emqx/emqx-builder/6.2-3:1.19.1-28.4.1-7-ubuntu24.04@sha256:7134ef634abc6021f100c2a16cb83b40fed2a44671037ba2d25ca0c0fa21d12d`。

## 构建、服务与反馈验证

NanoMQ 与 NanoNNG 均使用 AFLNet `afl-gcc` 编译插桩，目标二进制记录了 124 个 AFL 插桩符号。正式轮绑定镜像 ID `sha256:379e31e7941c60fa526190ca66020e5998e1dc450895a167d9021bf475ab0a8a`。shell launcher 最终 `exec` 该 ELF；只有在确认 MQTT 应用层 smoke、forkserver 握手和实际目标插桩后才设置 `AFL_SKIP_BIN_CHECK=1` 跳过 AFLNet 对脚本文件的预检。

应用 smoke 对 MQTT 3.1.1 和 5.0 各运行 3 轮发布/订阅事务，6/6 通过。AFLNet MQTT parser 的正常帧、截断剩余长度和畸形尾部检查也在正式轮前完成。目标以单 task-queue 线程、单最大 task-queue 线程和 `parallel=1` 运行；每次启动后设置 500 ms 等待。

正式响应状态图包含 7 个状态和 7 条边：成功 CONNACK `2000`、MQTT 5 CONNACK 错误返回码 `2129`、SUBACK `109`、PUBLISH `103`、UNSUBACK `111`、PINGRESP `113` 及初始状态 `0`。AFLNet 另报告 `bitmap_cvg=8.93%`；这是插桩位图反馈，不是源码行/分支覆盖率。本轮没有生成独立源码覆盖率或逐队列覆盖回放报告。

## 正式轮结果

| 指标 | 结果 |
|---|---:|
| 运行时间 | 1,801 秒（外层超时退出码 124，符合 1,800 秒计划） |
| 执行数 | 2,509（约 1.19 exec/s） |
| `paths_total` / `paths_found` | 64 / 59 |
| `variable_paths` / stability | 64 / 47.26% |
| AFL 位图覆盖反馈 | 8.93% |
| `cycles_done` | 0，正式轮结束时仍未完成首轮队列周期 |
| unique crash / hang | 0 / 0 |
| 最慢样本 | 1,136 ms |

5 个初始种子在 AFLNet dry-run 中都出现 instrumentation-output varies 警告，且 AFLNet 将目标标为较慢。60 秒预检记录 60 次执行、5 条初始路径，最终统计稳定度为 0%，所以启动正式轮是为了保留完整运行证据；结果应标为**低稳定度、低吞吐的探索性基准**，不能当作稳定覆盖率对比基线。低稳定度可能来自目标或其异步运行时的非确定性；本轮没有把根因归结到单一线程或某个具体子系统。

## 可复核材料

源码与 AFLNet 归档、构建锁、镜像 ID、smoke 结果、预检统计、正式 `fuzzer_stats`、状态图、AFLNet 日志和命令参数均随交付包保存。`results/SHA256SUMS` 校验所有可读的结果文件；`source/SHA256SUMS` 校验两份源码归档。
