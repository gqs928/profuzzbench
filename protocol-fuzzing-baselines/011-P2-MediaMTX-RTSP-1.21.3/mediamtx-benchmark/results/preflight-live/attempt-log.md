# MediaMTX 预检尝试记录

保留每次尝试及其失败证据，不把构建/验收器问题归咎于 MediaMTX：

- `aflnet-60s-final3`：AFLNet timer 和 RTSP 状态图已生成，但把模糊写入后的同一个服务实例直接用于发布冒烟，publisher `SETUP` 返回 400；服务提前强杀，未留下 Go counter。
- `aflnet-60s-final4`：campaign 与 post-smoke 分开启动，两个 Go 服务都以 SIGTERM 正常退出并各自写出 `covcounters.*`；冒烟仍因 RTSP publisher `SETUP` 缺少 `mode=record` 返回 400。
- `aflnet-60s-final5`：补上 `mode=record` 后 OPTIONS、ANNOUNCE、发布 SETUP/RECORD、读取 DESCRIBE/SETUP/PLAY/TEARDOWN 全部为 200；coverage 合并已得到输入，但登录 shell 清空了 `PATH` 中的 Go 目录。
- `aflnet-60s-final6`：Go 命令改用绝对路径；非 root 容器用户没有默认 `/.cache/go-build` 写权限。
- `aflnet-60s-final7`：Go cache 改到结果目录并成功合并 counters；`go tool cover` 需要从 MediaMTX 模块目录解析源文件。
- `aflnet-60s-final8`：Go 汇总成功（总语句覆盖 11.5%），冒烟和两组优雅退出均通过；旧验收器误要求响应图必须含 200，而本轮有效响应图记录了 `400` 和 `404` 状态迁移。
- `aflnet-60s-final9`：验收器改为检查合法 RTSP 状态节点及迁移边；短时 campaign、独立发布/读取冒烟、两组 Go counters 和覆盖率汇总全部通过。此目录为最终短时预检证据。
