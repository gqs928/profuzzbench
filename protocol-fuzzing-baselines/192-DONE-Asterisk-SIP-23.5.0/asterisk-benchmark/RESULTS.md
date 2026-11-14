# Asterisk SIP/TCP 严格验收报告

| 验收项 | 结果 | 证据摘要 |
|---|---|---|
| 1. 目标可重建 | 通过 | Asterisk/AFLNet/PJPROJECT 固定提交和 SHA-256、Ubuntu 基础镜像摘要、软件源快照、依赖包清单、无缓存构建日志、镜像 ID、构建时输入和最终交付输入 SHA-256 均已留存。 |
| 2. 协议行为保留 | 通过 | 参考版和 AFL/ASan 版各 10/10 次；相同 OPTIONS、REGISTER、INVITE/CANCEL 请求的最终状态码、10 次稳定 transcript 和端口复位检查已保存；transcript SHA-256=94dec5fe3345833b3683826e617b19c0940d06a286082c552a58177327a8be0c。 |
| 3. 种子真正进入业务状态 | 通过 | 固定语料 11 条；包含 REGISTER 成功、带 SDP 的 INVITE、匹配事务 CANCEL，以及消息正文/非法长度边界；正常回放实测 100/200/487 业务响应。 |
| 4. 状态反馈有效 | 通过 | AFLNet SIP 状态图包含 100 Trying、200 OK 等真实服务端响应节点；中文状态映射已保存；execs_done=797。 |
| 5. 覆盖率可信 | 通过 | 独立 gcov Asterisk 回放队列 29 条；PJSIP 核心文件已覆盖 5570 行、1933/22413 个分支，命中函数 431 个；TXT/HTML/CSV/函数清单齐全。 |
| 6. 每轮可复位 | 通过 | 参考版/AFL 版同一请求各 10 轮 transcript 一致并释放端口；正式运行 variable_paths=29 的 29 条样本各独立复播 10 次、响应序列稳定；30 分钟 stability=95.43%。 |
| 7. 异常可观察 | 通过 | 临时 SIP 故障探针 unique_crashes=1，异常样本独立回放记录存在且注入源码/服务已删除；真实目标 unique_hangs=0。 |
| 8. 结果可复查 | 通过 | 实际模糊测试 1800 秒；execs_done=797、paths_total=29、unique_crashes=0、unique_hangs=0；队列、状态图、参数、CSV、逐样本回放及 SHA-256 清单已留存。 |

详细命令日志、构建输入、种子、AFLNet 统计、状态图、逐样本回放和覆盖率报告均在本目录。
