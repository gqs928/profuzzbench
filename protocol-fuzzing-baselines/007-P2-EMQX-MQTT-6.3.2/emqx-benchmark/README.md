# EMQX 6.3.2 MQTT/TCP 基准

本包基于 EMQX 官方 `6.3.2` 源码提交构建单节点 broker，并为 AFLNet 增加 MQTT 控制报文解析。测试范围是 MQTT 3.1.1 与 MQTT 5.0 的明文 TCP/1883，包括 CONNECT、SUBSCRIBE、PUBLISH、UNSUBSCRIBE、PINGREQ 和 DISCONNECT。

## 构建和验证

需要 Docker、约 10 GB 可用磁盘，以及可访问 GitHub/Hex 和 Ubuntu 软件源的构建网络。构建器固定为 EMQX 官方 OTP 28 / Elixir 1.19.1 镜像 digest；构建成功后会记录源码、AFLNet、工具链、release tarball 哈希和镜像 ID。

```sh
./build.sh
docker run --rm --network none \
  -v "$PWD/results:/work/results" \
  emqx-mqtt-aflnet:6.3.2 /work/validate.sh

docker run --rm --network none \
  -v "$PWD/results:/work/results" \
  emqx-mqtt-aflnet:6.3.2 /work/run.sh /work/results/mqtt-30m 1800s
./package.sh
```

镜像构建需要网络获取 EMQX 锁定的依赖；冒烟和模糊测试容器使用 `--network none`，broker 与 fuzzer 只通过容器回环地址通信。构建结果和测试证据保存在 `results/`。
`validate.sh` 运行六组 MQTT 3.1.1/5.0 协议冒烟和 60 秒状态反馈预检；正式记录单独使用 1,800 秒 campaign。两个入口都等到有效 CONNECT/CONNACK 往返后才继续，不能只以 TCP 端口已打开作为 broker 就绪信号。
预检还要求真实响应状态图包含初始态、成功 CONNACK、SUBACK、PUBLISH、UNSUBACK 和 PINGRESP，并至少有五条转换边。
最初一次只探测 TCP 端口的失败尝试保留在 `results/diagnostics/` 供排查；以握手就绪检查生成的 `results/preflight/` 才是正式预检证据。

## 模糊测试配置与测量范围

AFLNet 的 `-P MQTT` 适配器按 MQTT 固定报头和最多四字节 Remaining Length 切分请求，以服务端 MQTT 报文类型及 CONNACK 原因码生成状态反馈。畸形或截断的末尾报文会作为单个区域保留。`fuzzer/parser-test.c` 覆盖正常、多帧、截断和非法长度编码。

EMQX 使用 Erlang/BEAM，AFLNet 的 C 编译器插桩不会覆盖其 BEAM 业务代码。本基准启用 AFLNet forkserver 与 MQTT 响应状态反馈；为避免每个样本都重启昂贵的 Erlang 节点，EMQX 在一个 campaign 中持续运行，AFLNet 每个样本启动并回收一个最小 C 生命周期进程，再连接回环上的 EMQX。该 C 进程只提供 AFLNet 的目标生命周期和 forkserver，不能代表 EMQX 的业务边覆盖；`fuzzer_stats` 的目标进程崩溃数也不能解释为 EMQX 崩溃数。结果会单独记录 EMQX 生命周期和回放证据，不报告 EMQX 源码覆盖率。

配置仅启用明文 MQTT/TCP 监听器，关闭 TLS、WebSocket、QUIC 和 Dashboard 监听器；匿名本地会话、无外部网络、单节点、无桥接或外部集成。未覆盖集群、持久化消息队列、认证后端、TLS、WebSocket、QUIC 或吞吐性能。

共享的基准化经验库独立维护，不会包含在本协议 ZIP 中。
