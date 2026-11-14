FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_OPT=-j2
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG FREERADIUS_REF=release_3_2_10
ARG FREERADIUS_COMMIT=9071ea0
ARG AFLNET_REF=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG FREERADIUS_ARCHIVE_SHA256=3e9f24439ce976c04e4c56441722a3bd18677a61dd17f67bc8863eb4ed36cd4b
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV DEBIAN_FRONTEND=noninteractive \
    WORKDIR=/home/ubuntu/experiments \
    AFLNET=/home/ubuntu/aflnet \
    AFL_PATH=/home/ubuntu/aflnet \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    ASAN_OPTIONS=abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends ca-certificates && \
    sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends \
      autoconf automake build-essential ca-certificates clang gcovr git graphviz graphviz-dev libcap-dev \
      libpcre3-dev libssl-dev libtalloc-dev libtool llvm llvm-dev make \
      netcat-openbsd patch pkg-config procps python3 strace && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 ubuntu && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu

USER ubuntu
WORKDIR /home/ubuntu

COPY --chown=ubuntu:ubuntu aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY --chown=ubuntu:ubuntu freeradius-3.2.10.tar.gz /tmp/freeradius.tar.gz
COPY --chown=ubuntu:ubuntu aflnet-radius.patch radius_aflnet.c parser-test.c build-scope.patch /tmp/

RUN set -eu; \
    echo "${AFLNET_ARCHIVE_SHA256}  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    echo "${FREERADIUS_ARCHIVE_SHA256}  /tmp/freeradius.tar.gz" | sha256sum -c -; \
    mkdir -p "${AFLNET}" /tmp/freeradius-source; \
    tar -xzf /tmp/aflnet.tar.gz -C "${AFLNET}"; \
    tar -xzf /tmp/freeradius.tar.gz -C /tmp/freeradius-source --strip-components=1; \
    sed -i 's/\r$//' "${AFLNET}"/Makefile "${AFLNET}"/aflnet.h \
      "${AFLNET}"/afl-fuzz.c "${AFLNET}"/afl-replay.c \
      "${AFLNET}"/aflnet-replay.c; \
    cp /tmp/radius_aflnet.c "${AFLNET}/radius_aflnet.c"; \
    git -C "${AFLNET}" apply --check /tmp/aflnet-radius.patch; \
    git -C "${AFLNET}" apply /tmp/aflnet-radius.patch; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    AFL_NO_X86=1 make -C "${AFLNET}" all "${make_args[@]}"; \
    AFL_NO_X86=1 make -C "${AFLNET}/llvm_mode" "${make_args[@]}"; \
    cc -O2 -Wall -Wextra -Werror -I"${AFLNET}" /tmp/parser-test.c \
      "${AFLNET}/radius_aflnet.o" -o /tmp/parser-test; \
    /tmp/parser-test

COPY --chown=ubuntu:ubuntu site-default clients.conf authorize radius.dict \
     prepare_seeds.py clean.sh seeds-manifest.json /home/ubuntu/experiments/
COPY --chown=ubuntu:ubuntu seeds/ /home/ubuntu/experiments/seeds/

RUN set -eu; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    for variant in reference afl gcov; do \
      source_dir="${WORKDIR}/src-${variant}"; \
      prefix="${WORKDIR}/freeradius-${variant}"; \
      mkdir -p "${source_dir}" "${prefix}"; \
      cp -a /tmp/freeradius-source/. "${source_dir}/"; \
      git -C "${source_dir}" apply --check /tmp/build-scope.patch; \
      git -C "${source_dir}" apply /tmp/build-scope.patch; \
      configure_args=(--prefix="${prefix}" --sysconfdir="${prefix}/etc" \
        --localstatedir="${prefix}/var" --with-logdir="${prefix}/var/log/radius" \
        --with-radacctdir="${prefix}/var/log/radius/radacct" --with-tcp \
        --with-modules='rlm_detail rlm_files rlm_pap' \
        --enable-reproducible-builds); \
      if [[ "${variant}" == afl ]]; then \
        (cd "${source_dir}" && AFL_USE_ASAN=1 CC="${AFLNET}/afl-clang-fast" \
          CFLAGS='-O1 -g' LDFLAGS='' ./configure "${configure_args[@]}" && \
          AFL_USE_ASAN=1 make "${make_args[@]}" && AFL_USE_ASAN=1 make install); \
      elif [[ "${variant}" == gcov ]]; then \
        (cd "${source_dir}" && CC=cc CFLAGS='-O0 -g --coverage' \
          LDFLAGS='--coverage' ./configure "${configure_args[@]}" && \
          make "${make_args[@]}" && make install); \
      else \
        (cd "${source_dir}" && ./configure "${configure_args[@]}" && \
          make "${make_args[@]}" && make install); \
      fi; \
      mkdir -p "${prefix}/etc/raddb/sites-enabled" \
        "${prefix}/etc/raddb/mods-enabled" "${prefix}/etc/raddb/mods-config/files" \
        "${prefix}/var/run/radiusd" "${prefix}/var/log/radius"; \
      rm -f "${prefix}/etc/raddb/sites-enabled/"*; \
      rm -f "${prefix}/etc/raddb/mods-enabled/"*; \
      ln -s ../sites-available/default "${prefix}/etc/raddb/sites-enabled/default"; \
      for module in detail files pap; do \
        ln -s "../mods-available/${module}" "${prefix}/etc/raddb/mods-enabled/${module}"; \
      done; \
      cp /home/ubuntu/experiments/site-default \
        "${prefix}/etc/raddb/sites-available/default"; \
      cp /home/ubuntu/experiments/clients.conf "${prefix}/etc/raddb/clients.conf"; \
      cp /home/ubuntu/experiments/authorize \
        "${prefix}/etc/raddb/mods-config/files/authorize"; \
      sed -i -E 's#^([[:space:]]*)filename = .*#\1filename = /home/ubuntu/experiments/state/radacct/detail#' \
        "${prefix}/etc/raddb/mods-available/detail"; \
      test -x "${prefix}/sbin/radiusd"; \
      test -x "${prefix}/bin/radclient"; \
    done; \
    nm "${WORKDIR}/freeradius-afl/sbin/radiusd" | grep -F '__afl_area_ptr' >/dev/null; \
    python3 "${WORKDIR}/prepare_seeds.py" /tmp/seeds-check /tmp/seeds-check-manifest.json; \
    diff -r "${WORKDIR}/seeds" /tmp/seeds-check; \
    cmp "${WORKDIR}/seeds-manifest.json" /tmp/seeds-check-manifest.json; \
    { \
      printf 'base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214\n'; \
      printf 'ubuntu_snapshot=%s\n' "${UBUNTU_SNAPSHOT}"; \
      printf 'freeradius_tag=%s\nfreeradius_commit=%s\n' "${FREERADIUS_REF}" "${FREERADIUS_COMMIT}"; \
      printf 'freeradius_archive_sha256=%s\n' "${FREERADIUS_ARCHIVE_SHA256}"; \
      printf 'aflnet_commit=%s\naflnet_archive_sha256=%s\n' "${AFLNET_REF}" "${AFLNET_ARCHIVE_SHA256}"; \
      printf 'aflnet_radius_patch_sha256='; sha256sum /tmp/aflnet-radius.patch | cut -d ' ' -f1; \
      printf 'radius_parser_sha256='; sha256sum /tmp/radius_aflnet.c | cut -d ' ' -f1; \
      printf 'build_scope_patch_sha256='; sha256sum /tmp/build-scope.patch | cut -d ' ' -f1; \
      printf 'parser_test_sha256='; sha256sum /tmp/parser-test.c | cut -d ' ' -f1; \
      cc --version | sed -n '1p'; clang --version | sed -n '1p'; \
      printf 'build_variants=reference,afl+asan,gcov\nconfigure_modules=rlm_detail,rlm_files,rlm_pap\n'; \
      printf 'benchmark_site_sha256='; sha256sum /home/ubuntu/experiments/site-default | cut -d ' ' -f1; \
      printf 'seed_manifest_sha256='; sha256sum "${WORKDIR}/seeds-manifest.json" | cut -d ' ' -f1; \
    } > "${WORKDIR}/build-versions.txt"; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' | sort > "${WORKDIR}/package-manifest.txt"

ENV PATH=/home/ubuntu/aflnet:${PATH} \
    RADIUS_REFERENCE_BIN=/home/ubuntu/experiments/freeradius-reference/sbin/radiusd \
    RADIUS_AFL_BIN=/home/ubuntu/experiments/freeradius-afl/sbin/radiusd \
    RADIUS_GCOV_BIN=/home/ubuntu/experiments/freeradius-gcov/sbin/radiusd \
    RADIUS_REFERENCE_CONFIG=/home/ubuntu/experiments/freeradius-reference/etc/raddb \
    RADIUS_AFL_CONFIG=/home/ubuntu/experiments/freeradius-afl/etc/raddb \
    RADIUS_GCOV_CONFIG=/home/ubuntu/experiments/freeradius-gcov/etc/raddb

EXPOSE 1812/udp 1813/udp 1812/tcp 1813/tcp
