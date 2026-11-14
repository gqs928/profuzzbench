FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG MAKE_JOBS=1

ENV DEBIAN_FRONTEND=noninteractive \
    UBUNTU_SNAPSHOT=20260928T000000Z \
    AFLNET_REF=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732 \
    GANESHA_REF=7af850559957b244e712280dd3590c4cbaedaae8 \
    NTIRPC_REF=366b5c3c1f8cb4090df942ce57e9913be96406a9 \
    AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d \
    GANESHA_ARCHIVE_SHA256=668b6eef4f073cc46f68afe54c4d83185b049df5a5cd239367759d6fba01f927 \
    NTIRPC_ARCHIVE_SHA256=9b0b7963a40b15565f5ea55454d2c0d69d5737ead5a1dede63059d0c4b183153 \
    WORKDIR=/home/ubuntu/experiments \
    AFLNET=/home/ubuntu/aflnet \
    AFL_PATH=/home/ubuntu/aflnet \
    GANESHA_REFERENCE_PREFIX=/home/ubuntu/experiments/ganesha-reference \
    GANESHA_AFL_PREFIX=/home/ubuntu/experiments/ganesha-afl \
    GANESHA_GCOV_PREFIX=/home/ubuntu/experiments/ganesha-gcov \
    GANESHA_REFERENCE_BIN=/home/ubuntu/experiments/ganesha-reference/bin/ganesha.nfsd \
    GANESHA_AFL_BIN=/home/ubuntu/experiments/ganesha-afl/bin/ganesha.nfsd \
    GANESHA_GCOV_BIN=/home/ubuntu/experiments/ganesha-gcov/bin/ganesha.nfsd \
    GANESHA_REFERENCE_CONFIG=/workspace/ganesha.conf \
    GANESHA_AFL_CONFIG=/workspace/ganesha.conf \
    GANESHA_GCOV_CONFIG=/workspace/ganesha.conf \
    NFS_PORT=12049 \
    MOUNT_PORT=12050 \
    NFS_PSEUDO=/nfs-fuzz \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR /workspace

# 固定 Ubuntu 软件源快照；只装 NFSv3、FSAL_MEM 和覆盖率构建依赖。
RUN rm -f /etc/apt/apt.conf.d/docker-clean && \
    sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/$UBUNTU_SNAPSHOT/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 -o Acquire::https::Verify-Peer=false && \
    apt-get install -y -o Acquire::Retries=5 -o Acquire::https::Verify-Peer=false --no-install-recommends ca-certificates && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends \
      autoconf automake bison build-essential ca-certificates clang cmake \
      flex gcovr git graphviz libgraphviz-dev libacl1-dev libattr1-dev libcap-dev libevent-dev \
      libkrb5-dev libssl-dev libtirpc-dev liburcu-dev libtool llvm llvm-dev make \
      pkg-config procps python3 python3-minimal zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 ubuntu && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu && \
    mkdir -p /home/ubuntu/experiments /home/ubuntu/aflnet && \
    chown -R ubuntu:ubuntu /home/ubuntu

USER ubuntu
COPY --chown=ubuntu:ubuntu aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY --chown=ubuntu:ubuntu nfs-ganesha-V9.14.tar.gz /tmp/ganesha.tar.gz
COPY --chown=ubuntu:ubuntu ntirpc-366b5c3c1f8cb4090df942ce57e9913be96406a9.tar.gz /tmp/ntirpc.tar.gz
COPY --chown=ubuntu:ubuntu aflnet-nfs.patch parser-test.c fault_probe.c /tmp/

RUN set -eu; \
    echo "$AFLNET_ARCHIVE_SHA256  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    echo "$GANESHA_ARCHIVE_SHA256  /tmp/ganesha.tar.gz" | sha256sum -c -; \
    echo "$NTIRPC_ARCHIVE_SHA256  /tmp/ntirpc.tar.gz" | sha256sum -c -; \
    tar -xzf /tmp/aflnet.tar.gz -C "$AFLNET"; \
    mkdir -p /tmp/ganesha-src; \
    tar -xzf /tmp/ganesha.tar.gz -C /tmp/ganesha-src --strip-components=1; \
    tar -xzf /tmp/ntirpc.tar.gz -C /tmp/ganesha-src/src/libntirpc --strip-components=1; \
    sed -i 's/\r$//' "$AFLNET"/Makefile "$AFLNET"/aflnet.h \
      "$AFLNET"/afl-fuzz.c "$AFLNET"/afl-replay.c "$AFLNET"/aflnet-replay.c; \
    git -C "$AFLNET" apply --check /tmp/aflnet-nfs.patch; \
    git -C "$AFLNET" apply /tmp/aflnet-nfs.patch; \
    make -C "$AFLNET" -j"$MAKE_JOBS" all; \
    make -C "$AFLNET/llvm_mode" -j"$MAKE_JOBS"; \
    "$AFLNET/afl-clang-fast" -O1 -g -fno-omit-frame-pointer \
      /tmp/fault_probe.c -o "$WORKDIR/fault-probe"; \
    cc -O2 -Wall -Wextra -Werror -I"$AFLNET" /tmp/parser-test.c \
      "$AFLNET/nfs_aflnet.o" -o /tmp/nfs-parser-test; \
    /tmp/nfs-parser-test; \
    cp -a /tmp/ganesha-src "$WORKDIR/ganesha-reference-src"; \
    cp -a /tmp/ganesha-src "$WORKDIR/ganesha-afl-src"; \
    cp -a /tmp/ganesha-src "$WORKDIR/ganesha-gcov-src"; \
    common_args=( \
      -DUSE_SYSTEM_NTIRPC=OFF -DRPCBIND=OFF -DUSE_GSS=OFF -DUSE_NFS_RDMA=OFF -DUSE_9P=OFF \
      -DUSE_DBUS=OFF -DUSE_NFSIDMAP=OFF -DUSE_CAPS=OFF -DUSE_UNWIND=OFF \
      -DUSE_NLM=OFF -DUSE_MONITORING=OFF -DUSE_ADMIN_TOOLS=OFF -DUSE_GUI_ADMIN_TOOLS=OFF \
      -DUSE_RADOS_RECOV=OFF -DRADOS_URLS=OFF -D_MSPAC_SUPPORT=OFF \
      -DUSE_FSAL_PROXY_V4=OFF -DUSE_FSAL_PROXY_V3=OFF -DUSE_FSAL_VFS=OFF \
      -DUSE_FSAL_LUSTRE=OFF -DUSE_FSAL_LIZARDFS=OFF -DUSE_FSAL_KVSFS=OFF \
      -DUSE_FSAL_CEPH=OFF -DUSE_FSAL_GPFS=OFF -DUSE_FSAL_XFS=OFF \
      -DUSE_FSAL_GLUSTER=OFF -DUSE_FSAL_NULL=OFF -DUSE_FSAL_RGW=OFF \
      -DUSE_FSAL_SAUNAFS=OFF -DUSE_FSAL_MEM=ON ); \
    cmake -S "$WORKDIR/ganesha-reference-src/src" -B "$WORKDIR/build-reference" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_INSTALL_PREFIX="$GANESHA_REFERENCE_PREFIX" "${common_args[@]}"; \
    cmake --build "$WORKDIR/build-reference" --parallel "$MAKE_JOBS"; \
    cmake --install "$WORKDIR/build-reference"; \
    export CC="$AFLNET/afl-clang-fast" CXX="$AFLNET/afl-clang-fast++"; \
    cmake -S "$WORKDIR/ganesha-afl-src/src" -B "$WORKDIR/build-afl" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX="$GANESHA_AFL_PREFIX" \
      -DCMAKE_C_FLAGS="-O1 -g -fno-omit-frame-pointer" \
      -DCMAKE_CXX_FLAGS="-O1 -g -fno-omit-frame-pointer" "${common_args[@]}"; \
    cmake --build "$WORKDIR/build-afl" --parallel "$MAKE_JOBS"; \
    cmake --install "$WORKDIR/build-afl"; \
    unset AFL_USE_ASAN; export CC=cc CXX=c++; \
    cmake -S "$WORKDIR/ganesha-gcov-src/src" -B "$WORKDIR/build-gcov" \
      -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX="$GANESHA_GCOV_PREFIX" \
      -DCMAKE_C_FLAGS="-O0 -g --coverage" -DCMAKE_CXX_FLAGS="-O0 -g --coverage" \
      -DCMAKE_EXE_LINKER_FLAGS="--coverage" -DCMAKE_SHARED_LINKER_FLAGS="--coverage" \
      -DCOVERAGE=ON "${common_args[@]}"; \
    cmake --build "$WORKDIR/build-gcov" --parallel "$MAKE_JOBS"; \
    cmake --install "$WORKDIR/build-gcov"; \
    for variant in reference afl gcov; do \
      test -x "$WORKDIR/ganesha-$variant/bin/ganesha.nfsd"; \
      find "$WORKDIR/ganesha-$variant" -name 'libfsalmem.so' -print -quit | grep -q .; \
    done; \
    { \
      printf 'base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214\n'; \
      printf 'ubuntu_snapshot=%s\n' "$UBUNTU_SNAPSHOT"; \
      printf 'aflnet_commit=%s\n' "$AFLNET_REF"; \
      printf 'nfs_ganesha_version=V9.14\n'; \
      printf 'nfs_ganesha_commit=%s\n' "$GANESHA_REF"; \
      printf 'ntirpc_version=366b5c3c1f8cb4090df942ce57e9913be96406a9\n'; \
      printf 'ntirpc_commit=%s\n' "$NTIRPC_REF"; \
      printf 'source_hashes=%s,%s,%s\n' "$AFLNET_ARCHIVE_SHA256" "$GANESHA_ARCHIVE_SHA256" "$NTIRPC_ARCHIVE_SHA256"; \
      cc --version | sed -n '1p'; clang --version | sed -n '1p'; \
      dpkg-query -W build-essential clang cmake gcovr llvm liburcu-dev make python3; \
    } > "$WORKDIR/build-versions.txt"; \
    mkdir -p "$WORKDIR/in-nfs"; \
    rm -f /tmp/nfs-parser-test

COPY --chown=ubuntu:ubuntu . /workspace
COPY --chown=ubuntu:ubuntu source/SHA256SUMS /workspace/source/SHA256SUMS
RUN for prefix in "$GANESHA_REFERENCE_PREFIX" "$GANESHA_AFL_PREFIX" "$GANESHA_GCOV_PREFIX"; do \
      mkdir -p "$prefix/var/lib/nfs/ganesha"; \
    done
RUN "$AFLNET/afl-clang-fast" -O1 -g -fno-omit-frame-pointer \
      /workspace/fault_probe.c -o "$WORKDIR/fault-probe" && \
    test -x "$WORKDIR/fault-probe"

EXPOSE 12049/tcp 12050/tcp
CMD ["bash"]
