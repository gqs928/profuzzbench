FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_OPT=-j2
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG POSTGRES_VERSION=18.6
ARG POSTGRES_SHA256=555610c24d53e4316da5b7d3fc25c279d96856d5e0e23ee308c328c5fa881d9f
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV DEBIAN_FRONTEND=noninteractive WORKDIR=/home/ubuntu/experiments AFLNET=/home/ubuntu/aflnet AFL_PATH=/home/ubuntu/aflnet AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Ubuntu 基础层缺少 CA；首次只从固定快照按 APT 签名安装 CA，随后恢复 TLS 证书校验。
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked --mount=type=cache,target=/var/lib/apt,sharing=locked rm -f /etc/apt/apt.conf.d/docker-clean && sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}/#g" /etc/apt/sources.list && apt-get update -o Acquire::Retries=5 -o Acquire::Check-Valid-Until=false -o Acquire::https::Verify-Peer=false -o Acquire::https::Verify-Host=false && apt-get install -y -o Acquire::Retries=5 -o Acquire::Check-Valid-Until=false -o Acquire::https::Verify-Peer=false -o Acquire::https::Verify-Host=false --no-install-recommends ca-certificates && apt-get update -o Acquire::Retries=5 -o Acquire::Check-Valid-Until=false && apt-get install -y -o Acquire::Retries=5 -o Acquire::Check-Valid-Until=false --no-install-recommends autoconf automake bison build-essential ca-certificates clang flex gcc gcovr git graphviz graphviz-dev libtool llvm llvm-dev make perl pkg-config procps python3 python3-pip strace zip && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 ubuntu && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu
USER ubuntu
WORKDIR /home/ubuntu

COPY --chown=ubuntu:ubuntu postgresql-18.6.tar.bz2 aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz aflnet-postgres.patch postgres_aflnet.c parser-test.c /tmp/
COPY --chown=ubuntu:ubuntu test-stubs/ /tmp/test-stubs/
COPY --chown=ubuntu:ubuntu seeds/ /home/ubuntu/experiments/seeds/
COPY --chown=ubuntu:ubuntu seeds-manifest.json prepare_seeds.py clean.sh postgres.dict /home/ubuntu/experiments/
COPY --chown=ubuntu:ubuntu protocol_smoke.py coverage_replay.py seed_replay.py summarize_coverage.py fault_probe_server.c fault_probe_replay.py postgres-state-mapping.md /home/ubuntu/experiments/

RUN set -eu; echo "${POSTGRES_SHA256}  /tmp/postgresql-18.6.tar.bz2" | sha256sum -c -; echo "${AFLNET_ARCHIVE_SHA256}  /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz" | sha256sum -c -; mkdir -p "${AFLNET}" /tmp/postgres-source; tar -xzf /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C "${AFLNET}"; tar -xjf /tmp/postgresql-18.6.tar.bz2 -C /tmp/postgres-source --strip-components=1; sed -i 's/\r$//' "${AFLNET}"/Makefile "${AFLNET}"/aflnet.h "${AFLNET}"/afl-fuzz.c "${AFLNET}"/afl-replay.c "${AFLNET}"/aflnet-replay.c; cp /tmp/postgres_aflnet.c "${AFLNET}/postgres_aflnet.c"; git -C "${AFLNET}" apply --check /tmp/aflnet-postgres.patch; git -C "${AFLNET}" apply /tmp/aflnet-postgres.patch; read -r -a make_args <<< "${MAKE_OPT}"; AFL_NO_X86=1 make -C "${AFLNET}" all "${make_args[@]}"; AFL_NO_X86=1 make -C "${AFLNET}/llvm_mode" "${make_args[@]}"; cc -O2 -Wall -Wextra -Werror -I"${AFLNET}" /tmp/parser-test.c "${AFLNET}/postgres_aflnet.c" -o /tmp/parser-test; /tmp/parser-test; python3 /home/ubuntu/experiments/prepare_seeds.py /tmp/postgres-seed-check /tmp/postgres-seeds-check.json; diff -r /home/ubuntu/experiments/seeds /tmp/postgres-seed-check; cmp /home/ubuntu/experiments/seeds-manifest.json /tmp/postgres-seeds-check.json

RUN set -eu; read -r -a make_args <<< "${MAKE_OPT}"; for variant in reference afl gcov; do source_dir="${WORKDIR}/src-${variant}"; prefix="${WORKDIR}/postgres-${variant}"; mkdir -p "${source_dir}" "${prefix}"; cp -a /tmp/postgres-source/. "${source_dir}/"; configure_args=(--prefix="${prefix}" --enable-debug --without-readline --without-zlib --without-icu --without-openssl --without-ldap --without-pam --without-gssapi --without-libxml --without-lz4 --without-zstd); if [[ "${variant}" == afl ]]; then (cd "${source_dir}" && CC="${AFLNET}/afl-clang-fast" CFLAGS='-O1 -g' ./configure "${configure_args[@]}" && make "${make_args[@]}" && make install); elif [[ "${variant}" == gcov ]]; then (cd "${source_dir}" && configure_args+=(--enable-coverage) && CC=gcc CFLAGS='-O0 -g --coverage' LDFLAGS='--coverage' ./configure "${configure_args[@]}" && make "${make_args[@]}" && make install); else (cd "${source_dir}" && CC=gcc CFLAGS='-O2 -g' ./configure "${configure_args[@]}" && make "${make_args[@]}" && make install); fi; test -x "${prefix}/bin/postgres"; test -x "${prefix}/bin/initdb"; done; nm "${WORKDIR}/postgres-afl/bin/postgres" | grep -F '__afl_area_ptr' >/dev/null; { echo "postgresql_version=${POSTGRES_VERSION}"; echo "postgresql_archive_sha256=${POSTGRES_SHA256}"; echo "aflnet_commit=${AFLNET_COMMIT}"; echo "aflnet_archive_sha256=${AFLNET_ARCHIVE_SHA256}"; echo "aflnet_postgres_patch_sha256=$(sha256sum /tmp/aflnet-postgres.patch | cut -d ' ' -f1)"; echo "postgres_parser_sha256=$(sha256sum /tmp/postgres_aflnet.c | cut -d ' ' -f1)"; echo "seed_manifest_sha256=$(sha256sum ${WORKDIR}/seeds-manifest.json | cut -d ' ' -f1)"; echo "build_variants=reference,afl-instrumented,gcov"; echo "configure_options=debug,afl-instrumented-without-asan,coverage,no-readline,no-zlib,no-icu,no-openssl,no-ldap,no-pam,no-gssapi,no-libxml,no-lz4,no-zstd"; gcc --version | sed -n '1p'; clang --version | sed -n '1p'; for variant in reference afl gcov; do printf '%s: ' "${variant}"; "${WORKDIR}/postgres-${variant}/bin/pg_config" --version; done; } > "${WORKDIR}/build-versions.txt"; dpkg-query -W -f='${binary:Package}=${Version}\n' | sort > "${WORKDIR}/package-manifest.txt"

# AFLNet 源码目录含有指向 afl-as 的 as 链接，放在 PATH 末尾以免系统编译器递归调用。
ENV PATH=/home/ubuntu/experiments/postgres-reference/bin:${PATH}:/home/ubuntu/aflnet POSTGRES_REFERENCE_BIN=/home/ubuntu/experiments/postgres-reference/bin/postgres POSTGRES_AFL_BIN=/home/ubuntu/experiments/postgres-afl/bin/postgres POSTGRES_GCOV_BIN=/home/ubuntu/experiments/postgres-gcov/bin/postgres POSTGRES_INITDB_BIN=/home/ubuntu/experiments/postgres-reference/bin/initdb POSTGRES_PG_CTL_BIN=/home/ubuntu/experiments/postgres-reference/bin/pg_ctl

COPY --chown=ubuntu:ubuntu target-launcher.c aflnet-no-forkserver-fix.patch /home/ubuntu/experiments/
RUN git -C "${AFLNET}" apply --check /home/ubuntu/experiments/aflnet-no-forkserver-fix.patch && git -C "${AFLNET}" apply /home/ubuntu/experiments/aflnet-no-forkserver-fix.patch && read -r -a make_args <<< "${MAKE_OPT}" && AFL_NO_X86=1 make -C "${AFLNET}" all "${make_args[@]}" && /home/ubuntu/aflnet/afl-clang-fast -O1 -g -Wall -Wextra -Werror /home/ubuntu/experiments/target-launcher.c -o /home/ubuntu/experiments/target-launcher && nm /home/ubuntu/experiments/target-launcher | grep -F '__afl_area_ptr' >/dev/null && echo "aflnet_no_forkserver_fix_sha256=$(sha256sum /home/ubuntu/experiments/aflnet-no-forkserver-fix.patch | cut -d ' ' -f1)" >> /home/ubuntu/experiments/build-versions.txt && echo "target_launcher_sha256=$(sha256sum /home/ubuntu/experiments/target-launcher | cut -d ' ' -f1)" >> /home/ubuntu/experiments/build-versions.txt

EXPOSE 5432/tcp
