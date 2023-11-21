#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_provider.py

from kernel.kernel_message import MasterMessage, NodeType
from kernel.kernel_node import KernelNode


class KernelProvider(KernelNode):
    limit: int = 0

    def __init__(self, master_address: str, root_path: str) -> None:
        super().__init__(NodeType.Provider, root_path=root_path)
        self.connect(master_address, to_master=True)

        # Master Events
        self.listen(MasterMessage.SETUP_PROVIDER, self._on_setup)

    # Master Events
    def _on_setup(self, _, settings) -> None:
        self.limit = settings["limit"]


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Launch a kernel provider")
    parser.add_argument("address", type=str, help="Address of the kernel master")
    parser.add_argument(
        "--root_path",
        type=str,
        help="Root path of the kernel provider",
        required=False,
        default=f"{os.path.expanduser('~')}/.kernel_provider",
    )
    args = parser.parse_args()

    provider = KernelProvider(f"tcp://{args.address}", args.root_path)
    provider.run()
