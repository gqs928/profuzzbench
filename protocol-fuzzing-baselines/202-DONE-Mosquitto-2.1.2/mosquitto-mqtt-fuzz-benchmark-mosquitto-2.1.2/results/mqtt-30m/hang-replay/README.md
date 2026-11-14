# AFLNet hang 样本复核

30 分钟正式运行记录了两个 AFLNet hang 候选。每条原始输入分别在干净参考版和 AFL/ASan broker 上回放；四次复测均无 MQTT 响应、客户端收到对端关闭，broker 进程仍存活，正常发出 SIGTERM 后退出码为 0。当前没有复现 broker 崩溃或进程 hang。

| 样本 | 输入长度 | 参考版 | AFL/ASan 版 |
|---|---:|---|---|
| `id:000000,src:000000+000002,op:splice,rep:128` | 42 B | 连接关闭、进程存活 | 连接关闭、进程存活 |
| `id:000001,src:000000,op:havoc,rep:2` | 33 B | 连接关闭、进程存活 | 连接关闭、进程存活 |

对应 JSON 结果为 `reference-final-*.json`、`afl-final-*.json`；`*-broker.log` 保存 broker 日志。`triage-summary.json` 汇总了输入 SHA-256 和所有复测数据。
