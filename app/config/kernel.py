#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/config/kernel.py

from app.config import settings
from kernel.kernel_message import NodeType
from kernel.kernel_node import KernelNode

settings = settings.get()


class KernelClient(KernelNode):
    def __init__(self, master_address: str) -> None:
        super().__init__(NodeType.Client, root_path=settings.kernel_root)
        self.connect(master_address, to_master=True)


def init(app):
    app.kc = KernelClient(
        f"tcp://{settings.kernel_master_host}:{settings.kernel_master_port}"
    )


async def stop(app):
    await app.kc.stop(io_stop=False)
