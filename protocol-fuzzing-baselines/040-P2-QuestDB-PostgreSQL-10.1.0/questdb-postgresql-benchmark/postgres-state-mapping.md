# PostgreSQL 前后端协议状态映射

POSTGRES 适配器按后端消息边界解析 TCP 响应，不将响应文件本身当作状态。每种消息映射为固定整数；ReadyForQuery 另按事务状态区分。

| 状态 ID | 协议含义 | 典型触发 |
|---:|---|---|
| 0 | 会话初始状态 | 每条状态序列的起点 |
| 1 | 认证成功 | AuthenticationOk |
| 2 | 认证挑战 | 明文、MD5、SASL 等 AuthenticationRequest |
| 10 | 空闲就绪 | ReadyForQuery(I) |
| 11 | 事务中就绪 | ReadyForQuery(T) |
| 12 | 事务失败就绪 | ReadyForQuery(E) |
| 20 | 命令完成 | CommandComplete 或 EmptyQueryResponse |
| 21 | 行描述 | RowDescription |
| 22 | 数据行 | DataRow |
| 23 | 扩展查询阶段完成 | Parse/Bind/CloseComplete、NoData、PortalSuspended |
| 30 | COPY 流程 | CopyIn/CopyOut/CopyBoth、CopyData/CopyDone/CopyFail |
| 40 | 认证/授权错误 | ErrorResponse SQLSTATE 类别 28 |
| 41 | SQL/协议错误 | 其他 ErrorResponse |
| 50 | Notice 或通知 | NoticeResponse、NotificationResponse |
| 51 | 参数状态 | ParameterStatus |
| 52 | 后端取消密钥 | BackendKeyData |
| 53 | 协议版本协商 | NegotiateProtocolVersion |
| 54 | SSL/GSS 协商拒绝 | 单字节 N |
| 99 | 其他或不可解析响应 | 未列出的完整消息 |

请求解析遵循 PostgreSQL 帧格式：Startup、SSL、GSS 和 Cancel 请求以 32 位长度开头；常规消息以 1 字节类型和 32 位长度开头。畸形或截断的消息尾部会作为一个区域保留，避免丢弃 AFLNet 输入。

SSL/GSS 加密通道、复制协议、取消请求的独立第二连接、OAuth/SCRAM 凭证生成以及协议外层代理不在本基准范围内。语料覆盖 SSLRequest 明文拒绝后继续启动、Trust 登录、登录/数据库拒绝、简单查询、扩展查询、事务恢复和 COPY FROM STDIN。
