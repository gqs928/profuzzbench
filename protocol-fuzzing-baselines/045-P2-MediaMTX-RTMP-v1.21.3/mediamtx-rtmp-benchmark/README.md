# MediaMTX RTMP benchmark profile

This profile targets the official MediaMTX v1.21.3 stable source release over RTMP v3/TCP. The source archive, AFLNet commit, and build image are pinned in source-lock.json.

Stock AFLNet does not include an RTMP request parser. rtmp_aflnet.c adds handshake-aware request segmentation, RTMP chunk reassembly, and response-state IDs derived from RTMP message types and AMF command names. The local rtmp_proxy.py bridges MediaMTX on 127.0.0.1:1935 to AFLNet on 127.0.0.1:1936: it forwards each C0/C1 handshake, returns the server S0/S1/S2, then sends the connection-specific S1 echo as C2. The testcase C2 bytes are a placeholder and are not forwarded; all later RTMP command/chunk bytes pass through unchanged.

The target is built with Go native coverage (-cover -coverpkg=./...). AFLNet response-state paths describe MediaMTX RTMP behavior; its bitmap and process counters describe only the lifecycle helper, not the Go target. Preflight, formal-campaign, and post-smoke coverage data are separated. The post-smoke service is a fresh process.

Build and validate the image, including a 60-second response-state preflight, by running ./build.sh from this directory.

Run the formal 30-minute campaign from this directory:

    docker run -d --name mediamtx-rtmp-30m --network none --user "$(id -u):$(id -g)" -v "$PWD/results:/work/results" mediamtx-rtmp-aflnet:v1.21.3 -lc '/work/run.sh /work/results/rtmp-30m 1800'
    docker wait mediamtx-rtmp-30m
    docker logs mediamtx-rtmp-30m > results/rtmp-30m/container.log 2>&1
    docker rm mediamtx-rtmp-30m
    ./package.sh
    docker image rm mediamtx-rtmp-aflnet:v1.21.3

The formal run starts the target, handshake bridge, and fuzzer inside one isolated container. It records a fresh RTMP connect smoke before the campaign and after a clean target restart. package.sh verifies the 1,800-second AFLNet run, coverage files, response-state graph, and graceful target shutdown before writing the independent ZIP and SHA-256 sidecar. Reusable lessons are maintained centrally in 基准化经验库.md, outside this protocol package.
