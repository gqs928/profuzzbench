FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG ZLM_VERSION=fb326572-snapshot
ARG ZLM_COMMIT=fb3265725f0880da1f52a3cc6e6eb04bbc327fa3
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ENV AFL_PATH=/opt/aflnet AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1
WORKDIR /work

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential ca-certificates cmake coreutils graphviz libgraphviz-dev libssl-dev libsqlite3-dev pkg-config \
    python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/ZLMediaKit-fb326572.tar.gz /tmp/ZLMediaKit-fb326572.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY source/SHA256SUMS /tmp/SHA256SUMS
COPY config/config.ini /work/config.ini
COPY seeds/ /work/seeds/
COPY run.sh smoke.py validate.sh capture-build.sh normalize_config.py target-wrapper.sh /work/

RUN set -eux; cd /tmp; sha256sum -c SHA256SUMS; \
    mkdir -p /src/ZLMediaKit /opt/aflnet /opt/zlmediakit /work/build-evidence /work/results; \
    tar -xzf /tmp/ZLMediaKit-fb326572.tar.gz --strip-components=1 -C /src/ZLMediaKit; \
    tar -xzf /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/aflnet.c /opt/aflnet/afl-fuzz.c; \
    AFL_NO_X86=1 CFLAGS='-O3 -funroll-loops -Wall -D_GNU_SOURCE -include libgen.h -D_FORTIFY_SOURCE=2 -g -Wno-pointer-sign -Wno-unused-result -DTRUE=1 -DFALSE=0' \
      make -C /opt/aflnet -j2 afl-fuzz afl-gcc afl-showmap afl-as

RUN set -eux; \
    cmake -S /src/ZLMediaKit -B /src/ZLMediaKit-build \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_C_COMPILER=/opt/aflnet/afl-gcc \
      -DCMAKE_CXX_COMPILER=/opt/aflnet/afl-g++ -DCMAKE_C_FLAGS='-O1 -g' \
      -DCMAKE_CXX_FLAGS='-O1 -g -I/src/ZLMediaKit/3rdpart/media-server/libflv/include' -DBUILD_SHARED_LIBS=OFF -DENABLE_SERVER=ON \
      -DENABLE_OPENSSL=ON -DENABLE_API=OFF -DENABLE_PLAYER=OFF -DENABLE_HLS=OFF \
      -DENABLE_MP4=ON -DENABLE_SRT=OFF -DENABLE_SCTP=OFF -DENABLE_WEBRTC=OFF \
      -DENABLE_TESTS=OFF -DENABLE_OBJCOPY=OFF -DDISABLE_REPORT=ON; \
    cmake --build /src/ZLMediaKit-build -j1 --target MediaServer

RUN set -eux; \
    install -m 0755 /src/ZLMediaKit/release/linux/RelWithDebInfo/MediaServer /opt/zlmediakit/MediaServer; \
    install -m 0644 /src/ZLMediaKit/default.pem /opt/zlmediakit/default.pem; \
    install -d /work/www /work/logs; \
    python3 /work/normalize_config.py /work/config.ini; \
    printf 'target_version=%s\ntarget_commit=%s\n' "${ZLM_VERSION}" "${ZLM_COMMIT}" > /work/build-evidence/build-lock.txt; \
    printf 'aflnet_commit=%s\nbase_image=%s\n' "${AFLNET_COMMIT}" 'ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852' >> /work/build-evidence/build-lock.txt; \
    printf 'submodule_ZLToolKit=%s\nsubmodule_jsoncpp=%s\nsubmodule_media-server=%s\nsubmodule_pybind11=%s\nsubmodule_webassist=%s\n' \
      'd7d601200f65f3111dbf9d20ed7f14d2654bbd6e' 'ca98c98457b1163cca1f7d8db62827c115fec6d1' \
      '21c4451ff2e4c4bb1c817e606c8b4e5deac1e719' 'ed5057ded698e305210269dafa57574ecf964483' \
      '6689195ac89462d40accd88f13dfde58902da57b' >> /work/build-evidence/build-lock.txt; \
    printf 'target=MediaServer RTSP; loopback TCP 8554; all other listener ports disabled; telemetry disabled\nfeature=ENABLE_MP4 linked for bundled ext-codec symbols; media payload profile out of scope\n' >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_binary_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/aflnet/afl-fuzz | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'target_binary_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/zlmediakit/MediaServer | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'compiler=' >> /work/build-evidence/build-lock.txt; gcc --version | head -1 >> /work/build-evidence/build-lock.txt; \
    chmod +x /work/run.sh /work/validate.sh /work/capture-build.sh /work/target-wrapper.sh

ENTRYPOINT ["/bin/bash"]
