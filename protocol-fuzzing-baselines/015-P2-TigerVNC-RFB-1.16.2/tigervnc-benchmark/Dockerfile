FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG TIGERVNC_VERSION=1.16.2
ARG TIGERVNC_COMMIT=b555312d70d7ff017f866649a7e7167af4eb8fca
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ENV AFL_PATH=/opt/aflnet AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1
WORKDIR /work

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential ca-certificates cmake coreutils graphviz libgnutls28-dev libgraphviz-dev libjpeg-dev libpam0g-dev \
    libpixman-1-dev libx11-dev libxdamage-dev libxext-dev libxfixes-dev libxrandr-dev \
    libxrender-dev libxtst-dev pkg-config python3 x11-utils xvfb zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/tigervnc-b555312.tar.gz /tmp/tigervnc-b555312.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY source/aflnet-rfb-rdp.patch /tmp/aflnet-rfb-rdp.patch
COPY source/SHA256SUMS /tmp/SHA256SUMS
COPY seeds/ /work/seeds/
COPY tests/ /work/tests/
COPY run.sh smoke.py validate.sh capture-build.sh /work/

RUN set -eux; cd /tmp; sha256sum -c SHA256SUMS; \
    mkdir -p /src/tigervnc /opt/aflnet /opt/tigervnc/bin /work/build-evidence /work/results; \
    tar -xzf /tmp/tigervnc-b555312.tar.gz --strip-components=1 -C /src/tigervnc; \
    tar -xzf /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/aflnet.c /opt/aflnet/afl-fuzz.c; \
    patch -d /opt/aflnet -p1 < /tmp/aflnet-rfb-rdp.patch; \
    AFL_NO_X86=1 CFLAGS='-O3 -funroll-loops -Wall -D_GNU_SOURCE -include libgen.h -D_FORTIFY_SOURCE=2 -g -Wno-pointer-sign -Wno-unused-result -DTRUE=1 -DFALSE=0' \
      make -C /opt/aflnet -j2 afl-fuzz afl-gcc afl-showmap afl-as; \
    gcc -O1 -g -Wall -Wextra -Wno-pointer-sign -Wno-sign-compare -Wno-type-limits \
      -Wno-stringop-truncation -Wno-maybe-uninitialized -D_GNU_SOURCE -include libgen.h \
      -DTRUE=1 -DFALSE=0 -ffunction-sections -fdata-sections -I/opt/aflnet \
      /work/tests/aflnet-parser-tests.c /opt/aflnet/aflnet.c -Wl,--gc-sections \
      -o /tmp/aflnet-parser-tests; \
    /tmp/aflnet-parser-tests > /work/build-evidence/parser-tests.txt; \
    cmake -S /src/tigervnc -B /src/tigervnc-build \
      -DCMAKE_INSTALL_PREFIX=/opt/tigervnc -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_C_COMPILER=/opt/aflnet/afl-gcc -DCMAKE_CXX_COMPILER=/opt/aflnet/afl-g++ \
      -DBUILD_VIEWER=OFF -DBUILD_JAVA=OFF -DBUILD_WINVNC=0 -DENABLE_H264=OFF \
      -DENABLE_NLS=OFF -DENABLE_WAYLAND=OFF -DINSTALL_SYSTEMD_UNITS=OFF; \
    cmake --build /src/tigervnc-build -j2 --target x0vncserver; \
    install -m 0755 /src/tigervnc-build/unix/x0vncserver/x0vncserver /opt/tigervnc/bin/x0vncserver; \
    printf 'target_version=%s\ntarget_commit=%s\n' "${TIGERVNC_VERSION}" "${TIGERVNC_COMMIT}" > /work/build-evidence/build-lock.txt; \
    printf 'aflnet_commit=%s\nbase_image=%s\n' "${AFLNET_COMMIT}" 'ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852' >> /work/build-evidence/build-lock.txt; \
    printf 'target=x0vncserver RFB 3.8; local Xvfb display :1; loopback TCP port 5901; SecurityTypes=None\n' >> /work/build-evidence/build-lock.txt; \
    printf 'parser_patch_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /tmp/aflnet-rfb-rdp.patch | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_binary_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/aflnet/afl-fuzz | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'target_binary_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/tigervnc/bin/x0vncserver | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'compiler=' >> /work/build-evidence/build-lock.txt; gcc --version | head -1 >> /work/build-evidence/build-lock.txt; \
    cat /work/build-evidence/parser-tests.txt >> /work/build-evidence/build-lock.txt; \
    chmod +x /work/run.sh /work/validate.sh /work/capture-build.sh

ENTRYPOINT ["/bin/bash"]
