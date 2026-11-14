# Netopeer2 NETCONF 2.8.21 基准验收

核验日期：2026-11-10。被测版本为上游发布版 [Netopeer2 2.8.21](https://github.com/CESNET/netopeer2/releases/tag/2.8.21)，配套锁定 libyang 6.4.13、libnetconf2 4.6.4、sysrepo 5.2.27。各归档 SHA-256 与构建依赖记录见 `source-lock.json`；AFLNet 锁定 commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`。

## 正式轮次

- 有效运行时间：1,801 秒；AFLNet 退出码 0。
- `execs_done=1405`；`paths_total=62`，其中 `paths_found=59`；`cycles_done=0`；`stability=100.00%`；`unique_hangs=0`。
- AFLNet 的 `unique_crashes=26` 是 testcase 后 SSH 健康检查失败时，ELF monitor 为了将当前输入留给 AFLNet 而主动发出的 SIGSEGV。正式轮次中记录 28 次服务恢复（每次均恢复到 SSH banner 可用）。这些数字是健康告警，不直接等价于 26 个 Netopeer2 缺陷。
- 已将 26 个 crash 候选各独立复放 3 次，共 78 次；全部输入成功发送，0 次复放后 SSH 服务不可用，0 次连接失败，0 次恢复动作。因此本轮没有确认可复现的 Netopeer2 崩溃；26 个候选均保留为未复现健康告警。
- AFLNet `bitmap_cvg=0.00%` 是黑盒状态反馈 profile 的 bitmap 指标，不是 Netopeer2 源码覆盖率。`cycles_done=0` 表示首轮队列尚未遍历完成，需按探索性结果解读。

## 跑前、跑后与队列回放

跑前 smoke、跑后 smoke、候选复放后的最终 smoke 均通过：SSH NETCONF 1.0 server hello 和 subtree-filtered `ietf-netconf-monitoring` `<get>` RPC reply 正常。查询限制在监控模块，日志不保存原始回复体。

正式队列 62/62 均连接成功，收到 20,728 个 NETCONF 1.0 完整响应帧、20,676 个 RPC reply；0 reset、0 网络错误、0 空响应。52 次是每样本等待下一响应帧的有界超时；5,023 个 `rpc-error` 是畸形/变异请求返回的协议错误，不是回放器错误。1 个只见 server hello、没有 RPC reply 的样本是 hello-only 初始语料。逐样本统计见 `results/netconf-30m/queue-replay.json`。

## 适配与复用经验

Netopeer2 仅经 SSH `netconf` subsystem 提供服务，因此 fuzz profile 在隔离容器内用 TCP-to-SSH bridge 映射 AFLNet testcase 到新 SSH subsystem 会话，SSH 端口 830 不发布到宿主机，仅 loopback TCP 端口 1830 用于测试。NETCONF base:1.0 语料使用 `]]>]]>`；base:1.1 chunk framing 仅留在 parser 支持中，未在未验证协商的情况下混入 live seeds。

外部服务健康监控必须区别真实、可复现的协议缺陷与短暂不可用告警。对照本轮的 monitor crash 候选进行独立复放，并在整个队列回放后再次做应用层 smoke，才能给 crash 归因。经验规则统一维护在汇总包的 `基准化经验库.md`，不复制到各协议交付包。
