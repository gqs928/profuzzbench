FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG ZLM_COMMIT=fb3265725f0880da1f52a3cc6e6eb04bbc327fa3
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 AFL_NO_UI=1
WORKDIR /work

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    bash build-essential ca-certificates cmake coreutils gcovr graphviz libgraphviz-dev \
    libsqlite3-dev libssl-dev pkg-config python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/ZLMediaKit-fb326572.tar.gz /tmp/ZLMediaKit-fb326572.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY source/aflnet-commit.txt /tmp/aflnet-commit.txt
COPY source/COMPONENTS.txt /tmp/COMPONENTS.txt
COPY source/SHA256SUMS /tmp/SHA256SUMS
COPY source-lock.json /work/source-lock.json
COPY rtmp_aflnet.c patch_aflnet_rtmp.py build_aflnet.sh rtmp-fuzz-helper.c rtmp_parser_test.c rtmp_proxy.py rtmp_protocol.py /work/
COPY config.ini normalize_config.py rtmp_smoke.py replay_queue.py run.sh validate.sh capture-build.sh /work/
COPY rtmp.dict /work/rtmp.dict
COPY seeds/ /work/seeds/

RUN set -eux; \
    cd /tmp; sha256sum -c SHA256SUMS; test "$(cat /tmp/aflnet-commit.txt)" = "$AFLNET_COMMIT"; \
    mkdir -p /src/ZLMediaKit /src/ZLMediaKit-build /opt/aflnet /opt/zlmediakit /work/build-evidence /work/results; \
    tar -xzf /tmp/ZLMediaKit-fb326572.tar.gz --strip-components=1 -C /src/ZLMediaKit; \
    tar -xzf /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/aflnet.c /opt/aflnet/afl-fuzz.c /opt/aflnet/afl-replay.c /opt/aflnet/aflnet-replay.c; \
    bash /work/build_aflnet.sh

RUN set -eux; \
    cmake -S /src/ZLMediaKit -B /src/ZLMediaKit-build \
      -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ \
      -DCMAKE_C_FLAGS='-O0 -g --coverage -fprofile-abs-path' \
      -DCMAKE_CXX_FLAGS='-O0 -g --coverage -fprofile-abs-path -I/src/ZLMediaKit/3rdpart/media-server/libflv/include' \
      -DCMAKE_EXE_LINKER_FLAGS='--coverage' -DCMAKE_SHARED_LINKER_FLAGS='--coverage' \
      -DBUILD_SHARED_LIBS=OFF -DENABLE_SERVER=ON -DENABLE_OPENSSL=ON -DENABLE_API=OFF \
      -DENABLE_PLAYER=OFF -DENABLE_HLS=OFF -DENABLE_MP4=ON -DENABLE_RTPPROXY=OFF \
      -DENABLE_SRT=OFF -DENABLE_SCTP=OFF -DENABLE_WEBRTC=OFF -DENABLE_TESTS=OFF \
      -DENABLE_OBJCOPY=OFF -DDISABLE_REPORT=ON; \
    cmake --build /src/ZLMediaKit-build -j2 --target MediaServer; \
    find /src/ZLMediaKit-build -type d -exec chmod a+w {} +; \
    install -m 0755 /src/ZLMediaKit/release/linux/Debug/MediaServer /opt/zlmediakit/MediaServer; \
    install -m 0644 /src/ZLMediaKit/default.pem /opt/zlmediakit/default.pem; \
    install -d /opt/zlmediakit/log /opt/zlmediakit/www/snap /opt/zlmediakit/ffmpeg /opt/zlmediakit/objs; \
    chmod 0777 /opt/zlmediakit/log /opt/zlmediakit/www /opt/zlmediakit/www/snap /opt/zlmediakit/ffmpeg /opt/zlmediakit/objs; \
    python3 /work/normalize_config.py /work/config.ini; \
    printf 'target_version=master snapshot\ntarget_commit=%s\n' "$ZLM_COMMIT" > /work/build-evidence/zlm-version.txt; \
    printf 'target_version=master snapshot\ntarget_commit=%s\nbase_image=ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852\naflnet_commit=%s\n' "$ZLM_COMMIT" "$AFLNET_COMMIT" > /work/build-evidence/build-lock.txt; \
    printf 'target=MediaServer RTMP; native GCC coverage; RTMP TCP 1935; dynamic C2 bridge TCP 1936\nruntime_writable_dirs=/opt/zlmediakit/log,/opt/zlmediakit/www,/opt/zlmediakit/ffmpeg,/opt/zlmediakit/objs\n' >> /work/build-evidence/build-lock.txt; \
    printf 'target_binary_sha256=' > /work/build-evidence/zlm-binary.sha256; sha256sum /opt/zlmediakit/MediaServer >> /work/build-evidence/zlm-binary.sha256; \
    printf 'aflnet_binary_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/aflnet/afl-fuzz | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    dpkg-query -W -f='${binary:Package}=${Version}\n' | sort > /work/build-evidence/ubuntu-packages.txt; \
    chmod +x /work/run.sh /work/validate.sh /work/capture-build.sh /work/rtmp_proxy.py /work/rtmp_smoke.py /work/replay_queue.py

ENTRYPOINT ["/bin/bash"]
