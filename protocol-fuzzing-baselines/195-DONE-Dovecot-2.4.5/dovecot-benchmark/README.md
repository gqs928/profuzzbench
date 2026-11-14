# Dovecot IMAP 状态化模糊测试基准

此交付包把 Dovecot 的明文 IMAP 服务变成一个可重建、可复位、可回放并能核对覆盖率的 AFLNet 目标。业务范围覆盖欢迎响应、认证前命令、失败及成功认证、邮箱选择、列表/状态查询、搜索、取信、APPEND 字面量、标志修改、EXPUNGE 和退出。

## 固定版本与构建

- Dovecot：上游 `dovecot/core` 稳定发行标签 `2.4.5`，提交 `0cbb641e3e88d1616c2e8c1ff109c67c0985ddc6`。
- AFLNet：ProFuzzBench AFLNet 提交 `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`。
- Unicode：Dovecot 构建使用的 UCD `18.0.0` 文件按 `ucd-checksums.sha256` 校验；提交短号版本头由锁定提交号生成。
- 基础镜像：Ubuntu 20.04 固定摘要；构建软件包来自 `20260928T000000Z` 固定快照。
- `source-lock.json`、源码归档哈希、Unicode 数据哈希、AFLNet IMAP 补丁、编译器版本和构建参数共同锁定输入。Dockerfile 从归档重建三套 Dovecot：普通参考版、AFL 覆盖插桩版、gcov 覆盖率版。

普通协议回放由容器内 `ubuntu` 用户执行；sudoers 白名单只允许固定启动器按固定变体启动、停止服务或清理固定测试状态目录。AFLNet 短时切换到容器 root 身份，直接执行 AFL 插桩版 Dovecot，避免权限代理隔断 forkserver；IMAP、认证和内部服务仍按配置降到 `ubuntu` 用户。启动前清理旧运行套接字，并以 `ubuntu` 身份重建邮箱；AFLNet 的服务初始化等待为 500 毫秒。模糊运行目录在结束时开放读取权限，便于宿主验收结果。运行时启动器与 sudoers 覆盖层在服务编译后单独构建，避免管理入口变更触发三套源码重新编译。AFL 目标启用 AFLNet LLVM 覆盖插桩；未启用 ASan，因为当前宿主机内核上的固定 Clang 10 ASan 运行时无法启动 Dovecot 子进程。模糊器仍会记录目标的崩溃信号和超时；独立故障探针核验崩溃样本留存。

只有 AFLNet 适配层需要补丁：它注册 IMAP 命令解析和响应状态提取。Dovecot 协议处理源码保持原样。补丁在镜像构建时先执行 `git apply --check`，然后重新应用，再编译并运行解析器自检。

## 快速构建

在有 Docker 和网络访问的 Linux 主机上：

```sh
./build.sh dovecot-imap-fuzz
```

`build.sh` 默认执行 `docker build --pull --no-cache`，核对源码哈希并保存 Docker 构建日志、依赖包清单、版本信息、镜像摘要和构建输入哈希。构建使用固定源码和 APT 快照，不依赖浮动的上游分支。

## 严格验收

一次命令按图片中的验收要求完成重建、正常协议流程、重复回放、30 分钟运行、独立覆盖率回放和异常记录探针。异常探针默认运行 30 分钟，也可用 `DOVECOT_FAULT_PROBE_DURATION` 覆盖：

```sh
./full-acceptance.sh dovecot-imap-fuzz "$PWD/results/dovecot-acceptance" 30m
```

运行步骤：

1. 从固定依赖和源码归档无缓存重建镜像；运行 IMAP 边界解析器自检并校验种子清单。
2. 普通版和 AFL 插桩版各执行 10 次完整正常客户端流程，并验证错误密码返回 `NO`。测试流程包含登录、邮箱列表、选择、状态、搜索、取信、APPEND、标志更新、EXPUNGE 和退出。
3. 在干净邮箱上把同一 `login-mailbox.imap` 种子回放 10 次，比较忽略动态标签和计数后的响应状态序列。
4. 用 AFLNet 状态反馈模式持续运行 30 分钟，记录运行参数、执行数、状态图、崩溃数、挂起数、队列和完整日志。
5. 将队列逐个送入独立 gcov 构建，导出 IMAP 登录/命令解析目录的行、分支覆盖率和已命中的核心函数，并保留每个输入的回放状态。
6. 在临时 AFL 插桩版 Dovecot 的 `LOGIN` 处理路径加入可控异常。探针使用有效短账号和正常 `LOGIN` 种子，仅在用户名或密码字段变异时触发，检查 AFLNet 是否记录异常和可回放样本；随后撤回源码补丁，并在容器销毁时丢弃测试二进制。只有 Dovecot 进程异常确实由 AFLNet 记录并保存样本时，此项才通过；正常参考版和正式 AFL 版均不含故障注入。

验收证据放在结果目录中：`build-logs/`、`protocol-smoke/`、`seed-replay/`、`fuzz-30m/`、`coverage/coverage-summary.csv`、`coverage/coverage-functions.csv`、`coverage/key-function-coverage.csv`、`fault-probe/`、`acceptance-report.md` 以及 `SHA256SUMS`。gcov 独立回放会逐条记录状态；畸形变异输入可能让服务端正常断开或无法产生标签应答，这类记录标为“部分结束”，不会算作完整应答。`acceptance_report.py` 会逐项给出通过/失败与实际数据；覆盖率和异常统计不会只以一个 `.dot` 文件代替。

## 单独运行

```sh
./build.sh dovecot-imap-fuzz
docker run --rm --network none \
  --user root \
  -v "$PWD:/workspace:ro" -v "$PWD/results:/results" \
  dovecot-imap-fuzz bash /workspace/run.sh /results/imap-30m 30m
```

服务器只监听容器内部回环地址 `127.0.0.1:1143`；容器使用 `--network none`，不向主机发布端口。测试账户 `fuzzuser`、固定 Maildir 和所有运行状态都仅供本地回放。AFLNet 每轮清理脚本重建邮件内容；每次独立会话都会由启动脚本重新初始化运行目录。

## 文件说明

- `imap_aflnet.c`：处理命令标签、CRLF、引号和 IMAP 字面量边界；对响应状态丢弃动态字段。
- `seeds/`、`prepare_seeds.py`、`seeds-manifest.json`：确定性会话语料及哈希清单。语料先认证，再进入邮箱业务状态。
- `dovecot.conf`、`passwd`、`prepare_maildir.py`、`clean.sh`：隔离测试配置、账户和确定性邮件复位。
- `state-mapping.md`：状态编号与 IMAP 协议阶段的对应关系。
- `coverage-run.sh`、`coverage_run.py`：独立 gcov 队列回放与报告。
- `dovecot-fault-injection.patch`、`dovecot-fault.dict`、`fault-kill-helper.c`、`fault-probe.sh`：只用于临时故障验证；探针服务将登录 worker chroot 到 `/`，使临时助手可从真实 LOGIN 路径运行；脚本会记录配置哈希、补丁撤回前后的源码哈希和 AFLNet 崩溃样本统计。

## 范围

本基准只覆盖明文 IMAP/TCP，不覆盖 TLS/STARTTLS、POP3、LMTP、外部认证后端或性能吞吐量。短时构建和模糊运行用来验证复现性、协议处理、状态反馈和覆盖率采集；不等于安全审计，也不据此推断 Dovecot 存在或不存在漏洞。
