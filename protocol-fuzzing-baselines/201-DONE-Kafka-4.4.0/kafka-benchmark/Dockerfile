FROM ubuntu:24.04@sha256:f610ab94648195aa356059f5b41d6085c9d4d903c072430cdd1af7bdb646106b

ARG DEBIAN_FRONTEND=noninteractive
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG KAFKA_COMMIT=1156b2752aaa28eafc0b4c4d387e63356793268d
ARG KAFKA_VERSION=4.4.0
ARG KAFKA_BINARY_SHA512=f5ceba8a265ab6bb2d68362b1f6859a95e15d60ef92ba83b43fdf065b557dc18e98d6383c15b9977320e25b3a2c8b6f11decb17b0fa6c0f163423793a0eb95cb
ARG KAFKA_SOURCE_SHA512=94e118d8e129017f25eb923f7f5e720368fad489bd6bb4ef57427f1ae61273356812c8c7ae0f36b013cb50855ca5b2bd2fc54de917b1c94051d4c709c6eacac7
ARG SCALA_VERSION=2.13
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d
ARG JACOCO_VERSION=0.8.13
ARG MAKE_OPT=-j1
ARG UBUNTU_CONFIG_DIGEST=sha256:69f919497cada9a8611f3de61df902d9f94bf20f84552ef5bd93125c38608ef9
ARG UBUNTU_MANIFEST_DIGEST=sha256:f610ab94648195aa356059f5b41d6085c9d4d903c072430cdd1af7bdb646106b

ENV DEBIAN_FRONTEND=noninteractive \
    WORKDIR=/home/ubuntu/experiments \
    AFLNET=/home/ubuntu/aflnet \
    AFL_PATH=/home/ubuntu/aflnet \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    KAFKA_HEAP_OPTS="-Xms256m -Xmx768m" \
    JAVA_TOOL_OPTIONS="-Djava.awt.headless=true"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# 所有软件包来自固定 Ubuntu 快照。首次安装 CA 时由 APT 的仓库签名和包哈希校验内容；
# CA 安装后再启用 HTTPS 证书校验，避免引入基础镜像之外的可变软件源包。
RUN rm -f /etc/apt/apt.conf.d/docker-clean && \
    find /etc/apt -type f \( -name 'sources.list' -o -name '*.sources' \) \
      -exec sed -i -E "s#https?://(archive|security)\\.ubuntu\\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${UBUNTU_SNAPSHOT}/#g" {} + && \
    apt-get update -o Acquire::Retries=5 -o Acquire::Check-Valid-Until=false \
      -o Acquire::https::Verify-Peer=false -o Acquire::https::Verify-Host=false && \
    apt-get install -y -o Acquire::Retries=5 -o Acquire::Check-Valid-Until=false \
      -o Acquire::https::Verify-Peer=false -o Acquire::https::Verify-Host=false \
      --no-install-recommends ca-certificates && \
    apt-get update -o Acquire::Retries=5 -o Acquire::Check-Valid-Until=false && \
    apt-get install -y -o Acquire::Retries=5 -o Acquire::Check-Valid-Until=false --no-install-recommends \
      ca-certificates curl git build-essential clang libclang-rt-18-dev openjdk-21-jdk \
      libgraphviz-dev python3 procps netcat-openbsd bash coreutils && \
    rm -rf /var/lib/apt/lists/*

# 依赖安装后再收紧 JVM 默认堆，避免改动固定快照安装层的缓存键。
ENV KAFKA_HEAP_OPTS="-Xms128m -Xmx384m" \
    JAVA_TOOL_OPTIONS="-Djava.awt.headless=true -XX:ActiveProcessorCount=1"

# 官方 Ubuntu 24.04 镜像预置 UID/GID 均为 1000 的 ubuntu 用户和用户组。
RUN test "$(id -u ubuntu)" = 1000 && test "$(id -g ubuntu)" = 1000

USER ubuntu
WORKDIR /home/ubuntu

COPY --chown=ubuntu:ubuntu aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY --chown=ubuntu:ubuntu aflnet-kafka.patch kafka_aflnet.c parser-test.c /tmp/
COPY --chown=ubuntu:ubuntu test-stubs/ /tmp/test-stubs/

# Ubuntu 24.04 的 Clang 18 已移除旧阈值参数；一并移除其 -mllvm 参数前缀。
RUN set -eu; \
    echo "${AFLNET_ARCHIVE_SHA256}  /tmp/aflnet.tar.gz" | sha256sum -c -; \
    mkdir -p "${AFLNET}"; \
    tar -xzf /tmp/aflnet.tar.gz -C "${AFLNET}"; \
    sed -i 's/\r$//' "${AFLNET}"/Makefile "${AFLNET}"/aflnet.h \
      "${AFLNET}"/afl-fuzz.c "${AFLNET}"/afl-replay.c \
      "${AFLNET}"/aflnet-replay.c; \
    sed -i '/"-mllvm"/d; /sanitizer-coverage-block-threshold/d' \
      "${AFLNET}/llvm_mode/afl-clang-fast.c"; \
    cp /tmp/kafka_aflnet.c "${AFLNET}/kafka_aflnet.c"; \
    git -C "${AFLNET}" apply --check /tmp/aflnet-kafka.patch; \
    git -C "${AFLNET}" apply /tmp/aflnet-kafka.patch; \
    read -r -a make_args <<< "${MAKE_OPT}"; \
    AFL_NO_X86=1 make -C "${AFLNET}" all "${make_args[@]}"; \
    AFL_TRACE_PC=1 AFL_NO_X86=1 make -C "${AFLNET}/llvm_mode" "${make_args[@]}"; \
    cc -O2 -Wall -Wextra -Werror -I"${AFLNET}" \
      /tmp/parser-test.c "${AFLNET}/kafka_aflnet.c" -o /tmp/parser-test; \
    /tmp/parser-test

# 使用 Apache 官方 4.4.0 二进制与源码发行归档，按 Apache 发布页公布的 SHA-512 校验。
# 发行二进制是被测 Broker；源码包仅用于对应 JaCoCo 行覆盖报告，不在本机 Gradle 编译 Kafka。
RUN set -eu; \
    mkdir -p "${WORKDIR}/kafka" "${WORKDIR}/kafka-source"; \
    curl -fL --retry 5 --retry-delay 2 \
      "https://downloads.apache.org/kafka/${KAFKA_VERSION}/kafka_2.13-${KAFKA_VERSION}.tgz" \
      -o /tmp/kafka-binary.tgz; \
    echo "${KAFKA_BINARY_SHA512}  /tmp/kafka-binary.tgz" | sha512sum -c -; \
    curl -fL --retry 5 --retry-delay 2 \
      "https://downloads.apache.org/kafka/${KAFKA_VERSION}/kafka-${KAFKA_VERSION}-src.tgz" \
      -o /tmp/kafka-source.tgz; \
    echo "${KAFKA_SOURCE_SHA512}  /tmp/kafka-source.tgz" | sha512sum -c -; \
    tar -xzf /tmp/kafka-binary.tgz -C "${WORKDIR}/kafka" --strip-components=1; \
    tar -xzf /tmp/kafka-source.tgz -C "${WORKDIR}/kafka-source" --strip-components=1; \
    test "$(sed -n 's/^version=//p' "${WORKDIR}/kafka-source/gradle.properties" | head -n1)" = "${KAFKA_VERSION}"; \
    "${WORKDIR}/kafka/bin/kafka-topics.sh" --version | tee /tmp/kafka-binary-version.txt; \
    grep -F "${KAFKA_VERSION}" /tmp/kafka-binary-version.txt; \
    printf 'kafka_binary_sha512=%s\nkafka_source_sha512=%s\n' \
      "${KAFKA_BINARY_SHA512}" "${KAFKA_SOURCE_SHA512}" > "${WORKDIR}/kafka-release-hashes.txt"

# JVMTI 覆盖代理在已校验的 Kafka 官方发行归档之后构建。
COPY --chown=ubuntu:ubuntu kafka_jvm_agent.c /tmp/kafka_jvm_agent.c

# Kafka JVM 会持续写共享覆盖图；每个样本终止 Broker 后再收集覆盖，避免异步后台线程拖延采集。
COPY --chown=ubuntu:ubuntu aflnet-kafka-fuzz.patch /tmp/aflnet-kafka-fuzz.patch
RUN set -eu; \
    git -C "${AFLNET}" apply --check /tmp/aflnet-kafka-fuzz.patch; \
    git -C "${AFLNET}" apply /tmp/aflnet-kafka-fuzz.patch; \
    AFL_NO_X86=1 make -C "${AFLNET}" afl-fuzz

# JaCoCo 导出 Java 行/分支覆盖；JVMTI 代理把 Kafka 方法边写入 AFLNet 共享覆盖图。
RUN set -eu; \
    mkdir -p /home/ubuntu/agents; \
    curl -fL --retry 5 --retry-delay 2 \
      "https://repo.maven.apache.org/maven2/org/jacoco/org.jacoco.agent/${JACOCO_VERSION}/org.jacoco.agent-${JACOCO_VERSION}-runtime.jar" \
      -o /home/ubuntu/agents/jacoco-agent.jar; \
    curl -fL --retry 5 --retry-delay 2 \
      "https://repo.maven.apache.org/maven2/org/jacoco/org.jacoco.cli/${JACOCO_VERSION}/org.jacoco.cli-${JACOCO_VERSION}-nodeps.jar" \
      -o /home/ubuntu/agents/jacococli.jar; \
    JAVA_HOME_REAL="$(dirname "$(dirname "$(readlink -f "$(command -v javac)")")")"; \
    cc -shared -fPIC -O2 -Wall -Wextra -Werror -pthread \
      -I"${JAVA_HOME_REAL}/include" -I"${JAVA_HOME_REAL}/include/linux" \
      -o /home/ubuntu/agents/libkafka_afl_agent.so /tmp/kafka_jvm_agent.c; \
    test -s /home/ubuntu/agents/libkafka_afl_agent.so

COPY --chown=ubuntu:ubuntu kafka-broker.properties kafka.dict \
     prepare_seeds.py start-kafka.sh clean.sh prepare-cluster.sh \
     protocol_smoke.py parser-test.c kafka_aflnet.c kafka_jvm_agent.c \
     aflnet-kafka.patch aflnet-kafka-fuzz.patch seeds-manifest.json source-lock.json \
     /home/ubuntu/experiments/
COPY --chown=ubuntu:ubuntu seeds/ /home/ubuntu/experiments/seeds/
COPY --chown=ubuntu:ubuntu fault_probe_server.c fault-probe.sh fault-probe-replay.py \
     kafka_launcher.c \
     /home/ubuntu/experiments/

# AFLNet 要求目标是插桩 ELF；启动器随后 exec 负责快照复位的脚本。
RUN set -eu; \
    chmod +x "${WORKDIR}"/*.sh; \
    mkdir -p "${WORKDIR}/results"; \
    "${AFLNET}/afl-clang-fast" -O2 -g -Wall -Wextra -Werror \
      -o "${WORKDIR}/kafka-launcher" "${WORKDIR}/kafka_launcher.c"; \
    "${AFLNET}/afl-clang-fast" -O1 -g -Wall -Wextra -Werror \
      -o /tmp/fault-probe-build-check "${WORKDIR}/fault_probe_server.c"; \
    rm -f /tmp/fault-probe-build-check; \
    python3 "${WORKDIR}/prepare_seeds.py" /tmp/kafka-seeds-check \
      /tmp/kafka-seeds-check.json; \
    diff -r "${WORKDIR}/seeds" /tmp/kafka-seeds-check; \
    cmp "${WORKDIR}/seeds-manifest.json" /tmp/kafka-seeds-check.json; \
    bash "${WORKDIR}/prepare-cluster.sh"; \
    { \
      printf 'base_image=ubuntu:24.04\n'; \
      printf 'base_image_config_digest=%s\nbase_image_amd64_manifest_digest=%s\n' \
        "${UBUNTU_CONFIG_DIGEST}" "${UBUNTU_MANIFEST_DIGEST}"; \
      printf 'ubuntu_snapshot=%s\n' "${UBUNTU_SNAPSHOT}"; \
      printf 'kafka_version=%s\nkafka_commit=%s\n' "${KAFKA_VERSION}" "${KAFKA_COMMIT}"; \
      printf 'kafka_distribution=Apache official 4.4.0 binary archive; no local Gradle compile\n'; \
      printf 'scala_version=%s\n' "${SCALA_VERSION}"; \
      printf 'aflnet_commit=%s\naflnet_archive_sha256=%s\n' "${AFLNET_COMMIT}" "${AFLNET_ARCHIVE_SHA256}"; \
      printf 'aflnet_kafka_patch_sha256='; sha256sum /tmp/aflnet-kafka.patch | cut -d ' ' -f1; \
      printf 'aflnet_kafka_fuzz_patch_sha256='; sha256sum "${WORKDIR}/aflnet-kafka-fuzz.patch" | cut -d ' ' -f1; \
      printf 'kafka_parser_sha256='; sha256sum "${WORKDIR}/kafka_aflnet.c" | cut -d ' ' -f1; \
      printf 'jvm_agent_sha256='; sha256sum /home/ubuntu/agents/libkafka_afl_agent.so | cut -d ' ' -f1; \
      printf 'jacoco_version=%s\n' "${JACOCO_VERSION}"; \
      printf 'build_variants=reference+kafka-jvm-method-coverage+JaCoCo\n'; \
      printf 'aflnet_instrumentation=LLVM trace-pc-guard\n'; \
      printf 'kafka_jvm_coverage=KafkaApis-request-handler-method-presence-bitmap;call-frequency-not-counted\n'; \
      printf 'target_launcher=aflnet_instrumented_elf_exec_wrapper\n'; \
      printf 'cpu_limits=native_build_single_worker;java_active_processor_count=1;runtime_docker_cpu_default=1\n'; \
      printf 'memory_limits=broker_heap_max=384m;runtime_docker_memory=1g;runtime_swap=disabled\n'; \
      printf 'build_host_min_available_memory_mib=1024\n'; \
      java -version 2>&1 | sed -n '1,3p'; \
      clang --version | sed -n '1p'; \
      cat "${WORKDIR}/kafka-release-hashes.txt"; \
    } > "${WORKDIR}/build-versions.txt"; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' | sort > "${WORKDIR}/package-manifest.txt"; \
    cd "${WORKDIR}"; \
      sha256sum kafka-broker.properties kafka.dict prepare_seeds.py kafka_launcher.c start-kafka.sh \
      kafka_aflnet.c kafka_jvm_agent.c start-kafka.sh aflnet-kafka.patch aflnet-kafka-fuzz.patch \
      parser-test.c source-lock.json \
      seeds/* seeds-manifest.json > source-checksums.sha256

ENV PATH=/home/ubuntu/aflnet:/home/ubuntu/experiments/kafka/bin:${PATH} \
    KAFKA_HOME=/home/ubuntu/experiments/kafka \
    KAFKA_SOURCE=/home/ubuntu/experiments/kafka-source \
    KAFKA_AFL_AGENT=/home/ubuntu/agents/libkafka_afl_agent.so \
    JACOCO_AGENT=/home/ubuntu/agents/jacoco-agent.jar \
    JACOCO_CLI=/home/ubuntu/agents/jacococli.jar \
    KAFKA_CONFIG=/home/ubuntu/experiments/kafka-broker.properties \
    KAFKA_SNAPSHOT=/home/ubuntu/experiments/kafka-data-snapshot \
    KAFKA_DATA=/home/ubuntu/experiments/kafka-data

WORKDIR /home/ubuntu/experiments
