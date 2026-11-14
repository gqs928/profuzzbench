# RADIUS 状态反馈映射

AFLNet 的 `RADIUS` 适配器按每个响应报文的 Code 字段产生状态编号。状态 `0` 表示本轮连接尚未收到完整响应；未知或异常响应归入 `255`。

| 状态编号 | RADIUS 响应 | 基准中的业务含义 |
|---:|---|---|
| `2` | Access-Accept | PAP 用户认证通过 |
| `3` | Access-Reject | 用户名或密码认证被拒绝 |
| `5` | Accounting-Response | 记账开始/停止请求已处理 |
| `11` | Access-Challenge | 服务端发起后续认证挑战 |
| `12` | Status-Server | 服务端状态查询 |
| `13` | Status-Client | 客户端状态响应 |
| `41` | Disconnect-ACK | 断开请求已确认 |
| `42` | Disconnect-NAK | 断开请求被拒绝 |
| `44` | CoA-ACK | 动态授权变更已确认 |
| `45` | CoA-NAK | 动态授权变更被拒绝 |
| `255` | 未识别响应 | 其他、畸形或未来扩展状态 |

请求切分直接读取 RADIUS 固定头部中的 16 位网络序 Length 字段；完整报文按边界切分。小于 20 字节的长度、超过当前缓冲区的声明长度和尾部截断数据会作为独立畸形请求保留，使变异内容仍能送达 FreeRADIUS。

图中的整数对应 RADIUS Code，而不是只按“收到了一个 `.dot` 文件”判定状态反馈有效。`protocol-smoke.py` 会先验证 Access-Accept、Access-Reject、Accounting-Response，再由 AFLNet 生成状态图。
