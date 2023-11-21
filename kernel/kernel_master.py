#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_master.py

from typing import Dict, Set

from kernel.kernel_message import NodeType
from kernel.kernel_node import KernelNode


class KernelMaster(KernelNode):
    settings: Dict = {
        "limit": 0,
    }
    providers: Set[bytes] = set()

    def __init__(self, port: int, root_path: str, limit: int) -> None:
        super().__init__(NodeType.Master, port=port, root_path=root_path)

        self.settings["limit"] = limit

    def on_connect(self, id, type) -> None:
        if NodeType.Provider.type(type):
            self.providers.add(id)


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Launch a kernel master")
    parser.add_argument(
        "--port",
        type=int,
        help="Port of the kernel master",
        default=8090,
    )
    parser.add_argument(
        "--root_path",
        type=str,
        help="Root path of the kernel master",
        required=False,
        default=f"{os.path.expanduser('~')}/.kernel_master",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Number of kernels that can be created per kernel provider",
        default=5,
    )
    args = parser.parse_args()

    server = KernelMaster(args.port, args.root_path, args.limit)
    server.run()
