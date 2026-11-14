# Redis RESP 状态模糊测试基准

本包以 Redis 8.10.3 和固定 AFLNet 版本，对 RESP2/RESP3 客户端 TCP 请求进行状态引导模糊测试。源码归档、依赖和构建环境锁定，并保存普通版、AFL/ASan 插桩版与 gcov 覆盖版证据。

AFLNet 适配器按 RESP 帧拆分数组、bulk string、嵌套聚合、RESP3 流式聚合/流式 bulk string，并保留 Redis 支持的 inline 请求。状态反馈区分 AUTH 错误、常见成功响应和 RESP 顶层类型，映射见 [redis-state-mapping.md](redis-state-mapping.md)。

## 严格验收结果

完整八项验收和证据分类见 [RESULTS.md](RESULTS.md)。正式 30 分钟运行有 4,589 次执行、206 条路径、85.06% AFLNet stability、0 自然 crash/hang；206 个队列输入完成三轮独立覆盖回放。临时 DEBUG 控制探针可复现 SIGSEGV；AFLNet 的一个变异候选未能独立复现，未列作缺陷。

## 重建与复验

在有 Docker 权限的 Linux 工作区运行：

```sh
chmod +x ./*.sh
./build.sh redis-resp-fuzz
./validate.sh redis-resp-fuzz "$PWD/results/preflight" 90s
```

正式 fuzz 命令：

```sh
docker run --rm --network none \\
  -v "$PWD:/workspace:ro" \\
  -v "$PWD/results:/results" \\
  redis-resp-fuzz bash /workspace/run.sh /results/redis-resp-30m 30m
```

Redis 只绑定容器 loopback；不要发布 6379 主机端口。覆盖回放为每条输入启动全新 Redis 和临时数据目录，每轮开始前清除 gcov 计数器。

## 覆盖范围

- RESP2/RESP3、明文 TCP/6379、HELLO 3。
- PING、SET/GET、INCR、HSET/HGETALL、MULTI/EXEC、CLIENT 与固定密码 AUTH 成功/失败流程。
- 请求帧边界、RESP3 类型、inline 请求、畸形长度、截断与状态反馈。
- 不覆盖 TLS、Redis Cluster 节点间协议、模块命令、持久化、广泛 ACL 策略或吞吐量测试。

Redis 官方资料：[RESP 规范](https://redis.io/docs/latest/develop/reference/protocol-spec/)、[redis/redis 上游仓库](https://github.com/redis/redis)。
