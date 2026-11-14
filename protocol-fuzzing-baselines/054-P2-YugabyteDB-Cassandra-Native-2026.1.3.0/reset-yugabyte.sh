#!/usr/bin/env bash
set -euo pipefail

WORKDIR=${WORKDIR:-/opt/benchmark}
LIFECYCLE_LOG=${YUGABYTE_LIFECYCLE_LOG:-/results/yugabyte-lifecycle.tsv}
YCQL_PORT=${YCQL_PORT:-9042}
YCQL_HOST=${YCQL_HOST:-$(hostname -i | awk '{print $1}')}
YCQLSH=/home/yugabyte/bin/ycqlsh
mkdir -p "$(dirname "$LIFECYCLE_LOG")"
record() { printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "$LIFECYCLE_LOG"; }

if ! /bin/bash "$WORKDIR/start-yugabyte.sh"; then
  record 'reset-failed=server-not-ready'
  exit 1
fi

keyspaces=$(runuser -u yugabyte -- "$YCQLSH" "$YCQL_HOST" "$YCQL_PORT" \
  --request-timeout=10 -e 'SELECT keyspace_name FROM system_schema.keyspaces')
mapfile -t user_keyspaces < <(awk '
  /^[[:space:]]*keyspace_name[[:space:]]*$/ { next }
  /^-+$/ { in_rows = 1; next }
  in_rows && /^\([0-9]+ rows?\)$/ { exit }
  in_rows {
    gsub(/^[[:space:]]+|[[:space:]]+$/, "")
    if (length($0)) print $0
  }
' <<< "$keyspaces")

dropped=0
for keyspace in "${user_keyspaces[@]}"; do
  case "$keyspace" in
    system|system_*) continue ;;
  esac
  [[ "$keyspace" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || {
    record 'reset-failed=unsupported-keyspace-identifier'
    exit 1
  }
  runuser -u yugabyte -- "$YCQLSH" "$YCQL_HOST" "$YCQL_PORT" \
    --request-timeout=20 -e "DROP KEYSPACE IF EXISTS \"${keyspace}\"" >/dev/null
  dropped=$((dropped + 1))
done
record "reset-ok product_version=${YUGABYTE_EXPECTED_VERSION:-2026.1.3.0} user_keyspaces_dropped=$dropped"
