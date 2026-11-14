#!/usr/bin/env python3
"""构造 NFSv3 NULL 探针输入；用于校准 AFLNet 异常退出记录能力。"""

import pathlib
import sys

from nfs_rpc import NFS_PROGRAM, NFS_VERSION, rpc_call


def main() -> None:
    destination = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/results/fault-probe/seeds")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "nfs-null-abort.bin").write_bytes(
        rpc_call(NFS_PROGRAM, NFS_VERSION, 0, b"", 1)
    )
    print(f"已生成独立探针的 NFSv3 NULL 请求：{destination / 'nfs-null-abort.bin'}")


if __name__ == "__main__":
    main()
