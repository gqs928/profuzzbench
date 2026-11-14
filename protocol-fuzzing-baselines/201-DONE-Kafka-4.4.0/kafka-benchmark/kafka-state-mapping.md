# Kafka 状态映射

## 报文边界

Kafka TCP 请求和响应都以 4 字节大端长度开头。长度值不包含自身的 4 字节前缀。适配器按前缀拆分完整帧；长度小于请求头最小值、超出剩余输入、截断或溢出的尾部会作为单独可变区域保留，确保畸形数据仍能发往真实 Broker。

## 响应状态

Kafka 响应头包含 correlation id。种子把 id 1–6 分配给 ApiVersions、Metadata、Produce、Fetch、ListOffsets 和 FindCoordinator 请求，服务端按协议原样回传。AFLNet 解析器据此映射响应阶段；未知 id 映射为 99，初始状态为 0。此设计不把 Kafka 错误码误当作通用响应字段，因为 Kafka 每种 API 的响应体结构不同。

| 状态 | 含义 |
| --- | --- |
| 0 | 初始状态 |
| 1 | ApiVersions 响应 |
| 2 | Metadata 响应 |
| 3 | Produce 响应 |
| 4 | Fetch 响应 |
| 5 | ListOffsets 响应 |
| 6 | FindCoordinator 响应 |
| 99 | 未识别、被变异的 correlation id |

## 会话语料

有效种子包含能力协商、主题元数据查询、消息写入和读取、偏移量查询及消费者协调器查询；另含不支持的 API 版本、未知 API key 和截断帧。Broker 预置固定单分区主题 `fuzz-topic`。状态映射依赖 correlation id 约定，因此变异 id 会进入未知状态；报文本身仍按 Kafka 请求头解析。

该状态图用于指导状态感知变异，不代表 API 响应的成功/失败结果码。实际业务结果由正常客户端回放记录验证，JaCoCo 报告则统计 Broker 内部请求解析与处理代码。
