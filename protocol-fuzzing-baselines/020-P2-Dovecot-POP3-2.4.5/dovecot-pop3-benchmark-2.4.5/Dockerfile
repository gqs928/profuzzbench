FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_OPT=-j2
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG DOVECOT_VERSION=2.4.5
ARG DOVECOT_ARCHIVE_SHA256=868c2686a61b5f8e00a3e4721789b1ab46e6528fd773a5fbed07a6ecba7731e6
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

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends ca-certificates && \
    sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends \
      autoconf automake bison build-essential ca-certificates clang flex gcovr gettext \
      git graphviz graphviz-dev libcap-dev libpcre2-32-0 libpcre2-dev libssl-dev \
      libtool llvm llvm-dev make netcat-openbsd patch perl pkg-config procps runit \
      python3 wget zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 ubuntu && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu
USER ubuntu
WORKDIR /home/ubuntu

COPY --chown=ubuntu:ubuntu source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY --chown=ubuntu:ubuntu source/dovecot-2.4.5.tar.gz /tmp/source/dovecot-2.4.5.tar.gz
COPY --chown=ubuntu:ubuntu source-checksums.sha256 /tmp/source-checksums.sha256
COPY --chown=ubuntu:ubuntu aflnet-pop3.patch pop3_aflnet.c parser-test.c pop3.dict \
  prepare_seeds.py prepare_maildir.py /tmp/
COPY --chown=ubuntu:ubuntu seeds/ /home/ubuntu/experiments/seeds/
COPY --chown=ubuntu:ubuntu source-lock.json ucd-checksums.sha256 dovecot.conf passwd seeds-manifest.json \
  /home/ubuntu/experiments/

RUN set -eu; \
    cd /tmp && sha256sum -c source-checksums.sha256; \
    mkdir -p "${AFLNET}" /tmp/dovecot-source "${WORKDIR}"; \
    tar -xzf /tmp/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C "${AFLNET}"; \
    tar -xzf /tmp/source/dovecot-2.4.5.tar.gz -C /tmp/dovecot-source --strip-components=1; \
    test "$(cat /tmp/dovecot-source/version.txt)" = "${DOVECOT_VERSION}"; \
    sed -i 's/\r$//' "${AFLNET}"/Makefile "${AFLNET}"/aflnet.h \
      "${AFLNET}"/afl-fuzz.c "${AFLNET}"/afl-replay.c "${AFLNET}"/aflnet-replay.c; \
    cp /tmp/pop3_aflnet.c "${AFLNET}/pop3_aflnet.c"; \
    git -C "${AFLNET}" apply --check /tmp/aflnet-pop3.patch; \
    git -C "${AFLNET}" apply /tmp/aflnet-pop3.patch; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    AFL_NO_X86=1 make -C "${AFLNET}" all "${make_args[@]}"; \
    AFL_NO_X86=1 make -C "${AFLNET}/llvm_mode" "${make_args[@]}"; \
    cc -O2 -Wall -Wextra -Werror -I"${AFLNET}" /tmp/parser-test.c \
      "${AFLNET}/pop3_aflnet.o" -o /tmp/parser-test; \
    /tmp/parser-test; \
    python3 /tmp/prepare_seeds.py /tmp/generated-seeds --username fuzzuser \
      --password dovecot-benchmark-pass --manifest /tmp/generated-seeds-manifest.json; \
    diff -r /home/ubuntu/experiments/seeds /tmp/generated-seeds; \
    cmp /home/ubuntu/experiments/seeds-manifest.json /tmp/generated-seeds-manifest.json; \
    for name in CaseFolding.txt CompositionExclusions.txt DerivedBidiClass.txt \
      DerivedCoreProperties.txt DerivedJoiningType.txt DerivedNormalizationProps.txt \
      emoji-data.txt GraphemeBreakProperty.txt GraphemeBreakTest.txt NormalizationTest.txt \
      PropertyValueAliases.txt PropList.txt Scripts.txt SpecialCasing.txt UnicodeData.txt \
      WordBreakProperty.txt IdnaMappingTable.txt IdnaTestV2.txt; do \
      wget -nv --tries=5 --waitretry=2 --timeout=30 --no-use-server-timestamps -O "/tmp/dovecot-source/src/lib/ucd/${name}" "https://dovecot.org/res/${name}"; \
    done; \
    (cd /tmp/dovecot-source/src/lib/ucd && sha256sum -c /home/ubuntu/experiments/ucd-checksums.sha256); \
    test -x /tmp/dovecot-source/configure; \
    for variant in reference afl gcov; do \
      cp -a /tmp/dovecot-source "${WORKDIR}/src-${variant}"; \
      source_dir="${WORKDIR}/src-${variant}"; prefix="${WORKDIR}/dovecot-${variant}"; \
      configure_args=(--prefix="${prefix}" --sysconfdir="${prefix}/etc" \
        --localstatedir="${prefix}/var" --with-rundir="${prefix}/var/run/dovecot" \
        --with-statedir="${prefix}/var/lib/dovecot" --with-ioloop=epoll \
        --with-notify=none --without-pam --without-bsdauth --without-gssapi \
        --without-ldap --without-sql --without-pgsql --without-mysql --without-sqlite \
        --without-cassandra --without-stemmer --without-textcat --without-icu \
        --without-solr --without-flatcurve --without-sodium --without-bzlib \
        --without-lz4 --without-zstd --without-libcap --with-systemd=no --without-lua); \
      while IFS= read -r source_subdir; do mkdir -p "${source_subdir}/.libs"; done \
        < <(find "${source_dir}/src" -type d -print); \
      if [[ "${variant}" == afl ]]; then \
        (cd "${source_dir}" && CC="${AFLNET}/afl-clang-fast" CFLAGS='-O1 -g -fno-omit-frame-pointer' \
          ./configure "${configure_args[@]}" && make "${make_args[@]}" && make install); \
      elif [[ "${variant}" == gcov ]]; then \
        (cd "${source_dir}" && CC=cc CFLAGS='-O0 -g --coverage' LDFLAGS='--coverage' \
          ./configure "${configure_args[@]}" && make "${make_args[@]}" && make install); \
      else \
        (cd "${source_dir}" && CC=cc CFLAGS='-O2 -g' ./configure "${configure_args[@]}" \
          && make "${make_args[@]}" && make install); \
      fi; \
      test -x "${prefix}/sbin/dovecot"; \
      test -x "${prefix}/libexec/dovecot/pop3"; \
      test -x "${prefix}/libexec/dovecot/pop3-login"; \
    done; \
    { \
      printf 'base_image=%s\n' 'ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214'; \
      printf 'ubuntu_snapshot=%s\n' "${UBUNTU_SNAPSHOT}"; \
      printf 'dovecot_version=%s\n' "${DOVECOT_VERSION}"; \
      printf 'dovecot_archive_sha256=%s\n' "${DOVECOT_ARCHIVE_SHA256}"; \
      printf 'aflnet_commit=%s\n' "${AFLNET_COMMIT}"; \
      printf 'aflnet_archive_sha256=%s\n' "${AFLNET_ARCHIVE_SHA256}"; \
      printf 'aflnet_pop3_patch_sha256='; sha256sum /tmp/aflnet-pop3.patch | cut -d ' ' -f1; \
      printf 'pop3_parser_sha256='; sha256sum /tmp/pop3_aflnet.c | cut -d ' ' -f1; \
      for variant in reference afl gcov; do printf '%s=' "${variant}_version"; "${WORKDIR}/dovecot-${variant}/sbin/dovecot" --version; done; \
      cc --version | sed -n '1p'; clang --version | sed -n '1p'; \
      dpkg-query -W -f='${binary:Package}=${Version}\n' build-essential clang gcovr gettext \
        libpcre2-dev libssl-dev llvm llvm-dev make python3 wget; \
    } > "${WORKDIR}/build-versions.txt"

USER root
RUN groupadd --system dovecot
COPY dovecot-pop3-runner.c /tmp/dovecot-pop3-runner.c
RUN /home/ubuntu/aflnet/afl-clang-fast -O1 -g -Wall -Wextra -Werror \
      -fno-omit-frame-pointer /tmp/dovecot-pop3-runner.c \
      -o /usr/local/sbin/dovecot-pop3-runner && \
    printf 'dovecot_pop3_runner_sha256=' >> /home/ubuntu/experiments/build-versions.txt && \
    sha256sum /tmp/dovecot-pop3-runner.c | cut -d ' ' -f1 \
      >> /home/ubuntu/experiments/build-versions.txt
COPY --chmod=0755 dovecot-root-launcher-runtime.sh /usr/local/sbin/dovecot-root-launcher
COPY --chmod=0755 clean.sh /usr/local/sbin/dovecot-clean-maildir

ENV PATH=/home/ubuntu/experiments/dovecot-reference/bin:/home/ubuntu/experiments/dovecot-reference/sbin:/home/ubuntu/aflnet:${PATH} \
    DOVECOT_REFERENCE_PREFIX=/home/ubuntu/experiments/dovecot-reference \
    DOVECOT_AFL_PREFIX=/home/ubuntu/experiments/dovecot-afl \
    DOVECOT_GCOV_PREFIX=/home/ubuntu/experiments/dovecot-gcov \
    POP3_PORT=1110

EXPOSE 1110/tcp
