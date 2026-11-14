#!/usr/bin/env bash
set -euo pipefail

# Replay a completed AFLNet queue on the separate gcov broker and render coverage.
if (($# < 2)); then
  echo "usage: coverage-run.sh FUZZ_OUTPUT_DIR OUTPUT_DIR [QUEUE_LIMIT]" >&2
  exit 2
fi
FUZZ_DIR=$1
OUTDIR=$2
if (($# >= 3)); then LIMIT=$3; else LIMIT=200; fi
TARGET_ROOT=/home/ubuntu/experiments/mosquitto-gcov

if [[ -e $OUTDIR ]] && [[ -n $(find "$OUTDIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "Output directory is nonempty: $OUTDIR. Choose a fresh path." >&2
  exit 2
fi
mkdir -p "$OUTDIR"
find "$TARGET_ROOT" -type f -name '*.gcda' -delete
MOSQUITTO_GCOV_BIN="$TARGET_ROOT/src/mosquitto" \
  python3 /workspace/coverage_replay.py "$FUZZ_DIR" "$OUTDIR/replay" "$LIMIT"

mkdir -p "$OUTDIR/coverage"
# Mosquitto compiles libcommon/, lib/ and src/ from their own working directories. The
# pinned gcovr 4.2 needs each object's original working directory specified.
# The C++ wrapper is not linked into the broker target. Remove its unused coverage
# notes before scanning so gcovr does not report missing data for unexecuted objects.
if [[ -d "$TARGET_ROOT/lib/cpp" ]]; then
  find "$TARGET_ROOT/lib/cpp" -type f \( -name '*.gcno' -o -name '*.gcda' \) -delete
fi
for component in libcommon lib src; do
  (
    cd "$TARGET_ROOT/$component"
    gcovr --root "$TARGET_ROOT" \
      --object-directory "$TARGET_ROOT/$component" \
      --json -o "$OUTDIR/coverage/$component.json" \
      "$TARGET_ROOT/$component"
  )
done

gcovr --root "$TARGET_ROOT" \
  --add-tracefile "$OUTDIR/coverage/lib.json" \
  --add-tracefile "$OUTDIR/coverage/libcommon.json" \
  --add-tracefile "$OUTDIR/coverage/src.json" \
  --html-details "$OUTDIR/coverage/index.html"
gcovr --root "$TARGET_ROOT" \
  --add-tracefile "$OUTDIR/coverage/lib.json" \
  --add-tracefile "$OUTDIR/coverage/libcommon.json" \
  --add-tracefile "$OUTDIR/coverage/src.json" \
  --print-summary > "$OUTDIR/coverage-summary.txt"
(
  cd "$OUTDIR"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
echo "Coverage reports: $OUTDIR/coverage/index.html and $OUTDIR/coverage-summary.txt"
