FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG SRS_VERSION=v6.0-r3
ARG SRS_COMMIT=9f6d88164c8608d80ac41264998e80b8076d5e43
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732

ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    autoconf automake bash bison build-essential ca-certificates coreutils cmake flex gcovr graphviz \
    libgraphviz-dev libssl-dev libtool make nasm patch perl pkg-config python3 unzip which yasm zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/srs-server-6.0-r3.tar.gz /tmp/srs-server-6.0-r3.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY source/aflnet-commit.txt /tmp/aflnet-commit.txt
COPY source/verification.txt /tmp/verification.txt
COPY source/SHA256SUMS /tmp/SHA256SUMS
COPY source-lock.json /work/source-lock.json
COPY rtmp_aflnet.c patch_aflnet_rtmp.py build_aflnet.sh rtmp-fuzz-helper.c rtmp_parser_test.c rtmp_proxy.py rtmp_protocol.py /work/
COPY rtmp.conf rtmp.dict rtmp_smoke.py replay_queue.py run.sh validate.sh capture-build.sh /work/
COPY seeds/ /work/seeds/

RUN set -eux; \
    cd /tmp; sha256sum -c SHA256SUMS; \
    mkdir -p /src/srs /opt/aflnet /work/build-evidence /work/results /work/srs-work; \
    tar -xzf /tmp/srs-server-6.0-r3.tar.gz --strip-components=1 -C /src/srs; \
    tar -xzf /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/afl-replay.c /opt/aflnet/aflnet-replay.c; \
    bash /work/build_aflnet.sh; \
    cd /src/srs/trunk; \
    ./configure --rtc=off --srt=off --hls=off --hds=off --http-api=off --http-server=off \
      --http-callback=off --dvr=off --transcode=on --ingest=off --stream-caster=off --stat=off \
      --ssl=on --sys-ssl=on --utest=off --extra-flags='-O0 -g --coverage -fprofile-abs-path' --extra-ldflags='--coverage'; \
    make -j2; \
    find /src/srs/trunk/objs -type d -exec chmod a+w {} +; \
    dpkg-query -W -f='${Package}=${Version}\n' > /work/build-evidence/ubuntu-packages.txt; \
    ./objs/srs -v > /work/build-evidence/srs-version.txt 2>&1; \
    grep -q '6.0.195' /work/build-evidence/srs-version.txt; \
    printf 'target_version=%s (release build %s)\n' "$SRS_VERSION" 'v6.0.195' > /work/build-evidence/build-lock.txt; \
    printf 'release_commit=%s\n' "$SRS_COMMIT" >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_commit=%s\n' "$AFLNET_COMMIT" >> /work/build-evidence/build-lock.txt; \
    printf 'builder_image=%s\n' 'ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852' >> /work/build-evidence/build-lock.txt; \
    printf 'target_binary_sha256=' > /work/build-evidence/srs-binary.sha256; sha256sum /src/srs/trunk/objs/srs >> /work/build-evidence/srs-binary.sha256; \
    printf 'protocol=RTMP v3; native GCC coverage; no transcode engines configured or exercised; optional RTC/SRT/HLS/HTTP listeners disabled\n' >> /work/build-evidence/build-lock.txt; \
    chmod +x /work/run.sh /work/validate.sh /work/capture-build.sh /work/rtmp_proxy.py /work/rtmp_smoke.py /work/replay_queue.py

WORKDIR /work
ENTRYPOINT ["/bin/bash"]
