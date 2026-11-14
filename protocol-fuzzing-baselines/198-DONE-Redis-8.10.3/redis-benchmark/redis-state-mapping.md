# AFLNet Redis RESP state mapping

`extract_response_codes_redis()` emits one state for each complete top-level
server response frame. The first state, `0`, is AFLNet's initial state. The
remaining states classify stable response semantics first, then fall back to
the RESP top-level type.

| State | Server response |
|---:|---|
| 200 | Simple string `+OK` |
| 201 | Simple string `+PONG` |
| 202 | Simple string `+QUEUED` |
| 203 | Any other simple string (`+`) |
| 210 | Integer (`:`) |
| 220 | Bulk string (`$`) |
| 230 | Array (`*`) |
| 231 | Map (`%`) |
| 232 | Set (`~`) |
| 233 | Attribute (`|`) |
| 234 | Push (`>`) |
| 235 | Blob error (`!`) |
| 236 | Verbatim string (`=`) |
| 237 | Null (`_`) |
| 238 | Boolean (`#`) |
| 239 | Double (`,`) |
| 240 | Big number (`(`) |
| 300 | Error code `NOAUTH` |
| 301 | Error code `WRONGPASS` |
| 302 | Error code `NOPERM` |
| 303 | Any other simple error (`-`) |
| 299 | Unrecognized fallback |

The state graph uses these numeric IDs. The checked protocol transcripts let a
reviewer associate successive responses with their requests. For example,
`AUTH default ...` yields 200, `PING` yields 201, `GET` yields 220, RESP2
`HGETALL` yields 230, and RESP3 `HGETALL`/`HELLO 3` yields 231. In a transaction,
`MULTI` yields 200, queued commands yield 202, and `EXEC` yields 230.

The mapping is intentionally stable across payload values. It distinguishes
authentication failures, common command outcomes, and RESP2/RESP3 aggregate
families without treating volatile payload bytes as separate states.
