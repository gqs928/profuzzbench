FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG DEBIAN_FRONTEND=noninteractive
ARG TGT_VERSION=1.0.98
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG TGT_SHA256=1167005b20f18a3a4c6171e309156e8ac6d0ccc1c2a7687baf605764f473fc94
ARG AFLNET_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV DEBIAN_FRONTEND=noninteractive \
    WORKDIR=/opt/benchmark \
    AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_NO_UI=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    TGT_REFERENCE_PREFIX=/opt/tgt-reference \
    TGT_AFL_PREFIX=/opt/tgt-afl \
    TGT_GCOV_PREFIX=/opt/tgt-gcov \
    TGT_IPC_SOCKET=/tmp/tgt-benchmark-ipc

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential ca-certificates graphviz libaio-dev libgraphviz-dev \
      python3 time coreutils procps && \
    rm -rf /var/lib/apt/lists/*

COPY source/tgt-v1.0.98.tar.gz /tmp/tgt.tar.gz
COPY source/aflnet.tar.gz /tmp/aflnet.tar.gz
COPY iscsi_aflnet.c parser-test.c patch_aflnet.py protocol_client.py \
     tgt-runner.c start-target.sh smoke.sh run.sh validate.sh iscsi.dict /opt/benchmark/

RUN set -eu; \
    echo "${TGT_SHA256}  /tmp/tgt.tar.gz" | sha256sum -c -; \
    echo "${AFLNET_SHA256}  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    mkdir -p /opt/aflnet /tmp/tgt-source; \
    tar -xzf /tmp/aflnet.tar.gz -C /opt/aflnet; \
    tar -xzf /tmp/tgt.tar.gz -C /tmp/tgt-source --strip-components=1; \
    python3 /opt/benchmark/patch_aflnet.py /opt/aflnet /opt/benchmark/iscsi_aflnet.c; \
    make -C /opt/aflnet -j2 all; \
    cc -O2 -Wall -Wextra -Werror -I/opt/aflnet \
      /opt/benchmark/parser-test.c /opt/aflnet/iscsi_aflnet.o -o /tmp/parser-test; \
    /tmp/parser-test; \
    for variant in reference afl gcov; do \
      mkdir -p "/opt/tgt-${variant}"; \
      cp -a /tmp/tgt-source/. "/opt/tgt-${variant}/src"; \
      cd "/opt/tgt-${variant}/src/usr"; \
      if [[ "${variant}" == afl ]]; then \
        AFL_PATH=/opt/aflnet CC=/opt/aflnet/afl-gcc \
          make -j2 VERSION="${TGT_VERSION}" PREFIX="/opt/tgt-${variant}"; \
      elif [[ "${variant}" == gcov ]]; then \
        CC='cc --coverage' CFLAGS='-O0 -g' \
          make -j2 VERSION="${TGT_VERSION}" PREFIX="/opt/tgt-${variant}"; \
      else \
        CC=cc CFLAGS='-O2 -g' make -j2 VERSION="${TGT_VERSION}" PREFIX="/opt/tgt-${variant}"; \
      fi; \
      make install VERSION="${TGT_VERSION}" PREFIX="/opt/tgt-${variant}"; \
      test -x "/opt/tgt-${variant}/sbin/tgtd"; \
      test -x "/opt/tgt-${variant}/sbin/tgtadm"; \
    done; \
    AFL_PATH=/opt/aflnet /opt/aflnet/afl-gcc -std=c11 -O2 -Wall -Wextra -Werror \
      /opt/benchmark/tgt-runner.c -o /opt/benchmark/tgt-runner; \
    { \
      printf 'base_image=%s\n' 'ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852'; \
      printf 'tgt_version=%s\n' "${TGT_VERSION}"; \
      printf 'tgt_archive_sha256=%s\n' "${TGT_SHA256}"; \
      printf 'aflnet_commit=%s\n' "${AFLNET_COMMIT}"; \
      printf 'aflnet_archive_sha256=%s\n' "${AFLNET_SHA256}"; \
      printf 'iscsi_adapter_sha256='; sha256sum /opt/benchmark/iscsi_aflnet.c | cut -d ' ' -f1; \
      printf 'protocol_client_sha256='; sha256sum /opt/benchmark/protocol_client.py | cut -d ' ' -f1; \
      printf 'tgt_runner_sha256='; sha256sum /opt/benchmark/tgt-runner.c | cut -d ' ' -f1; \
      for variant in reference afl gcov; do \
        printf '%s=' "${variant}"; "/opt/tgt-${variant}/sbin/tgtd" -V; \
      done; \
      cc --version | sed -n '1p'; \
      dpkg-query -W -f='${binary:Package}=${Version}\n' build-essential graphviz \
        libaio-dev libgraphviz-dev make python3; \
    } > /opt/benchmark/build-versions.txt; \
    rm -rf /tmp/tgt-source /tmp/aflnet.tar.gz /tmp/tgt.tar.gz /tmp/parser-test

WORKDIR /opt/benchmark
CMD ["bash"]
