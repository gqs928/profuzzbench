FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG XRDP_VERSION=0.10.6.1
ARG XRDP_COMMIT=80c52879fead585d6347df5b3c587718adf8f5a5
ARG LIBPAINTER_COMMIT=2255b3865e7b89afcbd2c310241d54dfa787b63e
ARG LIBRFXCODEC_COMMIT=c6b41afa6986d5e6df18778a342b407cae40e1b5
ARG ULALACA_COMMIT=f683d173a3feaa41c170d4d9ab572bdb60c03d7d
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ENV AFL_PATH=/opt/aflnet AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 LD_LIBRARY_PATH=/opt/xrdp/lib:/opt/xrdp/lib/xrdp
WORKDIR /work

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    autoconf automake build-essential ca-certificates coreutils graphviz libgraphviz-dev libjpeg-dev libpam0g-dev \
    libpixman-1-dev libssl-dev libtool libx11-dev libxfixes-dev libxkbfile-dev \
    libxrandr-dev nasm pkg-config python3 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY source/xrdp-80c5287.tar.gz /tmp/xrdp-80c5287.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY source/aflnet-rfb-rdp.patch /tmp/aflnet-rfb-rdp.patch
COPY source/SHA256SUMS /tmp/SHA256SUMS
COPY seeds/ /work/seeds/
COPY tests/ /work/tests/
COPY run.sh smoke.py validate.sh capture-build.sh /work/
COPY xrdp-fuzz-helper.c /tmp/xrdp-fuzz-helper.c

RUN set -eux; cd /tmp; sha256sum -c SHA256SUMS; \
    mkdir -p /src/xrdp /opt/aflnet /opt/xrdp /work/build-evidence /work/results /etc/xrdp /run/xrdp; \
    tar -xzf /tmp/xrdp-80c5287.tar.gz --strip-components=1 -C /src/xrdp; \
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
    cd /src/xrdp; ./bootstrap; \
    CC=/opt/aflnet/afl-gcc CXX=/opt/aflnet/afl-g++ CFLAGS='-O1 -g' CXXFLAGS='-O1 -g' \
      ./configure --prefix=/opt/xrdp --sysconfdir=/etc --localstatedir=/var --runstatedir=/run \
      --with-socketdir=/run/xrdp --with-systemdsystemunitdir=no --enable-pam --enable-pixman; \
    make -j2; make install; \
    if [ ! -s /etc/xrdp/rsakeys.ini ]; then /opt/xrdp/bin/xrdp-keygen xrdp /etc/xrdp/rsakeys.ini 2048; fi; \
    AFL_QUIET=1 AFL_PATH=/opt/aflnet /opt/aflnet/afl-gcc -O2 -g -Wall -Wextra -Werror /tmp/xrdp-fuzz-helper.c -o /opt/aflnet/xrdp-fuzz-helper; \
    cp /src/xrdp/xrdp/xrdp.ini.in /work/xrdp.ini; \
    sed -i -e 's/^fork=true$/fork=false/' -e 's/^port=3389$/port=3390/' \
      -e 's/^security_layer=negotiate$/security_layer=rdp/' -e 's/^crypt_level=high$/crypt_level=low/' /work/xrdp.ini; \
    printf 'target_version=%s\ntarget_commit=%s\n' "${XRDP_VERSION}" "${XRDP_COMMIT}" > /work/build-evidence/build-lock.txt; \
    printf 'aflnet_commit=%s\nbase_image=%s\n' "${AFLNET_COMMIT}" 'ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852' >> /work/build-evidence/build-lock.txt; \
    printf 'submodule_libpainter=%s\nsubmodule_librfxcodec=%s\nsubmodule_ulalaca=%s\n' \
      "${LIBPAINTER_COMMIT}" "${LIBRFXCODEC_COMMIT}" "${ULALACA_COMMIT}" >> /work/build-evidence/build-lock.txt; \
    printf 'target=xrdp RDP/X.224 negotiation on loopback TCP 3390, fork=false, security_layer=rdp\n' >> /work/build-evidence/build-lock.txt; \
    printf 'parser_patch_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /tmp/aflnet-rfb-rdp.patch | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_binary_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/aflnet/afl-fuzz | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'target_binary_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/xrdp/sbin/xrdp | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'helper_source_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /tmp/xrdp-fuzz-helper.c | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'helper_binary_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/aflnet/xrdp-fuzz-helper | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'compiler=' >> /work/build-evidence/build-lock.txt; gcc --version | head -1 >> /work/build-evidence/build-lock.txt; \
    cat /work/build-evidence/parser-tests.txt >> /work/build-evidence/build-lock.txt; \
    /opt/xrdp/sbin/xrdp --dump-config -c /work/xrdp.ini > /work/build-evidence/config-check.txt; \
    chmod +x /work/run.sh /work/validate.sh /work/capture-build.sh

ENTRYPOINT ["/bin/bash"]
