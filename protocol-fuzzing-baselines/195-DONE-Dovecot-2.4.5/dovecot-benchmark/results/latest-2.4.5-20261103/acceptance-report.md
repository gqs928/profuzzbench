# Dovecot IMAP 模糊测试验收报告

- 生成时间：2026-11-03 09:54:45 UTC
- 上游提交：`0cbb641e3e88d1616c2e8c1ff109c67c0985ddc6`
- AFLNet 提交：`0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`
- 总结：**全部通过**

## 验收项

| 验收项 | 结果 | 证据摘要 |
| --- | --- | --- |
| 目标可重建 | 通过 | 固定 Dovecot/AFLNet 源码、基础镜像、APT 快照、补丁重应用和完整构建日志 |
| 协议行为保留 | 通过 | 参考版和 AFL 版正常客户端流程各 10 次；成功 20/20 |
| 种子真实进入业务状态 | 通过 | 登录、邮箱操作与 APPEND 字面量均按步骤回放 |
| 状态反馈有效 | 通过 | 运行 1800 秒，执行 1609 次，状态图 17 个节点/48 条边 |
| 覆盖率可信 | 通过 | IMAP 行覆盖 2340/22265 (10.51%)；分支 908/8761 (10.36%)；核心函数 105/225；独立回放 32 条（完整应答 10，部分结束 22，标签等待超时 5，服务端非零退出 0） |
| 每轮可复位 | 通过 | login-mailbox 同一种子重复 10 次；状态签名数 1；稳定=true |
| 异常可观察 | 通过 | 临时故障注入探针运行 1800 秒、执行 2111 次；注入目标标记=1；登录 worker chroot=/；AFLNet 记录 2 个崩溃和 2 个可回放样本；源码补丁已撤回=true |
| 结果可复查 | 通过 | 队列、fuzzer_stats、IPSM 状态图、运行参数和回放/覆盖率 CSV 均保留 |

## 模糊运行

- 请求时长：`30m`；实测：1800 秒。
- 运行统计：执行 1609 次，队列 32，变化路径 32，稳定性 88.62%。
- 异常统计：崩溃 0，挂起 0。原始 `fuzzer_stats` 与日志在 `fuzz-30m/`。

## 已覆盖核心处理函数

- `cmd-append.c:cmd_append`（函数内行执行率 100.0%）
- `cmd-append.c:cmd_append_args_can_stop`（函数内行执行率 33.33%）
- `cmd-append.c:cmd_append_continue_message`（函数内行执行率 58.33%）
- `cmd-append.c:cmd_append_finish`（函数内行执行率 77.78%）
- `cmd-append.c:cmd_append_finish_parsing`（函数内行执行率 57.69%）
- `cmd-append.c:cmd_append_full`（函数内行执行率 57.41%）
- `cmd-append.c:cmd_append_handle_args`（函数内行执行率 45.45%）
- `cmd-append.c:cmd_append_parse_new_msg`（函数内行执行率 50.0%）
- `cmd-append.c:malloc_multiply_check`（函数内行执行率 60.0%）
- `cmd-append.c:p_malloc`（函数内行执行率 75.0%）
- `cmd-append.c:pool_unref`（函数内行执行率 100.0%）
- `cmd-append.c:str_append`（函数内行执行率 100.0%）
- `cmd-append.c:str_append_c`（函数内行执行率 100.0%）
- `cmd-fetch.c:cmd_fetch`（函数内行执行率 56.76%）
- `cmd-fetch.c:cmd_fetch_finish`（函数内行执行率 25.0%）
- `cmd-fetch.c:cmd_fetch_set_reason_codes`（函数内行执行率 35.71%）
- `cmd-fetch.c:fetch_parse_args`（函数内行执行率 33.33%）
- `cmd-fetch.c:imap_fetch_cmd_init_handler`（函数内行执行率 75.0%）
- `cmd-search.c:cmd_search`（函数内行执行率 50.0%）
- `cmd-search.c:malloc_multiply_check`（函数内行执行率 60.0%）
- `cmd-search.c:p_malloc`（函数内行执行率 75.0%）
- `cmd-select.c:array_is_created_i`（函数内行执行率 100.0%）
- `cmd-select.c:close_selected_mailbox`（函数内行执行率 60.0%）
- `cmd-select.c:cmd_select`（函数内行执行率 100.0%）
- `cmd-select.c:cmd_select_finish`（函数内行执行率 72.73%）
- `cmd-select.c:cmd_select_full`（函数内行执行率 54.84%）
- `cmd-select.c:malloc_multiply_check`（函数内行执行率 60.0%）
- `cmd-select.c:p_malloc`（函数内行执行率 75.0%）
- `cmd-select.c:select_context_free`（函数内行执行率 62.5%）
- `cmd-select.c:select_open`（函数内行执行率 67.24%）
- `imap-client.c:array_count_i`（函数内行执行率 100.0%）
- `imap-client.c:array_create_from_buffer_i`（函数内行执行率 100.0%）
- `imap-client.c:array_create_i`（函数内行执行率 100.0%）
- `imap-client.c:array_get_i`（函数内行执行率 100.0%）
- `imap-client.c:array_is_created_i`（函数内行执行率 100.0%）
- `imap-client.c:client_add_missing_io`（函数内行执行率 100.0%）
- `imap-client.c:client_args_finished`（函数内行执行率 100.0%）
- `imap-client.c:client_check_command_hangs`（函数内行执行率 21.43%）
- `imap-client.c:client_cmd_append_timing_stats`（函数内行执行率 93.75%）
- `imap-client.c:client_command_alloc`（函数内行执行率 100.0%）
- `imap-client.c:client_command_failed_early`（函数内行执行率 100.0%）
- `imap-client.c:client_command_find_with_flags`（函数内行执行率 71.43%）
- `imap-client.c:client_command_free`（函数内行执行率 90.16%）
- `imap-client.c:client_command_init_finished`（函数内行执行率 100.0%）
- `imap-client.c:client_command_input`（函数内行执行率 81.25%）
- `imap-client.c:client_command_is_ambiguous`（函数内行执行率 60.0%）
- `imap-client.c:client_command_new`（函数内行执行率 90.91%）
- `imap-client.c:client_continue_pending_input`（函数内行执行率 52.63%）
- `imap-client.c:client_create`（函数内行执行率 84.42%）
- `imap-client.c:client_create_finish`（函数内行执行率 66.67%）
- `imap-client.c:client_create_finish_io`（函数内行执行率 30.77%）
- `imap-client.c:client_default_destroy`（函数内行执行率 85.48%）
- `imap-client.c:client_default_init`（函数内行执行率 100.0%）
- `imap-client.c:client_default_send_tagline`（函数内行执行率 70.0%）
- `imap-client.c:client_default_sync_notify_more`（函数内行执行率 100.0%）
- `imap-client.c:client_destroy`（函数内行执行率 100.0%）
- `imap-client.c:client_disconnect`（函数内行执行率 90.91%）
- `imap-client.c:client_enabled_mailbox_features`（函数内行执行率 62.5%）
- `imap-client.c:client_get_commands_status`（函数内行执行率 11.11%）
- `imap-client.c:client_get_last_command_status`（函数内行执行率 62.5%）
- `imap-client.c:client_handle_input`（函数内行执行率 86.36%）
- `imap-client.c:client_handle_next_command`（函数内行执行率 54.55%）
- `imap-client.c:client_handle_unfinished_cmd`（函数内行执行率 50.0%）
- `imap-client.c:client_has_enabled`（函数内行执行率 60.0%）
- `imap-client.c:client_input`（函数内行执行率 69.57%）
- `imap-client.c:client_log_disconnect`（函数内行执行率 100.0%）
- `imap-client.c:client_read_args`（函数内行执行率 57.14%）
- `imap-client.c:client_read_string_args`（函数内行执行率 68.75%）
- `imap-client.c:client_remove_pending_unambiguity`（函数内行执行率 25.0%）
- `imap-client.c:client_search_updates_free`（函数内行执行率 50.0%）
- `imap-client.c:client_send_command_error`（函数内行执行率 58.33%）
- `imap-client.c:client_send_line`（函数内行执行率 100.0%）
- `imap-client.c:client_send_line_next`（函数内行执行率 76.92%）
- `imap-client.c:client_send_tagline`（函数内行执行率 100.0%）
- `imap-client.c:client_skip_line`（函数内行执行率 100.0%）
- `imap-client.c:client_stats`（函数内行执行率 96.3%）
- `imap-client.c:client_tagline_throttled_msecs`（函数内行执行率 66.67%）
- `imap-client.c:clients_destroy_all`（函数内行执行率 80.0%）
- `imap-client.c:clients_init`（函数内行执行率 100.0%）
- `imap-client.c:imap_unset_capability`（函数内行执行率 100.0%）
- `imap-client.c:malloc_multiply_check`（函数内行执行率 80.0%）
- `imap-client.c:p_clear`（函数内行执行率 100.0%）
- `imap-client.c:p_free_internal`（函数内行执行率 100.0%）
- `imap-client.c:p_malloc`（函数内行执行率 75.0%）
- `imap-client.c:pool_unref`（函数内行执行率 100.0%）
- `imap-client.c:str_append`（函数内行执行率 100.0%）
- `imap-client.c:str_append_c`（函数内行执行率 100.0%）
- `imap-client.c:str_data`（函数内行执行率 100.0%）
- `imap-client.c:str_len`（函数内行执行率 100.0%）
- `imap-client.c:str_truncate`（函数内行执行率 100.0%）
- `imap-client.c:timeval_diff_msecs`（函数内行执行率 100.0%）
- `imap-commands.c:array_append_i`（函数内行执行率 100.0%）
- `imap-commands.c:array_create_from_buffer_i`（函数内行执行率 100.0%）
- `imap-commands.c:array_create_i`（函数内行执行率 100.0%）
- `imap-commands.c:array_free_i`（函数内行执行率 100.0%）
- `imap-commands.c:command_bsearch`（函数内行执行率 100.0%）
- `imap-commands.c:command_cmp`（函数内行执行率 100.0%）
- `imap-commands.c:command_exec`（函数内行执行率 82.35%）
- `imap-commands.c:command_find`（函数内行执行率 100.0%）
- `imap-commands.c:command_register_array`（函数内行执行率 100.0%）
- `imap-commands.c:command_stats_flush`（函数内行执行率 100.0%）
- `imap-commands.c:command_stats_start`（函数内行执行率 100.0%）
- `imap-commands.c:commands_deinit`（函数内行执行率 100.0%）
- `imap-commands.c:commands_init`（函数内行执行率 100.0%）
- `imap-commands.c:malloc_multiply_check`（函数内行执行率 80.0%）

## 交付证据

- `build-logs/`：从头构建日志、工具链版本、软件包清单、镜像摘要及输入 SHA-256。
- `protocol-smoke/` 与 `seed-replay/`：正常客户端逐命令记录和同种子稳定性数据。
- `fuzz-30m/`：AFLNet 统计、状态图、运行参数、队列、异常样本和日志。
- `coverage/`：gcovr 原始 JSON、总行/分支 CSV、逐输入回放记录、核心函数摘要和函数覆盖明细。
- `fault-probe/`：临时 Dovecot 故障注入补丁、源码撤回校验、1800 秒探针运行日志和 AFLNet 统计；崩溃样本 2 个。
- `SHA256SUMS`：结果目录中的所有证据文件哈希。
