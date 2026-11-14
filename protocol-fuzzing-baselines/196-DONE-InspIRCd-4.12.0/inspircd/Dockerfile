FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214

ARG DEBIAN_FRONTEND=noninteractive
ARG MAKE_OPT=-j1
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG AFLNET_REF=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG INSPIRCD_REF=78159a35a6dba909c654a96ae92d8cb3340c8646
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d
ARG INSPIRCD_ARCHIVE_SHA256=5eefae1428d2e8b072c530cb01a1095a811927d63749d8c073c8044842e9c214

ENV DEBIAN_FRONTEND=noninteractive \
    WORKDIR=/home/ubuntu/experiments \
    AFLNET=/home/ubuntu/aflnet \
    AFL_PATH=/home/ubuntu/aflnet \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    ASAN_OPTIONS=abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1

# Bootstrap CA roots from Ubuntu's default HTTP mirror before switching to the
# immutable dated snapshot. This avoids the empty-CA-store TLS failure.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends ca-certificates && \
    sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 && \
    apt-get install -y -o Acquire::Retries=5 --no-install-recommends \
      autoconf automake build-essential clang git gcovr graphviz graphviz-dev \
      libssl-dev llvm llvm-dev make perl pkg-config procps python3 strace zlib1g-dev

RUN groupadd --gid 1000 ubuntu && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu

USER ubuntu
WORKDIR /home/ubuntu

COPY --chown=ubuntu:ubuntu aflnet-irc.patch inspircd-shutdown.patch irc_aflnet.c parser-test.c normalize_source.py \
    aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz \
    inspircd-78159a35a6dba909c654a96ae92d8cb3340c8646.tar.gz /tmp/irc-adapter/
RUN echo "${AFLNET_ARCHIVE_SHA256}  /tmp/irc-adapter/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz" | sha256sum -c - && \
    echo "${INSPIRCD_ARCHIVE_SHA256}  /tmp/irc-adapter/inspircd-78159a35a6dba909c654a96ae92d8cb3340c8646.tar.gz" | sha256sum -c - && \
    git init "${AFLNET}" && \
    tar -xzf /tmp/irc-adapter/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C "${AFLNET}" && \
    sed -i 's/\r$//' "${AFLNET}/Makefile" "${AFLNET}/aflnet.h" \
      "${AFLNET}/afl-fuzz.c" "${AFLNET}/afl-replay.c" "${AFLNET}/aflnet-replay.c" && \
    cp /tmp/irc-adapter/irc_aflnet.c "${AFLNET}/irc_aflnet.c" && \
    git -C "${AFLNET}" apply --unidiff-zero --check /tmp/irc-adapter/aflnet-irc.patch && \
    git -C "${AFLNET}" apply --unidiff-zero /tmp/irc-adapter/aflnet-irc.patch && \
    cd "${AFLNET}" && \
    env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin make clean all "${MAKE_OPT}" && \
    cd llvm_mode && env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin make "${MAKE_OPT}" && \
    cd "${AFLNET}" && make irc_aflnet.o && \
    cc -O2 -I"${AFLNET}" /tmp/irc-adapter/parser-test.c irc_aflnet.o -o /tmp/irc-parser-test && \
    /tmp/irc-parser-test

ENV PATH=/home/ubuntu/.local/bin:${PATH}

COPY --chown=ubuntu:ubuntu inspircd.conf motd.txt irc.dict prepare_seeds.py /tmp/irc-adapter/
COPY --chown=ubuntu:ubuntu seeds/ /tmp/irc-adapter/seeds/
RUN mkdir -p "${WORKDIR}/in-irc" "${WORKDIR}/inspircd-reference" \
             "${WORKDIR}/inspircd-afl" "${WORKDIR}/inspircd-gcov" && \
    python3 /tmp/irc-adapter/prepare_seeds.py /tmp/irc-adapter/seeds "${WORKDIR}/in-irc" && \
    cp /tmp/irc-adapter/irc.dict "${WORKDIR}/irc.dict" && \
    cp /tmp/irc-adapter/motd.txt "${WORKDIR}/motd.txt"

# Build clean reference, ASAN/AFL-instrumented, and gcov targets from the same
# immutable InspIRCd source commit. Only compiler/linker flags differ.
RUN set -eu; \
    for target in inspircd-reference inspircd-afl inspircd-gcov; do \
      git init "${WORKDIR}/${target}"; \
      tar -xzf /tmp/irc-adapter/inspircd-78159a35a6dba909c654a96ae92d8cb3340c8646.tar.gz -C "${WORKDIR}/${target}" --strip-components=1; \
      python3 /tmp/irc-adapter/normalize_source.py "${WORKDIR}/${target}"; \
      git -C "${WORKDIR}/${target}" apply --check /tmp/irc-adapter/inspircd-shutdown.patch; \
      git -C "${WORKDIR}/${target}" apply /tmp/irc-adapter/inspircd-shutdown.patch; \
    done; \
    for target in inspircd-reference inspircd-afl inspircd-gcov; do \
      cd "${WORKDIR}/${target}"; \
      case "${target}" in \
        inspircd-reference) compiler=c++; cxxflags='-O2 -g'; ldflags='';; \
        inspircd-afl) compiler="${AFLNET}/afl-clang-fast++"; cxxflags='-O1 -g -fno-omit-frame-pointer'; ldflags='';; \
        inspircd-gcov) compiler=c++; cxxflags='-O0 -g --coverage'; ldflags='--coverage';; \
      esac; \
      CXX="${compiler}" CXXFLAGS="${cxxflags}" LDFLAGS="${ldflags}" \
        ./configure --disable-auto-extras --disable-interactive --disable-ownership; \
      CXX="${compiler}" CXXFLAGS="${cxxflags}" LDFLAGS="${ldflags}" \
        AFL_USE_ASAN=1 make "${MAKE_OPT}"; \
      CXX="${compiler}" CXXFLAGS="${cxxflags}" LDFLAGS="${ldflags}" \
        AFL_USE_ASAN=1 make "${MAKE_OPT}" install; \
      mkdir -p run/conf run/data run/logs; \
      cp /tmp/irc-adapter/inspircd.conf run/conf/inspircd.conf; \
      cp /tmp/irc-adapter/motd.txt run/conf/motd.txt; \
    done

RUN { \
      printf 'base_image=ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214\n'; \
      printf 'ubuntu_snapshot=%s\n' "${UBUNTU_SNAPSHOT}"; \
      printf 'aflnet_commit=%s\n' "${AFLNET_REF}"; \
      printf 'aflnet_source_archive_sha256=%s\n' "$(sha256sum /tmp/irc-adapter/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz | cut -d ' ' -f1)"; \
      printf 'aflnet_irc_patch_sha256=%s\n' "$(sha256sum /tmp/irc-adapter/aflnet-irc.patch | cut -d ' ' -f1)"; \
      printf 'irc_parser_sha256=%s\n' "$(sha256sum /tmp/irc-adapter/irc_aflnet.c | cut -d ' ' -f1)"; \
      printf 'parser_test_sha256=%s\n' "$(sha256sum /tmp/irc-adapter/parser-test.c | cut -d ' ' -f1)"; \
      printf 'inspircd_source_normalizer_sha256=%s\n' "$(sha256sum /tmp/irc-adapter/normalize_source.py | cut -d ' ' -f1)"; \
      printf 'inspircd_commit=%s\n' "${INSPIRCD_REF}"; \
      printf 'inspircd_source_archive_sha256=%s\n' "$(sha256sum /tmp/irc-adapter/inspircd-78159a35a6dba909c654a96ae92d8cb3340c8646.tar.gz | cut -d ' ' -f1)"; \
      printf 'inspircd_shutdown_patch_sha256=%s\n' "$(sha256sum /tmp/irc-adapter/inspircd-shutdown.patch | cut -d ' ' -f1)"; \
      printf 'inspircd_version='; "${WORKDIR}/inspircd-afl/run/bin/inspircd" -v; \
      dpkg-query -W -f='${binary:Package}=${Version}\n' autoconf automake build-essential ca-certificates clang gcovr git llvm llvm-dev make perl python3; \
    } > "${WORKDIR}/build-versions.txt"

EXPOSE 6667/tcp
CMD ["/home/ubuntu/experiments/inspircd-afl/run/bin/inspircd", "-F", "-L", "-P", "-c", "/home/ubuntu/experiments/inspircd-afl/run/conf/inspircd.conf"]
