FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_JOBS=2
ARG UBUNTU_SNAPSHOT=20261014T000000Z
ARG ASTERISK_COMMIT=1da6eb34b3b23507e616863cf1e2c13c4f482fd7
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG ASTERISK_ARCHIVE_SHA256=8ed3a237e6d8dff94a09527a83143530b5afcc1aee73fa7b85c069bda507adac
ARG PJPROJECT_ARCHIVE_SHA256=04b2eb1f0f01aa0ad1945b167171843448a51aa6b7c3e806496d434f13a112b7
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV DEBIAN_FRONTEND=noninteractive \
    WORKDIR=/home/ubuntu/experiments \
    AFLNET=/home/ubuntu/aflnet \
    AFL_PATH=/home/ubuntu/aflnet \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    SOURCE_DATE_EPOCH=0 \
    TZ=UTC \
    ASAN_OPTIONS=abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# 固定 Ubuntu 软件源时间，且使用 BuildKit 缓存减少重建下载量。
# 基础镜像没有 CA 证书；引导阶段只关闭 TLS 证书校验，APT 仍验证 Ubuntu 签名索引和软件包哈希。
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    rm -rf /var/lib/apt/lists/* && \
    sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}/#g" /etc/apt/sources.list && \
    apt-get -o Acquire::https::Verify-Peer=false -o Acquire::https::Verify-Host=false \
      update -o Acquire::Retries=5 && \
    apt-get -o Acquire::https::Verify-Peer=false -o Acquire::https::Verify-Host=false \
      install -y -o Acquire::Retries=5 --no-install-recommends ca-certificates && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends \
      autoconf automake bison build-essential bzip2 ca-certificates clang curl flex gcovr gdb git \
      libblocksruntime-dev \
      graphviz graphviz-dev libasound2-dev libcap-dev libcurl4-openssl-dev \
      libedit-dev libgsm1-dev libjansson-dev libncurses5-dev libnewt-dev \
      libogg-dev libopus-dev libpcap-dev libpcre3-dev libspeex-dev \
      libspeexdsp-dev libsqlite3-dev libssl-dev libtinfo-dev libtool \
      libuuid1 libvorbis-dev libxml2-dev libxslt1-dev llvm llvm-dev make \
      netcat-openbsd patch pkg-config procps python3 python3-pip \
      python3-setuptools strace uuid-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 ubuntu && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu

# 上游的 bundled PJPROJECT 安装步骤会初始化 /opt/pjproject 数据目录，交由容器内构建用户维护。
RUN install -d -o ubuntu -g ubuntu /opt/pjproject

USER ubuntu
WORKDIR /home/ubuntu

COPY --chown=ubuntu:ubuntu aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY --chown=ubuntu:ubuntu asterisk-23.5.0-1da6eb34b3b23507e616863cf1e2c13c4f482fd7.tar.gz /tmp/asterisk.tar.gz
COPY --chown=ubuntu:ubuntu pjproject-2.17.tar.bz2 /tmp/pjproject-2.17.tar.bz2
COPY --chown=ubuntu:ubuntu aflnet-sip.patch asterisk-afl-build.patch \
    sip_aflnet.c parser-test.c /tmp/
COPY --chown=ubuntu:ubuntu prepare_seeds.py sip.dict /home/ubuntu/experiments/
COPY --chown=ubuntu:ubuntu seeds/ /home/ubuntu/experiments/seeds/
COPY --chown=ubuntu:ubuntu config/ /home/ubuntu/experiments/config/

# 校验全部源码输入，构建 AFLNet SIP/TCP 适配器并执行边界/状态测试。
RUN set -eu; \
    echo "${AFLNET_ARCHIVE_SHA256}  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    echo "${ASTERISK_ARCHIVE_SHA256}  /tmp/asterisk.tar.gz" | sha256sum -c -; \
    echo "${PJPROJECT_ARCHIVE_SHA256}  /tmp/pjproject-2.17.tar.bz2" | sha256sum -c -; \
    mkdir -p "${AFLNET}"; \
    tar -xzf /tmp/aflnet.tar.gz -C "${AFLNET}"; \
    sed -i 's/\r$//' "${AFLNET}"/Makefile "${AFLNET}"/aflnet.c \
      "${AFLNET}"/aflnet.h "${AFLNET}"/afl-fuzz.c \
      "${AFLNET}"/afl-replay.c "${AFLNET}"/aflnet-replay.c; \
    cp /tmp/sip_aflnet.c "${AFLNET}/sip_aflnet.c"; \
    git -C "${AFLNET}" apply --check /tmp/aflnet-sip.patch; \
    git -C "${AFLNET}" apply /tmp/aflnet-sip.patch; \
    read -r -a make_args <<< "${MAKE_JOBS}"; \
    make -C "${AFLNET}" -j"${make_args[0]}" all; \
    make -C "${AFLNET}/llvm_mode" -j"${make_args[0]}"; \
    cc -O2 -w -I"${AFLNET}" -c "${AFLNET}/aflnet.c" -o /tmp/aflnet-parser.o; \
    cc -O2 -Wall -Wextra -Werror -I"${AFLNET}" /tmp/parser-test.c \
      /tmp/aflnet-parser.o -o /tmp/sip-parser-test; \
    /tmp/sip-parser-test; \
    grep -a -q 'SIP' "${AFLNET}/afl-fuzz"; \
    rm -f /tmp/aflnet-parser.o /tmp/sip-parser-test

# 使用同一固定源码顺序构建参考版、AFL/ASan 版和 gcov 版；bininstall 不下载范围外的语音包。
# AFL 变体为 CC/CXX 显式指定包装器，并统一以 PIC 编译对象，兼容主程序 PIE 链接和共享模块。
# Asterisk 的 Blocks 探测会漏掉包装器运行时；AFL 变体显式链接 BlocksRuntime，并让主程序和模块共用 ASan 动态运行库。
# 通过 Clang 查询 ASan 动态库目录并写入 RPATH；AFL 变体另导出供动态模块解析的两个计数器符号。
# XML/XSLT 资源对象仅封装数据，不适用编译器包装器的插桩；AFL 变体用系统 Clang 生成这两类对象。
RUN set -eu; \
    ASAN_RUNTIME_SO=$(clang --print-file-name=libclang_rt.asan-x86_64.so); \
    test -f "${ASAN_RUNTIME_SO}"; \
    ASAN_RUNTIME_DIR=$(dirname "${ASAN_RUNTIME_SO}"); \
    read -r -a make_args <<< "${MAKE_JOBS}"; \
    for variant in reference afl gcov; do \
      if [[ "${variant}" == gcov ]]; then build_source=/home/ubuntu/asterisk-gcov-source; \
      else build_source=/tmp/asterisk-build; fi; \
      rm -rf "${build_source}"; \
      mkdir -p "${build_source}"; \
      tar -xzf /tmp/asterisk.tar.gz -C "${build_source}" --strip-components=1; \
      cp /tmp/pjproject-2.17.tar.bz2 "${build_source}/third-party/pjproject/pjproject-2.17.tar.bz2"; \
      prefix="/home/ubuntu/asterisk-${variant}"; \
      if [[ "${variant}" == afl ]]; then \
        (cd "${build_source}" && \
          patch -p1 --forward < /tmp/asterisk-afl-build.patch && \
          sed -i '/LINKER_SYMBOL_PREFIX_IO_stdin_used;/s/$/\n__afl_area_ptr;\n__afl_prev_loc;/' \
            main/asterisk.exports.in && \
          AFL_USE_ASAN=1 \
          CC="${AFLNET}/afl-clang-fast" CXX="${AFLNET}/afl-clang-fast++" \
          CFLAGS='-O1 -g -fno-omit-frame-pointer -fPIC' \
          LDFLAGS="-shared-libasan -Wl,-rpath,${ASAN_RUNTIME_DIR}" \
          ./configure --prefix="${prefix}" --with-pjproject-bundled --disable-xmldoc && \
          sed -i 's/^AST_CLANG_BLOCKS_LIBS=.*/AST_CLANG_BLOCKS_LIBS=-lBlocksRuntime/' makeopts && \
          AFL_USE_ASAN=1 CC="${AFLNET}/afl-clang-fast" \
            CXX="${AFLNET}/afl-clang-fast++" make -j"${make_args[0]}" && \
          AFL_USE_ASAN=1 CC="${AFLNET}/afl-clang-fast" \
            CXX="${AFLNET}/afl-clang-fast++" make bininstall); \
      elif [[ "${variant}" == gcov ]]; then \
        (cd "${build_source}" && CC=cc CFLAGS='-O0 -g --coverage' \
          LDFLAGS='--coverage' ./configure --prefix="${prefix}" \
          --with-pjproject-bundled --disable-xmldoc && \
          make -j"${make_args[0]}" && make bininstall); \
      else \
        (cd "${build_source}" && CC=cc CFLAGS='-O2 -g -fno-omit-frame-pointer' \
          ./configure --prefix="${prefix}" --with-pjproject-bundled --disable-xmldoc && \
          make -j"${make_args[0]}" && make bininstall); \
      fi; \
      test -x "${prefix}/sbin/asterisk"; \
      test -s "${prefix}/lib/asterisk/modules/chan_pjsip.so"; \
      test -s "${prefix}/lib/asterisk/modules/res_pjsip.so"; \
      if [[ "${variant}" == afl ]]; then \
        nm "${prefix}/sbin/asterisk" | grep -F '__afl_area_ptr' >/dev/null; \
        nm "${prefix}/lib/asterisk/modules/res_pjsip.so" | grep -F '__afl_area_ptr' >/dev/null; \
      fi; \
      if [[ "${variant}" != gcov ]]; then rm -rf "${build_source}"; fi; \
    done; \
    find "${build_source}" -type f \
      \( -name '*.o' -o -name '*.a' -o -name '*.la' -o -name '*.lo' \
         -o -name '*.so' -o -name '*.gcda' -o -name '*.d' \) -delete; \
    find "${build_source}" -type d -name '.deps' -prune -exec rm -rf {} +; \
    mkdir -p "${WORKDIR}"; \
    python3 /home/ubuntu/experiments/prepare_seeds.py /tmp/seeds-regenerated; \
    diff -r /home/ubuntu/experiments/seeds /tmp/seeds-regenerated; \
    { \
      printf 'base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214\n'; \
      printf 'ubuntu_snapshot=%s\n' "${UBUNTU_SNAPSHOT}"; \
      printf 'asterisk_ref=23.5.0\nasterisk_commit=%s\n' "${ASTERISK_COMMIT}"; \
      printf 'asterisk_archive_sha256=%s\n' "${ASTERISK_ARCHIVE_SHA256}"; \
      printf 'pjproject_version=2.17\npjproject_archive_sha256=%s\n' "${PJPROJECT_ARCHIVE_SHA256}"; \
      printf 'aflnet_commit=%s\naflnet_archive_sha256=%s\n' "${AFLNET_COMMIT}" "${AFLNET_ARCHIVE_SHA256}"; \
      printf 'aflnet_sip_patch_sha256='; sha256sum /tmp/aflnet-sip.patch | cut -d ' ' -f1; \
      printf 'asterisk_afl_build_patch_sha256='; sha256sum /tmp/asterisk-afl-build.patch | cut -d ' ' -f1; \
      printf 'sip_parser_sha256='; sha256sum "${AFLNET}/sip_aflnet.c" | cut -d ' ' -f1; \
      printf 'seed_manifest_sha256='; sha256sum /home/ubuntu/experiments/seeds/seeds-manifest.json | cut -d ' ' -f1; \
      printf 'compiler='; cc --version | sed -n '1p'; \
      printf 'clang='; clang --version | sed -n '1p'; \
      printf 'gcovr='; gcovr --version | sed -n '1p'; \
      printf 'build_variants=reference,afl+asan,gcov\n'; \
    } > "${WORKDIR}/build-versions.txt"; \
    for variant in reference afl gcov; do \
      printf 'asterisk_%s=' "${variant}" >> "${WORKDIR}/build-versions.txt"; \
      "/home/ubuntu/asterisk-${variant}/sbin/asterisk" -V \
        >> "${WORKDIR}/build-versions.txt" 2>&1; \
    done; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' | sort > "${WORKDIR}/package-manifest.txt"; \
    rm -rf /tmp/asterisk-build /tmp/aflnet.tar.gz /tmp/asterisk.tar.gz \
      /tmp/pjproject-2.17.tar.bz2 /tmp/seeds-regenerated

ENV PATH=/home/ubuntu/aflnet:${PATH} \
    ASTERISK_REFERENCE_PREFIX=/home/ubuntu/asterisk-reference \
    ASTERISK_AFL_PREFIX=/home/ubuntu/asterisk-afl \
    ASTERISK_GCOV_PREFIX=/home/ubuntu/asterisk-gcov \
    ASTERISK_GCOV_SOURCE=/home/ubuntu/asterisk-gcov-source

EXPOSE 5060/tcp
