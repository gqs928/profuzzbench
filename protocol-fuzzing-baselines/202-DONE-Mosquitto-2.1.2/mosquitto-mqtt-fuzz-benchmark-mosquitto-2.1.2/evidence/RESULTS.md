# Mosquitto 2.1.2 MQTT 基准结果

基准日期：2026-11-02  
对象：将原基准 Mosquitto 2.0.22（commit `766fa2c5a9bed6c65249cf555f430b982c417480`）升级为 Eclipse Mosquitto 2.1.2；测试 MQTT 3.1.1 / 5.0，明文 TCP/1883。  
AFLNet：2.56b，commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`。

## 源码和构建

使用 Eclipse Mosquitto [官方发布页](https://mosquitto.org/download/)当前列出的 `mosquitto-2.1.2.tar.gz`。源码 SHA-256：`fd905380691ac65ea5a93779e8214941829e3d6e038d5edff9eac5fd74cbed02`。基础镜像固定为 Ubuntu 20.04 digest，APT 包固定到 `20260928T000000Z` 快照。构建镜像：`sha256:a5249be51c286afd6020ee7de687fac371943bf3bda38c194589aa95460b6d46`。

已成功构建普通、AFL/ASan、gcov 三种 broker。2.1.2 的构建适配包含新增 `libcommon/`、cJSON 依赖、禁用本次范围之外的 HTTP API，以及将 gcov 数据从 `libcommon/`、`lib/`、`src/` 合并。详细可复现配置见根目录 `README.md`、`Dockerfile` 和 `build-logs/`。

为保持旧基准的限制，配置仍设 `message_size_limit 1048576`（PUBLISH payload 上限）；Mosquitto 默认 `max_packet_size` 另限制完整 MQTT 报文。日志会提示 `per_listener_settings` 已弃用，但该兼容配置在本次单监听器测试中可正常运行。二者的边界说明见官方[配置文档](https://mosquitto.org/man/mosquitto-conf-5.html)。

## 冒烟和短时反馈验收

- MQTT 解析器测试通过，覆盖 Remaining Length、截断尾部和服务端响应状态。
- MQTT 3.1.1 与 5.0 的 CONNECT、SUBSCRIBE、PUBLISH、UNSUBSCRIBE、PINGREQ、DISCONNECT 流程均通过。
- 普通 broker 与 AFL/ASan broker 每个协议版本分别运行 10 次新实例；客户端完整转录哈希一致。
- 60 秒 AFLNet 验收：153 次执行、6 条路径、97.00% 稳定性、4.32% bitmap 覆盖指标、0 crash、0 hang；MQTT 状态图包含多个状态和转换。

原始日志与逐次运行证据位于 `results/mqtt-validation-v212/`。

## 30 分钟 fuzz 与覆盖率

正式 AFLNet 运行 30 分钟：5,882 次执行、145 条路径、96.68% 稳定性、5.38% bitmap 覆盖指标、0 crash、2 个 hang 候选。每个 hang 样本分别在干净参考版和 AFL/ASan 版 Mosquitto 上复放。

| hang 样本 | 长度 | 参考版 | AFL/ASan 版 |
|---|---:|---|---|
| `id:000000,src:000000+000002,op:splice,rep:128` | 42 B | 无 MQTT 数据；broker 关闭连接，进程存活 | 无 MQTT 数据；broker 关闭连接，进程存活 |
| `id:000001,src:000000,op:havoc,rep:2` | 33 B | 无 MQTT 数据；broker 关闭连接，进程存活 | 无 MQTT 数据；broker 关闭连接，进程存活 |

这两条 AFLNet hang 记录都没有复现为 broker 进程挂死、崩溃或异常退出；应保留为无响应候选，不作为已确认缺陷。逐样本 JSON、broker 日志和原始输入位于 `results/mqtt-30m/hang-replay/` 与 `results/mqtt-30m/replayable-hangs/`。

完整队列 gcov 回放完成：145/145 个输入均成功回放，0 个超长跳过，broker 异常退出为 0。broker 范围汇总覆盖率为行 23.9%（3,876/16,229）、分支 14.1%（1,914/13,618）。覆盖率来源包括 `libcommon/`、`lib/` 和 `src/`；未链接进 broker 的 C++ wrapper 不计入目标范围。摘要见 `results/mqtt-coverage-final/coverage-summary.txt`，逐输入状态见 `results/mqtt-coverage-final/replay/replay.json`，组件 JSON 与 HTML 详情报告也保存在该目录。

## 运行范围

测试仅覆盖明文 MQTT/TCP broker 路径。容器使用 `--network none`，broker 只监听容器 loopback，没有向宿主机发布端口。本基准不覆盖 TLS、WebSockets、bridge、插件、身份验证或吞吐量。
