#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_provider.py

import asyncio
from typing import Dict

from kernel.kernel_message import (
    KernelMessage,
    MasterMessage,
    NodeType,
    ProviderMessage,
)
from kernel.kernel_node import Flow, KernelNode
from kernel.kernel_process import KernelProcess


class KernelProvider(KernelNode):
    limit: int = 0
    kernels: Dict[str, KernelProcess] = {}

    def __init__(self, master_address: str, root_path: str) -> None:
        super().__init__(NodeType.Provider, root_path=root_path)
        self.connect(master_address, to_master=True)

        # Master Events
        self.listen(MasterMessage.SETUP_PROVIDER, self.on_master_setup)
        self.listen(MasterMessage.SPWAN_KERNEL, self.on_master_spwan_kernel)

        # Kernel Events
        self.listen(KernelMessage.READY_KERNEL, self.on_kernel_ready)

    # Master Events
    def on_master_setup(self, _, settings, **__) -> None:
        self.limit = settings["limit"]

    def on_master_spwan_kernel(self, *_, flow: Flow, **__) -> None:
        current = asyncio.get_event_loop()

        kernel = KernelProcess(
            self._gen_unique_id(self.kernels),
            self.root_path,
            self._port,
            self._identity,
            flow,
        )
        self.kernels[kernel.kernel_id] = kernel
        kernel.start()

        asyncio.set_event_loop(current)

    # Kernel Events
    def on_kernel_ready(self, id, connection, flow=Flow, **_) -> None:
        kernel = self.kernels[connection["kernel_id"]]
        kernel.id = id

        self.send(
            ProviderMessage.SPWAN_KERNEL_REPLY,
            json_body=connection,
            flow=flow,
            to_master=True,
        )

    def on_stop(self):
        for kernel in self.kernels.values():
            kernel.stop()


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
