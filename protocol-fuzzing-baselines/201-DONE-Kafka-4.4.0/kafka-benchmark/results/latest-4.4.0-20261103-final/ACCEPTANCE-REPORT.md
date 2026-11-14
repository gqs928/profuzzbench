# Apache Kafka 二进制协议模糊测试严格验收报告

| 验收项 | 结果 | 证据摘要 |
|---|---|---|
| 1. 目标可重建 | 通过 | 固定提交与 Apache 官方二进制/源码 SHA-512、构建输入哈希、资源配置和镜像 ID 均已留存。 |
| 2. 协议行为保留 | 通过 | 无代理参考版 10 轮、插桩代理版 10 轮；ApiVersions→Metadata→Produce→Fetch 状态一致，Kafka 官方 CLI producer/consumer 均完成写读。 |
| 3. 种子真正进入业务状态 | 通过 | 可复现语料 10 个，覆盖协商、元数据、写入、读取、偏移查询、协调器及畸形帧；协议烟测确认成功请求到达 Broker。 |
| 4. 状态反馈有效 | 通过 | AFLNet IPSM 状态节点=0,1,2,3,4,5,6；包含 ApiVersions、Metadata、Produce、Fetch 四个真实响应阶段。 |
| 5. 覆盖率可信 | 通过 | KafkaApis 请求处理类行覆盖 300，分支覆盖 95；已覆盖函数：kafka.server.KafkaApis#handle：21/89 行, kafka.server.KafkaApis#handleProduceRequest：24/30 行, kafka.server.KafkaApis#handleFetchRequest：41/53 行, kafka.server.KafkaApis#handleListOffsetRequest：13/14 行, kafka.server.KafkaApis#handleTopicMetadataRequest：36/52 行, kafka.server.KafkaApis#handleFindCoordinatorRequest：3/4 行, kafka.server.KafkaApis#handleFindCoordinatorRequestLessThanV4：4/5 行, kafka.server.KafkaApis#handleApiVersionsRequest：1/1 行；JaCoCo TXT/HTML/XML/CSV 已保存。 |
| 6. 每轮可复位 | 通过 | 逐条回放队列 10 个输入；每次重启真实 Broker 并从同一 KRaft 存储快照恢复；10 轮业务 transcript 稳定；AFLNet 覆盖稳定度=100.00%（门槛 90%）。 |
| 7. 异常可观察 | 通过 | 隔离故障探针记录异常 1 次，样本独立复现 SIGABRT；Kafka 源码未注入故障，真实 Broker 挂起=0。 |
| 8. 结果可复查 | 通过 | 真实运行 1800 秒；execs_done=156、paths_total=10、variable_paths=0、unique_crashes=0、unique_hangs=0；CPU 配额=1 核；内存上限=1g；统计、参数、逐样本回放和覆盖报告齐全。 |

构建输入、版本、fuzzer_stats、状态图、种子、逐样本重放、JaCoCo 覆盖率和异常样本均留在此目录。
