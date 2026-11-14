# FreeRADIUS RADIUS/TCP 严格验收报告

| 验收项 | 结果 | 证据摘要 |
|---|---|---|
| 1. 目标可重建 | 通过 | 无缓存 Docker 构建日志、基础镜像/依赖/提交记录和构建输入 SHA-256 已留存。 |
| 2. 协议行为保留 | 通过 | 参考版和 AFL 版各 10/10 轮；UDP/TCP 认证、拒绝、记账 transcript 一致；SHA-256=8e82e73bb787a4f94a26ce166307c58b3259515307a64d1312b4c9c91265bc01。 |
| 3. 种子真正进入业务状态 | 通过 | 固定语料 6 个，含 PAP 成功/拒绝、Accounting-Start/Stop 和多包会话；服务端返回预期业务响应。 |
| 4. 状态反馈有效 | 通过 | AFLNet IPSM 实测状态节点=0,2,3,5；要求包含 Accept(2)、Reject(3)、Accounting-Response(5)，并留存中文状态映射。 |
| 5. 覆盖率可信 | 通过 | 队列与异常样本回放后，radius.c/listen.c/process.c 共覆盖 1346 行；TXT/HTML/JSON/CSV 报表已留存。 |
| 6. 每轮可复位 | 通过 | 独立队列回放 44 条；每次回放新启服务进程并清空 detail 状态；10 次重复 transcript 稳定；variable_paths=34。 |
| 7. 异常可观察 | 通过 | 故障探针异常计数=1，崩溃样本已保存且临时注入源码/程序已删除；真实目标挂起数=0。 |
| 8. 结果可复查 | 通过 | 实际运行 1801 秒；execs_done=1624、paths_total=44、unique_crashes=0、unique_hangs=0；统计、参数、覆盖率和逐样本记录齐全。 |

构建版本、运行参数、输入哈希、fuzzer_stats、状态图、独立回放记录和覆盖率报告均在本目录。
