ARG BUILDER_IMAGE=ubuntu:26.04@sha256:6a06111c3b0a8600feadb270aec771dc239bf407b25625f93f44ab00e11f4d3c
FROM ${BUILDER_IMAGE}

ARG MAKE_JOBS=2
ARG GST_RTSP_VERSION=1.28.8
ARG GST_RTSP_ARCHIVE_SHA256=59181ed21a5bc0533fb4f77cb7bc6005d89365e834b0c1294afb9ab5f7d96fe0
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    GST_DEBUG=0 \
    GST_REGISTRY_1_0=/tmp/gst-registry.bin

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential ca-certificates git make patch pkg-config python3 libgraphviz-dev \
      meson ninja-build \
      libglib2.0-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
      gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    && rm -rf /var/lib/apt/lists/*

COPY source/gst-rtsp-server-1.28.8.tar.xz /tmp/gst-rtsp-server-1.28.8.tar.xz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY source/SHA256SUMS /tmp/source-SHA256SUMS
COPY source/aflnet-commit.txt /tmp/aflnet-commit.txt
COPY patches/test-launch-signal-handling.patch /tmp/test-launch-signal-handling.patch
COPY seeds/ /work/seeds/
COPY rtsp.dict service_smoke.py run.sh validate.sh capture-build.sh /work/

RUN set -eux; \
    (cd /tmp && sha256sum -c source-SHA256SUMS); \
    mkdir -p /src/gst-rtsp-server /opt/aflnet /opt/gst-rtsp /work/build-evidence /work/results; \
    tar -xf /tmp/gst-rtsp-server-1.28.8.tar.xz --strip-components=1 -C /src/gst-rtsp-server; \
    patch -d /src/gst-rtsp-server -p1 --batch < /tmp/test-launch-signal-handling.patch; \
    tar -xzf /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/afl-replay.c /opt/aflnet/aflnet-replay.c; \
    AFL_NO_X86=1 CFLAGS='-O3 -funroll-loops -Wall -D_FORTIFY_SOURCE=2 -g -Wno-pointer-sign -Wno-unused-result -DTRUE=1 -DFALSE=0' make -C /opt/aflnet -j"${MAKE_JOBS}" afl-fuzz afl-gcc afl-showmap afl-as; \
    export AFL_PATH=/opt/aflnet AFL_QUIET=1; \
    CC=/opt/aflnet/afl-gcc CFLAGS='-O2 -g' meson setup /tmp/gst-rtsp-build /src/gst-rtsp-server \
      --prefix=/opt/gst-rtsp --libdir=lib -Dexamples=enabled -Dtests=disabled \
      -Dintrospection=disabled -Ddoc=disabled -Drtspclientsink=disabled; \
    meson compile -C /tmp/gst-rtsp-build -j"${MAKE_JOBS}"; \
    meson install -C /tmp/gst-rtsp-build; \
    cp /tmp/gst-rtsp-build/examples/test-launch /opt/gst-rtsp/test-launch; \
    printf 'gst_rtsp_server_version=' > /work/build-evidence/version.txt; \
    PKG_CONFIG_PATH=/opt/gst-rtsp/lib/pkgconfig pkg-config --modversion gstreamer-rtsp-server-1.0 >> /work/build-evidence/version.txt; \
    printf 'gstreamer_core_dependency=' >> /work/build-evidence/version.txt; pkg-config --modversion gstreamer-1.0 >> /work/build-evidence/version.txt; \
    printf 'gstreamer_plugins_base_dependency=' >> /work/build-evidence/version.txt; pkg-config --modversion gstreamer-app-1.0 >> /work/build-evidence/version.txt; \
    printf 'target_binary_sha256=' > /work/build-evidence/target-binary.sha256; sha256sum /opt/gst-rtsp/test-launch >> /work/build-evidence/target-binary.sha256; \
    printf 'target_library_sha256=' > /work/build-evidence/target-library.sha256; sha256sum /opt/gst-rtsp/lib/libgstrtspserver-1.0.so.0 >> /work/build-evidence/target-library.sha256; \
    printf 'target_instrumentation_symbols=' > /work/build-evidence/target-instrumentation-symbol-count.txt; nm /opt/gst-rtsp/lib/libgstrtspserver-1.0.so.0 | grep -c __afl_area_ptr >> /work/build-evidence/target-instrumentation-symbol-count.txt; \
    cp /tmp/aflnet-commit.txt /work/build-evidence/aflnet-commit.txt; \
    printf 'aflnet_archive_sha256=%s\n' "${AFLNET_ARCHIVE_SHA256}" > /work/build-evidence/aflnet-lock.txt; \
    printf 'aflnet_commit=%s\n' "${AFLNET_COMMIT}" >> /work/build-evidence/aflnet-lock.txt; \
    printf 'target_version=%s\n' "${GST_RTSP_VERSION}" > /work/build-evidence/build-lock.txt; \
    printf 'target_archive_sha256=%s\n' "${GST_RTSP_ARCHIVE_SHA256}" >> /work/build-evidence/build-lock.txt; \
    printf 'harness_patch_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /tmp/test-launch-signal-handling.patch | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'harness_patch_scope=%s\n' 'upstream test-launch example only: gracefully exit GLib main loop on SIGINT/SIGTERM so AFLNet can reset one RTSP server per testcase' >> /work/build-evidence/build-lock.txt; \
    printf 'builder_image=%s\n' 'ubuntu:26.04@sha256:6a06111c3b0a8600feadb270aec771dc239bf407b25625f93f44ab00e11f4d3c' >> /work/build-evidence/build-lock.txt; \
    printf 'compiler=' >> /work/build-evidence/build-lock.txt; /opt/aflnet/afl-gcc --version | sed -n '1p' >> /work/build-evidence/build-lock.txt; \
    printf 'gstreamer_build_packages:\n' >> /work/build-evidence/build-lock.txt; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' build-essential ca-certificates git make patch pkg-config python3 libgraphviz-dev meson ninja-build libglib2.0-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good >> /work/build-evidence/build-lock.txt; \
    chmod +x /work/run.sh /work/validate.sh /work/capture-build.sh

WORKDIR /work
ENTRYPOINT ["/bin/bash"]
