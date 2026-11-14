FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_OPT=-j2
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG DOVECOT_COMMIT=0cbb641e3e88d1616c2e8c1ff109c67c0985ddc6
ARG DOVECOT_VERSION=2.4.5
ARG DOVECOT_ARCHIVE_SHA256=4137f23e67aa89752870ae01a1def97d4da046f436a18b6731194ce1fe15d963
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV DEBIAN_FRONTEND=noninteractive \
    WORKDIR=/home/ubuntu/experiments \
    AFLNET=/home/ubuntu/aflnet \
    AFL_PATH=/home/ubuntu/aflnet \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# 先安装证书，再切换到固定 Ubuntu 快照，后续软件包均由该快照提供。
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends ca-certificates && \
    sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends \
      autoconf automake bison build-essential ca-certificates clang flex gcovr gettext git \
      graphviz graphviz-dev libcap-dev libpcre2-32-0 libpcre2-dev libssl-dev \
      libtool llvm llvm-dev make netcat-openbsd patch perl pkg-config procps sudo wget \
      python3 zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 ubuntu && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu && \
    groupadd --gid 1001 dovecot && \
    usermod -aG dovecot ubuntu

USER ubuntu
WORKDIR /home/ubuntu

COPY --chown=ubuntu:ubuntu aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY --chown=ubuntu:ubuntu dovecot-core-0cbb641e3e88d1616c2e8c1ff109c67c0985ddc6.tar.gz /tmp/dovecot.tar.gz
COPY --chown=ubuntu:ubuntu aflnet-imap.patch imap_aflnet.c parser-test.c \
     fault_probe_server.c /tmp/
COPY --chown=ubuntu:ubuntu prepare_seeds.py prepare_maildir.py \
     seeds-manifest.json dovecot.conf passwd imap.dict clean.sh reset-state.sh \
     start-server.sh /home/ubuntu/experiments/
COPY --chown=ubuntu:ubuntu seeds/ /home/ubuntu/experiments/seeds/

# 校验源码快照，应用 AFLNet 的 IMAP 适配补丁并编译适配器自测。
RUN set -eu; \
    echo "${AFLNET_ARCHIVE_SHA256}  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    echo "${DOVECOT_ARCHIVE_SHA256}  /tmp/dovecot.tar.gz" | sha256sum -c -; \
    mkdir -p "${AFLNET}" /tmp/dovecot-source; \
    tar -xzf /tmp/aflnet.tar.gz -C "${AFLNET}"; \
    tar -xzf /tmp/dovecot.tar.gz -C /tmp/dovecot-source --strip-components=1; \
    sed -i 's/\r$//' "${AFLNET}"/Makefile "${AFLNET}"/aflnet.h \
      "${AFLNET}"/afl-fuzz.c "${AFLNET}"/afl-replay.c \
      "${AFLNET}"/aflnet-replay.c; \
    cp /tmp/imap_aflnet.c "${AFLNET}/imap_aflnet.c"; \
    git -C "${AFLNET}" apply --check /tmp/aflnet-imap.patch; \
    git -C "${AFLNET}" apply /tmp/aflnet-imap.patch; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    AFL_NO_X86=1 make -C "${AFLNET}" all "${make_args[@]}"; \
    AFL_NO_X86=1 make -C "${AFLNET}/llvm_mode" "${make_args[@]}"; \
    cc -O2 -Wall -Wextra -Werror -I"${AFLNET}" /tmp/parser-test.c \
      "${AFLNET}/imap_aflnet.c" -o /tmp/parser-test; \
    /tmp/parser-test; \
    mkdir -p /home/ubuntu/experiments; \
    "${AFLNET}/afl-clang-fast" -O1 -g -Wall -Wextra -Werror \
      /tmp/fault_probe_server.c -o /home/ubuntu/experiments/fault_probe_server; \
    test "$(cat /tmp/dovecot-source/version.txt)" = "${DOVECOT_VERSION}"

# 从同一源码快照构建普通、AFL 覆盖插桩与 gcov 三套服务端。
COPY --chown=ubuntu:ubuntu Dockerfile source-lock.json /home/ubuntu/experiments/
COPY ucd-checksums.sha256 /tmp/ucd-checksums.sha256
COPY --chmod=0755 dovecot-root-launcher.sh /usr/local/sbin/dovecot-root-launcher
COPY --chmod=0440 sudoers.dovecot-benchmark /etc/sudoers.d/dovecot-benchmark
USER root
RUN visudo -cf /etc/sudoers.d/dovecot-benchmark
USER ubuntu
RUN set -eu; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    cd /tmp/dovecot-source; \
    ucd_dir=/tmp/dovecot-source/src/lib/ucd; \
    ucd_files=(CaseFolding.txt CompositionExclusions.txt DerivedBidiClass.txt \
      DerivedCoreProperties.txt DerivedJoiningType.txt DerivedNormalizationProps.txt \
      emoji-data.txt GraphemeBreakProperty.txt GraphemeBreakTest.txt \
      NormalizationTest.txt PropertyValueAliases.txt PropList.txt Scripts.txt \
      SpecialCasing.txt UnicodeData.txt WordBreakProperty.txt \
      IdnaMappingTable.txt IdnaTestV2.txt); \
    for ucd_file in "${ucd_files[@]}"; do \
      wget -nv --no-use-server-timestamps -O "${ucd_dir}/${ucd_file}" \
        "https://dovecot.org/res/${ucd_file}"; \
    done; \
    (cd "${ucd_dir}" && sha256sum -c /tmp/ucd-checksums.sha256); \
    (cd "${ucd_dir}" && sha256sum "${ucd_files[@]}") \
      | tee /home/ubuntu/experiments/ucd-sha256.txt; \
    ./autogen.sh; \
    revision=${DOVECOT_COMMIT:0:12}; \
    printf '%s\n' '#ifndef DOVECOT_VERSION_H' '#define DOVECOT_VERSION_H' \
      "#define DOVECOT_REVISION \"${revision}\"" \
      '#define DOVECOT_VERSION_FULL VERSION" ("DOVECOT_REVISION")"' \
      '#define DOVECOT_BUILD_INFO DOVECOT_VERSION_FULL' '#endif' \
      > /tmp/dovecot-source/dovecot-version.h; \
    for variant in reference afl gcov; do \
      cp -a /tmp/dovecot-source "/home/ubuntu/experiments/src-${variant}"; \
      source_dir="/home/ubuntu/experiments/src-${variant}"; \
      prefix="/home/ubuntu/experiments/dovecot-${variant}"; \
      configure_args=(--prefix="${prefix}" --sysconfdir="${prefix}/etc" \
        --localstatedir="${prefix}/var" --with-rundir="${prefix}/var/run/dovecot" \
        --with-statedir="${prefix}/var/lib/dovecot" --with-ioloop=epoll \
        --with-notify=none --without-pam --without-bsdauth --without-gssapi \
        --without-ldap --without-sql --without-pgsql --without-mysql \
        --without-sqlite --without-cassandra --without-stemmer --without-textcat \
        --without-icu --without-solr --without-flatcurve --without-sodium \
        --without-bzlib --without-lz4 --without-zstd --without-libcap \
        --with-systemd=no --without-lua); \
      while IFS= read -r source_subdir; do \
        mkdir -p "${source_subdir}/.libs"; \
      done < <(find "${source_dir}/src" -type d -print); \
      if [[ "${variant}" == afl ]]; then \
        (cd "${source_dir}" && CC="${AFLNET}/afl-clang-fast" \
          CFLAGS='-O1 -g -fno-omit-frame-pointer' ./configure "${configure_args[@]}" && \
          make "${make_args[@]}" && make install); \
      elif [[ "${variant}" == gcov ]]; then \
        (cd "${source_dir}" && CC=cc CFLAGS='-O0 -g --coverage' \
          LDFLAGS='--coverage' ./configure "${configure_args[@]}" && \
          make "${make_args[@]}" && make install); \
      else \
        (cd "${source_dir}" && CC=cc CFLAGS='-O2 -g' \
          ./configure "${configure_args[@]}" && make "${make_args[@]}" && make install); \
      fi; \
      test -x "${prefix}/sbin/dovecot"; \
      test -x "${prefix}/bin/doveadm"; \
      test -x "${prefix}/libexec/dovecot/imap"; \
      test -x "${prefix}/libexec/dovecot/imap-login"; \
    done; \
    python3 /home/ubuntu/experiments/prepare_seeds.py /tmp/seeds-generated \
      --manifest /tmp/seeds-manifest-generated.json; \
    diff -r /home/ubuntu/experiments/seeds /tmp/seeds-generated; \
    cmp /home/ubuntu/experiments/seeds-manifest.json /tmp/seeds-manifest-generated.json; \
    { \
      printf 'base_image=%s\n' 'ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214'; \
      printf 'ubuntu_snapshot=%s\n' "${UBUNTU_SNAPSHOT}"; \
      printf 'dovecot_commit=%s\n' "${DOVECOT_COMMIT}"; \
      printf 'dovecot_version=%s\n' "${DOVECOT_VERSION}"; \
      printf 'dovecot_archive_sha256=%s\n' "${DOVECOT_ARCHIVE_SHA256}"; \
      printf 'aflnet_commit=%s\n' "${AFLNET_COMMIT}"; \
      printf 'aflnet_archive_sha256=%s\n' "${AFLNET_ARCHIVE_SHA256}"; \
      printf 'make_opt=%s\n' "${MAKE_OPT}"; \
      printf 'aflnet_imap_patch_sha256='; sha256sum /tmp/aflnet-imap.patch | cut -d ' ' -f1; \
      printf 'imap_adapter_sha256='; sha256sum /tmp/imap_aflnet.c | cut -d ' ' -f1; \
      printf 'fault_probe_sha256='; sha256sum /tmp/fault_probe_server.c | cut -d ' ' -f1; \
      printf 'seeds_manifest_sha256='; sha256sum /home/ubuntu/experiments/seeds-manifest.json | cut -d ' ' -f1; \
      for variant in reference afl gcov; do \
        printf '%s_version=' "${variant}"; \
        "/home/ubuntu/experiments/dovecot-${variant}/sbin/dovecot" --version; \
      done; \
      cc --version | sed -n '1p'; clang --version | sed -n '1p'; \
      dpkg-query -W -f='${binary:Package}=${Version}\n' build-essential clang gcovr gettext \
        libpcre2-dev libssl-dev llvm llvm-dev make python3 sudo wget; \
    } > /home/ubuntu/experiments/build-versions.txt; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' | sort \
      > /home/ubuntu/experiments/package-manifest.txt

ENV PATH=/home/ubuntu/experiments/dovecot-reference/bin:/home/ubuntu/experiments/dovecot-reference/sbin:/home/ubuntu/aflnet:${PATH} \
    DOVECOT_REFERENCE_PREFIX=/home/ubuntu/experiments/dovecot-reference \
    DOVECOT_AFL_PREFIX=/home/ubuntu/experiments/dovecot-afl \
    DOVECOT_GCOV_PREFIX=/home/ubuntu/experiments/dovecot-gcov \
    DOVECOT_CONFIG=/workspace/dovecot.conf \
    IMAP_PORT=1143

EXPOSE 1143/tcp
