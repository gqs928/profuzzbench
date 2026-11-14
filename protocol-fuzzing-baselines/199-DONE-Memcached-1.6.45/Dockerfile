FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_OPT=-j1
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG AFLNET_REF=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG MEMCACHED_REF=2d51e364799bc9698bd4b11728ea978cea12da6e

ENV DEBIAN_FRONTEND=noninteractive
ENV WORKDIR=/home/ubuntu/experiments
ENV AFLNET=/home/ubuntu/aflnet
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1
ENV AFL_SKIP_CPUFREQ=1
ENV AFL_NO_AFFINITY=1
ENV ASAN_OPTIONS=abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1

RUN sed -i -E "s#https?://(archive|security)\.ubuntu\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}/#g" /etc/apt/sources.list && \
    apt-get -o Acquire::https::Verify-Peer=false -o Acquire::Retries=3 update && \
    apt-get -o Acquire::https::Verify-Peer=false install -y --no-install-recommends ca-certificates && \
    apt-get update -o Acquire::Retries=3 && \
    apt-get install -y --no-install-recommends \
      autoconf automake build-essential clang git gcovr gdb \
      graphviz graphviz-dev libevent-dev libaio-dev libtool llvm llvm-dev make \
      net-tools netcat-openbsd pkg-config procps python3 strace zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 ubuntu && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu

USER ubuntu
WORKDIR /home/ubuntu

# Build the pinned AFLNet commit with the Memcached ASCII/TCP parser patch.
COPY --chown=ubuntu:ubuntu aflnet-memcached.patch /tmp/aflnet-memcached.patch
COPY --chown=ubuntu:ubuntu memcached_aflnet.c /tmp/memcached_aflnet.c
COPY --chown=ubuntu:ubuntu parser-test.c /tmp/parser-test.c
RUN git init "${AFLNET}" && \
    git -C "${AFLNET}" remote add origin https://github.com/profuzzbench/aflnet.git && \
    git -C "${AFLNET}" fetch --depth=1 origin "${AFLNET_REF}" && \
    git -C "${AFLNET}" checkout --detach FETCH_HEAD && \
    test "$(git -C "${AFLNET}" rev-parse HEAD)" = "${AFLNET_REF}" && \
    cp /tmp/memcached_aflnet.c "${AFLNET}/memcached_aflnet.c" && \
    git -C "${AFLNET}" apply --unidiff-zero --check /tmp/aflnet-memcached.patch && \
    git -C "${AFLNET}" apply --unidiff-zero /tmp/aflnet-memcached.patch && \
    cd "${AFLNET}" && \
    env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin make clean all "${MAKE_OPT}" && \
    cd llvm_mode && \
    env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin make "${MAKE_OPT}"

RUN cc -O2 -I"${AFLNET}" /tmp/parser-test.c "${AFLNET}/memcached_aflnet.o" -o /tmp/parser-test && \
    /tmp/parser-test

ENV PATH=/home/ubuntu/.local/bin:${PATH}
ENV AFL_PATH=/home/ubuntu/aflnet

COPY --chown=ubuntu:ubuntu seeds/ /home/ubuntu/experiments/seeds/
COPY --chown=ubuntu:ubuntu prepare_seeds.py /home/ubuntu/experiments/prepare_seeds.py
RUN mkdir -p "${WORKDIR}/in-memcached" "${WORKDIR}/memcached-fuzz" \
             "${WORKDIR}/memcached-gcov" "${WORKDIR}/memcached-reference" && \
    python3 "${WORKDIR}/prepare_seeds.py" "${WORKDIR}/seeds" "${WORKDIR}/in-memcached" && \
    printf '"version"\n"stats"\n"set"\n"get"\n"gets"\n"delete"\n"flush_all"\n"quit"\n' \
      > "${WORKDIR}/memcached.dict"

# Three builds from the same immutable Memcached commit: unmodified reference,
# AFL-instrumented ASAN target, and gcov target for independent coverage replay.
RUN git init "${WORKDIR}/memcached-reference" && \
    git -C "${WORKDIR}/memcached-reference" remote add origin https://github.com/memcached/memcached.git && \
    git -C "${WORKDIR}/memcached-reference" fetch --depth=1 origin "${MEMCACHED_REF}" && \
    git -C "${WORKDIR}/memcached-reference" checkout --detach FETCH_HEAD && \
    test "$(git -C "${WORKDIR}/memcached-reference" rev-parse HEAD)" = "${MEMCACHED_REF}" && \
    cd "${WORKDIR}/memcached-reference" && ./autogen.sh && \
    env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ./configure --disable-dependency-tracking && \
    env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin make "${MAKE_OPT}"

RUN git init "${WORKDIR}/memcached-fuzz" && \
    git -C "${WORKDIR}/memcached-fuzz" remote add origin https://github.com/memcached/memcached.git && \
    git -C "${WORKDIR}/memcached-fuzz" fetch --depth=1 origin "${MEMCACHED_REF}" && \
    git -C "${WORKDIR}/memcached-fuzz" checkout --detach FETCH_HEAD && \
    test "$(git -C "${WORKDIR}/memcached-fuzz" rev-parse HEAD)" = "${MEMCACHED_REF}" && \
    cd "${WORKDIR}/memcached-fuzz" && ./autogen.sh && \
    env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    AFL_USE_ASAN=1 CC="${AFLNET}/afl-clang-fast" LIBS='-pthread' ./configure --disable-dependency-tracking && \
    env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin make "${MAKE_OPT}"

RUN git init "${WORKDIR}/memcached-gcov" && \
    git -C "${WORKDIR}/memcached-gcov" remote add origin https://github.com/memcached/memcached.git && \
    git -C "${WORKDIR}/memcached-gcov" fetch --depth=1 origin "${MEMCACHED_REF}" && \
    git -C "${WORKDIR}/memcached-gcov" checkout --detach FETCH_HEAD && \
    test "$(git -C "${WORKDIR}/memcached-gcov" rev-parse HEAD)" = "${MEMCACHED_REF}" && \
    cd "${WORKDIR}/memcached-gcov" && ./autogen.sh && \
    env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
      CFLAGS='-O0 -g -fprofile-arcs -ftest-coverage' LDFLAGS='--coverage' \
      ./configure --disable-dependency-tracking && \
    env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin make "${MAKE_OPT}"

RUN { \
      printf 'base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214\n'; \
      printf 'ubuntu_snapshot=%s\n' "${UBUNTU_SNAPSHOT}"; \
      printf 'aflnet_commit=%s\n' "$(git -C "${AFLNET}" rev-parse HEAD)"; \
      printf 'memcached_commit=%s\n' "$(git -C "${WORKDIR}/memcached-fuzz" rev-parse HEAD)"; \
      printf 'aflnet_memcached_patch_sha256=%s\n' "$(sha256sum /tmp/aflnet-memcached.patch | cut -d ' ' -f1)"; \
      printf 'memcached_parser_sha256=%s\n' "$(sha256sum /tmp/memcached_aflnet.c | cut -d ' ' -f1)"; \
      printf 'parser_test_sha256=%s\n' "$(sha256sum /tmp/parser-test.c | cut -d ' ' -f1)"; \
      printf 'memcached_version='; "${WORKDIR}/memcached-fuzz/memcached" -h 2>&1 | sed -n '1p'; \
      dpkg-query -W -f='${binary:Package}=${Version}\n' autoconf automake build-essential clang gcovr git llvm llvm-dev make python3; \
    } > "${WORKDIR}/build-versions.txt"

EXPOSE 11211/tcp
CMD ["/home/ubuntu/experiments/memcached-fuzz/memcached", "-B", "ascii", "-p", "11211", "-U", "0", "-t", "1"]
