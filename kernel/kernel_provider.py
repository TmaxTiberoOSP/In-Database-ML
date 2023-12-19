#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_provider.py

import asyncio
import errno
import signal
from typing import Dict

from app.config.settings import get
from kernel.kernel_message import (
    KernelMessage,
    MasterMessage,
    NodeType,
    ProviderMessage,
)
from kernel.kernel_node import Flow, KernelNode
from kernel.kernel_process import KernelProcess

settings = get()


class KernelProvider(KernelNode):
    host: str
    kernels: Dict[str, KernelProcess]
    limit: int = 0

    def __init__(self, master_address: str, host: str, root_path: str) -> None:
        super().__init__(NodeType.Provider, root_path=root_path)
        self.connect(master_address, to_master=True)

        self.host = host
        self.kernels = {}

        # Master Events
        self.listen(MasterMessage.SETUP_PROVIDER, self.on_master_setup)
        self.listen(MasterMessage.SPWAN_KERNEL, self.on_master_spwan_kernel)

        # Kernel Events
        self.listen(KernelMessage.READY_KERNEL, self.on_kernel_ready)

    def kill_kernel(self, kernel: KernelProcess):
        try:
            os.killpg(kernel.pid, signal.SIGKILL)
            kernel.join()
        except OSError as e:
            if e.errno != errno.ESRCH:
                raise

    def on_disconnect(self, id, _, **__) -> None:
        for kernel in list(self.kernels.values()):
            if kernel.id != id:
                continue

            self.kill_kernel(kernel)
            del self.kernels[kernel.kernel_id]

    # Master Events
    def on_master_setup(self, _, settings, **__) -> None:
        self.limit = settings["limit"]

    def on_master_spwan_kernel(self, _, info, flow: Flow) -> None:
        if len(self.kernels) >= self.limit:
            flow.set_cleanup()

            self.send(
                ProviderMessage.SPWAN_KERNEL_REPLY,
                json_body=None,
                flow=flow,
                to_master=True,
            )
        else:
            current = asyncio.get_event_loop()

            kernel = KernelProcess(
                self._gen_unique_id(self.kernels),
                info,
                self.root_path,
                self.host,
                self._port,
                self._identity,
                flow,
            )
            self.kernels[kernel.kernel_id] = kernel
            kernel.start()

            asyncio.set_event_loop(current)

    # Kernel Events
    def on_kernel_ready(self, id, connection, flow=Flow) -> None:
        flow.set_cleanup()

        kernel = self.kernels[connection["kernel_id"]]
        kernel.id = id

        self.send(
            ProviderMessage.SPWAN_KERNEL_REPLY,
            json_body=connection,
            flow=flow,
            to_master=True,
        )

    async def on_stop(self):
        for kernel in self.kernels.values():
            self.kill_kernel(kernel)


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Launch a kernel provider")
    parser.add_argument("address", type=str, help="Address of the kernel master")
    parser.add_argument(
        "--host",
        type=str,
        help="IP Address of the kernel provider",
        required=False,
        default="127.0.0.1",
    )
    parser.add_argument(
        "--root_path",
        type=str,
        help="Root path of the kernel provider",
        required=False,
        default=f"{os.path.expanduser('~')}/.kernel_provider",
    )
    args = parser.parse_args()

    provider = KernelProvider(f"tcp://{args.address}", args.host, args.root_path)
    provider.run()
