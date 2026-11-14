# Redis RESP 严格验收结果（8.10.3）

核验日期：2026-11-03（UTC）。正式自然 fuzz 时长 1,800 秒，结果为 **8 项验收全部通过**；自然 fuzz 未发现崩溃或挂起。受控 DEBUG 探针能复现测试注入的 SIGSEGV；AFLNet 另存的变异候选未能独立复现，因此不认定为 Redis 缺陷。

## 验收清单

| # | 验收项 | 结论 | 证据与结果 |
|---:|---|---|---|
| 1 | 目标可重建 | 通过 | Redis 8.10.3、AFLNet commit、Ubuntu digest 与 APT snapshot 固定；源码归档 SHA-256、依赖、构建日志和镜像 ID 见 `build-versions.txt` 与同级构建日志。 |
| 2 | 协议语义保留 | 通过 | RESP2/RESP3 reference 与 ASan 版各 10 个新服务器会话；AUTH、HELLO 3、PING、SET/GET、INCR、HSET/HGETALL 等 transcript 哈希一致。 |
| 3 | 种子进入业务状态 | 通过 | 种子包含认证成功/失败、RESP2/RESP3、事务、CLIENT 和截断 bulk；正式队列位于 `fuzz-30m/queue/`。 |
| 4 | 状态反馈有效 | 通过 | AFLNet 使用 `-P REDIS -E`；正式状态图 12 个节点、32 条边，时间序列 176 个采样点。 |
| 5 | 覆盖率可信 | 通过 | 206 个正式队列输入在三轮独立 gcov 回放中全部完成，服务端异常退出均为 0；每轮覆盖均为 9,114/77,070 行（11.8%）与 3,575/54,343 分支（6.6%），11 个核心命令处理函数 CSV 相同。 |
| 6 | 每轮可复位、可复查 | 通过 | 三轮 206/206 样本的响应状态/类型序列一致；`CLIENT ID/INFO` 输入的原始响应哈希有动态值差异，协议状态序列仍一致。AFL 位图 stability 另列为 85.06%，不替代业务回放对照。 |
| 7 | 异常可观察 | 通过 | 正式自然 fuzz 为 0 crash、0 hang。仅临时 DEBUG 配置下固定控制种子可独立触发 SIGSEGV（-11）；另一个 AFLNet 变异候选未能在 5 秒独立回放中复现，未记为确认缺陷。 |
| 8 | 结果可复查 | 通过 | 正式 fuzzer_stats、206 项队列、IPSM、plot_data、协议 smoke transcript、三轮逐样本回放、gcov 报告、故障探针及 SHA-256 清单随包保存。 |

## 正式 30 分钟 fuzz

- Redis 版本：8.10.3；正式记录时间戳间隔为 1,800 秒。
- 执行次数 4,589；总路径 206；`variable_paths=206`；最大深度 2。
- AFLNet stability 85.06%；bitmap coverage 13.06%；`cycles_done=0`。
- 唯一自然崩溃 0；唯一自然挂起 0；IPSM 12 节点、32 条边。

## 全队列回放与覆盖率

| 独立轮次 | 输入 | 输入后服务器异常退出 | 行覆盖 | 分支覆盖 |
|---:|---:|---:|---:|---:|
| 1 | 206/206 | 0 | 9,114 / 77,070 (11.8%) | 3,575 / 54,343 (6.6%) |
| 2 | 206/206 | 0 | 9,114 / 77,070 (11.8%) | 3,575 / 54,343 (6.6%) |
| 3 | 206/206 | 0 | 9,114 / 77,070 (11.8%) | 3,575 / 54,343 (6.6%) |

每轮队列状态均为已重放，无 replay error、无覆盖样本被跳过。18 个畸形或截断输入没有 RESP 响应，但服务器在 harness 的正常关闭流程中以 0 退出，按无响应样本记录，不算崩溃。`CLIENT ID/INFO` 产生一条原始字节哈希变化，协议状态与响应类型序列保持一致。

## 崩溃探针

Release 默认配置不启用 Redis DEBUG。临时探针配置仅在容器内开启该命令。固定 AUTH → DEBUG SEGFAULT 控制种子在独立 ASan Redis 上以 SIGSEGV（退出码 -11）复现，证明检测链路可用。AFLNet `-C` 的另一个变异输入未能在独立 5 秒期限内复现目标退出；该候选保留在证据中，但不当作 Redis 漏洞。完整分类见 `fault-probe/README.md` 与 `aflnet-candidate-replay.json`。

## 证据索引与范围

- 固定版本、归档和构建信息：`build-versions.txt`、`source-lock.json`、`build-logs/`
- RESP2/RESP3 smoke：`protocol-smoke/`
- 正式 fuzz：`fuzz-30m/`
- 三轮独立覆盖回放：`coverage-round1/`、`coverage-round2/`、`coverage-round3/`
- 受控探针：`fault-probe/`

本基准覆盖 RESP2/RESP3 客户端 TCP/6379 请求解析及固定认证状态下列出的 Redis 命令路径，不覆盖 TLS、Cluster 节点总线、模块命令、持久化、完整 ACL 策略或吞吐量。协议依据：[Redis RESP 规范](https://redis.io/docs/latest/develop/reference/protocol-spec/)；上游源码：[redis/redis](https://github.com/redis/redis)。
