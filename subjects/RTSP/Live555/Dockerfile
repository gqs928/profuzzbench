FROM ubuntu:22.04

# Install common dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update && \
    apt-get -y install sudo \ 
    apt-utils \
    build-essential \
    openssl \
    clang \
    graphviz-dev \
    git \
    autoconf \
    libgnutls28-dev \
    libssl-dev \
    llvm \
    python3-pip \
    nano \
    net-tools \
    vim \
    gdb \
    netcat-openbsd \
    strace \
    wget

# Add a new user ubuntu, pass: ubuntu
RUN groupadd ubuntu && \
    useradd -rm -d /home/ubuntu -s /bin/bash -g ubuntu -G sudo -u 1000 ubuntu -p "$(openssl passwd -1 ubuntu)"

RUN chmod 777 /tmp

RUN pip3 install gcovr==4.2

# Use ubuntu as default username
USER ubuntu
WORKDIR /home/ubuntu

# Import environment variable to pass as parameter to make (e.g., to make parallel builds with -j)
ARG MAKE_OPT

COPY --chown=ubuntu:ubuntu trace-pc-llvm14.patch /home/ubuntu/trace-pc-llvm14.patch

# Set up fuzzers
RUN git clone https://github.com/profuzzbench/aflnet.git && \
    cd aflnet && \
    patch -p1 < /home/ubuntu/trace-pc-llvm14.patch && \
    make clean all $MAKE_OPT && \
    cd llvm_mode && AFL_TRACE_PC=1 make clean all $MAKE_OPT

RUN git clone https://github.com/profuzzbench/aflnwe.git && \
    cd aflnwe && \
    patch -p1 < /home/ubuntu/trace-pc-llvm14.patch && \
    make clean all $MAKE_OPT && \
    cd llvm_mode && AFL_TRACE_PC=1 make clean all $MAKE_OPT

# Set up environment variables for AFLNet
ENV WORKDIR="/home/ubuntu/experiments"
ENV AFLNET="/home/ubuntu/aflnet"
ENV PATH="${PATH}:${AFLNET}:/home/ubuntu/.local/bin:${WORKDIR}"
ENV AFL_PATH="${AFLNET}"
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1


RUN mkdir $WORKDIR

COPY --chown=ubuntu:ubuntu fuzzing.patch ${WORKDIR}/fuzzing.patch
COPY --chown=ubuntu:ubuntu gcov.patch ${WORKDIR}/gcov.patch

# Set up environment variables for ASAN
env ASAN_OPTIONS='abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1:detect_container_overflow=0:poison_array_cookie=0:malloc_fill_byte=0:max_malloc_fill_size=16777216'

# Download and compile Live555 for fuzzing
RUN cd $WORKDIR && \
    wget -q https://download.live555.com/live.2026.10.24.tar.gz -O live.2026.10.24.tar.gz && \
    echo "5d6244604b364251d0c0b0fc87a849488958802245b1473eaaf55eaaef5a838b  live.2026.10.24.tar.gz" | sha256sum -c - && \
    tar -xzf live.2026.10.24.tar.gz && mv live live555 && \
    cd live555 && \
    patch -p1 < $WORKDIR/fuzzing.patch && \
    ./genMakefiles linux && \
    AFL_USE_ASAN=1 CC=afl-clang-fast CXX=afl-clang-fast++ make clean all $MAKE_OPT

# Set up Live555 for fuzzing
RUN cd ${WORKDIR}/live555/testProgs && \
    cp ${AFLNET}/tutorials/live555/sample_media_sources/*.* ./

# Download and compile Live555 for coverage analysis
RUN cd $WORKDIR && \
    mkdir live555-cov && tar -xzf live.2026.10.24.tar.gz --strip-components=1 -C live555-cov && \
    cd live555-cov && \
    patch -p1 < $WORKDIR/fuzzing.patch && \
    patch -p1 < $WORKDIR/gcov.patch && \
    ./genMakefiles linux && \
    make CFLAGS="-g -O0 -fprofile-arcs -ftest-coverage" CPPFLAGS="-fprofile-arcs -ftest-coverage" CXXFLAGS="-g -O0 -fprofile-arcs -ftest-coverage" LDFLAGS="--coverage" clean all $MAKE_OPT

# Set up Live555 for coverage analysis
RUN cd ${WORKDIR}/live555-cov/testProgs && \
    cp ${AFLNET}/tutorials/live555/sample_media_sources/*.* ./

COPY --chown=ubuntu:ubuntu kill-server.sh ${WORKDIR}/kill-server
COPY --chown=ubuntu:ubuntu in-rtsp ${WORKDIR}/in-rtsp
COPY --chown=ubuntu:ubuntu rtsp.dict ${WORKDIR}/rtsp.dict
COPY --chown=ubuntu:ubuntu cov_script.sh ${WORKDIR}/cov_script
COPY --chown=ubuntu:ubuntu run.sh ${WORKDIR}/run
