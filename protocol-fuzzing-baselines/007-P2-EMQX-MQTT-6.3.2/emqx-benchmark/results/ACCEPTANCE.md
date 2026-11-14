# EMQX 6.3.2 MQTT/TCP 基准验收

## 范围与来源

- 目标：EMQX 6.3.2，单节点，明文 MQTT/TCP 1883。
- 协议版本：MQTT 3.1.1 与 MQTT 5.0。TLS、WebSocket、集群、认证、持久化和桥接不在本轮范围内。
- 官方源码标记最终指向 commit `6e4ee3d080865d163e91f3e202c6c2d125523b3c`；源码归档 SHA-256：`9102f802386677433487b5d66515e74956ce1fcea8c1454fada6f23383df9143`。
- AFLNet commit：`0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`；构建输入、依赖和适配补丁哈希见 `results/build/build-lock.txt`。
- 正式运行使用镜像 ID `sha256:d2b0e9ab3390314571e4eb838e135cce5710e1b6b77cfaee7f9119db91025148`。最终验收镜像 ID：`sha256:605d30151932034823a0fdfdd9f613f242aee5045b3f42111602171400c5fad2`。

## 验收结果

- 最终镜像上 6 组 MQTT 3.1.1/5.0 发布订阅 smoke 全部通过；启动就绪通过真实 MQTT CONNECT/CONNACK 握手检查。
- 60 秒 AFLNet 黑盒状态反馈预检通过。状态节点为 `0, 2000, 109, 103, 111, 113`，包含 5 条边，摘要见 `results/preflight/state-summary.txt`。
- 正式运行起止时间相差 1,801 秒；时限包装器退出码 124，符合 1,800 秒运行预期。
- 正式轮统计：4,044 次执行、5 条路径、100.00% stability、0 unique crash、0 unique hang。原始数据见 `results/mqtt-30m/aflnet-out/fuzzer_stats` 和 `fuzzer-summary.txt`。

## 观测边界

EMQX 服务运行在 Erlang/BEAM 上，本轮 AFLNet 的 C 插桩和 forkserver 由生命周期辅助桩承载；AFL 位图、路径、crash/hang 计数反映该辅助桩及 harness 生命周期信号，不是 EMQX BEAM 源码覆盖率或缺陷计数。协议反馈状态来自真实 EMQX broker 的 MQTT 响应。因而本结果证明服务 smoke、协议响应状态反馈和 30 分钟 harness 运行通过，不据此宣称 EMQX 源码覆盖率或“没有缺陷”。
