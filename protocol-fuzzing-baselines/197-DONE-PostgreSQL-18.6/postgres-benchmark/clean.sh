#!/usr/bin/env bash
set -euo pipefail

# 每个样本都重新初始化数据库，防止事务提交和临时对象污染下一轮。
PGDATA=${PGDATA:-/tmp/postgres-fuzz/data}
INITDB=${POSTGRES_INITDB_BIN:-/home/ubuntu/experiments/postgres-reference/bin/initdb}
PG_CTL=${POSTGRES_PG_CTL_BIN:-/home/ubuntu/experiments/postgres-reference/bin/pg_ctl}

if [[ -s ${PGDATA}/PG_VERSION ]]; then "${PG_CTL}" -D "${PGDATA}" stop --mode=immediate --wait --timeout=3 >/dev/null 2>&1 || true; fi
rm -rf -- "${PGDATA}"
mkdir -p -- "$(dirname "${PGDATA}")"
if ! "${INITDB}" -D "${PGDATA}" --no-sync --auth-local=trust --auth-host=trust --username=postgres --encoding=UTF8 --locale=C >/tmp/postgres-initdb.log 2>&1; then
	cat /tmp/postgres-initdb.log >&2
	exit 1
fi

cat >> "${PGDATA}/postgresql.conf" <<'EOF'
listen_addresses = '127.0.0.1'
port = 5432
unix_socket_directories = ''
max_connections = 20
shared_buffers = '16MB'
fsync = off
full_page_writes = off
synchronous_commit = off
log_destination = 'stderr'
logging_collector = off
log_min_messages = warning
EOF
cat > "${PGDATA}/pg_hba.conf" <<'EOF'
local all all trust
host all all 127.0.0.1/32 trust
host all all ::1/128 reject
EOF
chmod 700 "${PGDATA}"
echo "已重建 PostgreSQL 测试集群：${PGDATA}"
