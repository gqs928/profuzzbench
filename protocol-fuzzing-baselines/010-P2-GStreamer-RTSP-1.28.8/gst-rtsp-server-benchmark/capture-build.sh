#!/usr/bin/env bash
set -euo pipefail
cp -a /work/build-evidence/. /work/results/build/
cp /work/rtsp.dict /work/results/build/rtsp.dict
cp /work/seeds/* /work/results/build/
/opt/aflnet/afl-fuzz -h > /work/results/build/aflnet-help.txt 2>&1 || test "$?" -eq 1
PKG_CONFIG_PATH=/opt/gst-rtsp/lib/pkgconfig pkg-config --modversion gstreamer-rtsp-server-1.0 > /work/results/build/built-gst-rtsp-server-version.txt
nm /opt/gst-rtsp/lib/libgstrtspserver-1.0.so.0 | grep -c __afl_area_ptr > /work/results/build/target-instrumentation-symbol-count.txt
ldd /opt/gst-rtsp/test-launch > /work/results/build/target-ldd.txt
chmod -R a+rX /work/results/build
