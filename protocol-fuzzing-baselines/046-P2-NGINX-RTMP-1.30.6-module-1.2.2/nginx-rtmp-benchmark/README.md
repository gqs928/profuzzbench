# NGINX RTMP benchmark profile

This profile targets the NGINX stable source release 1.30.6 with upstream `nginx-rtmp-module` tag v1.2.2, pinned to commit `23e1873aa62acb58b7881eed2a501f5bf35b82e9` in `source-lock.json`. The NGINX archive's PGP signature verified with the Sergey Kandaurov key listed on NGINX's official PGP page. The NGINX download page lists 1.30.6 as stable; the module repository has no GitHub release objects, so v1.2.2 is selected as its latest upstream tag.

The module source still defines `NGINX_RTMP_VERSION` as `1.1.4`; this is an internal stale macro, so the benchmark's module identity is the exact upstream tag, commit, and source archive hash recorded in `source-lock.json`.

Stock AFLNet has no RTMP adapter. The profile carries the RTMP C0/C1 and C2 handshake splitter, chunk reassembler, AMF command-state parser, and a loopback bridge that supplies the connection-specific S1 echo required for C2. The NGINX RTMP listener is loopback-only and configured with a single `live` application. The corpus exercises connect, stream creation, releaseStream, and publish.

NGINX and the RTMP module are compiled with GCC native coverage (`--coverage`); AFLNet response states describe the protocol path while target line/branch coverage is reported by gcovr. The AFLNet lifecycle helper is not used as a proxy for target coverage. Preflight, formal campaign, and fresh post-campaign smoke coverage remain separate.

Build the image and run the 60-second state-aware preflight with `bash build.sh`. Run the formal 30-minute campaign with:

    docker run -d --name nginx-rtmp-30m --network none --user "$(id -u):$(id -g)" -v "$PWD/results:/work/results" nginx-rtmp-aflnet:1.30.6-module-1.2.2 -lc '/work/run.sh /work/results/rtmp-30m 1800'
    docker wait nginx-rtmp-30m
    docker logs nginx-rtmp-30m > results/rtmp-30m/container.log 2>&1
    docker rm nginx-rtmp-30m
    bash stop-server-and-remove-image.sh
    bash package.sh

The queue replay runs against a live NGINX process after AFLNet stops. Every queue testcase gets a new RTMP session and a protocol-correct dynamic C2. The independent package excludes the central experience library, which is maintained in the framework deliverable.
