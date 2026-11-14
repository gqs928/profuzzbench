# Asterisk PJSIP/TCP 状态映射

目标是 Asterisk 上游 PJSIP 通道的 SIP/TCP 服务端路径，监听容器内的 `127.0.0.1:5060`。AFLNet 按 SIP 消息的头部结束符与 `Content-Length` 切分输入流；SIP 响应首行中的三位状态码作为状态图节点。状态切分只用于模糊器反馈，Asterisk 仍负责解析完整请求、认证/注册、对话事务、SDP 和拨号计划。

| 状态码 | SIP 含义 | 基准中触发方式 |
|---:|---|---|
| `0` | 初始/无法识别状态 | AFLNet 的起始状态 |
| `100` | Trying | INVITE 已进入 PJSIP 事务及拨号计划 |
| `180` | Ringing | 被叫进入振铃路径时可能出现 |
| `200` | OK | OPTIONS 能力查询、REGISTER 注册或 CANCEL 确认 |
| `400` | Bad Request | SIP 起始行、头字段或长度错误 |
| `401` / `403` | Unauthorized / Forbidden | 身份认证或访问控制拒绝 |
| `404` / `405` | Not Found / Method Not Allowed | 扩展或方法路由拒绝 |
| `408` | Request Timeout | 事务超时 |
| `415` / `488` | Unsupported Media Type / Not Acceptable Here | SDP 或媒体协商失败 |
| `481` | Call/Transaction Does Not Exist | 无匹配对话的 ACK、BYE 等请求 |
| `487` | Request Terminated | INVITE 被 CANCEL 后终止 |
| `489` | Bad Event | 不支持的订阅事件 |
| `500` / `503` | Server Error / Service Unavailable | 服务端错误或暂时不可用 |

种子中的 `REGISTER` 使用固定本地测试端点；`INVITE` 携带有效 SDP，并与 `CANCEL` 共用 Via branch、Call-ID 和 CSeq 序号。拨号计划在 5 秒后应答，为 CANCEL 留出业务处理窗口。测试客户端记录每轮的请求方法、响应状态码、响应头、Asterisk 日志和进程退出状态。

完整覆盖率报告由独立 gcov 构建的队列样本回放产生。需要核对的核心源文件包括 `res/res_pjsip/pjsip_distributor.c`、`res/res_pjsip_registrar.c`、`res/res_pjsip_session.c`、`res/res_pjsip.c` 和 `channels/chan_pjsip.c`；报告同时列出这些文件及实际命中的函数，而不是仅统计任意生成的 `.gcda` 文件。
