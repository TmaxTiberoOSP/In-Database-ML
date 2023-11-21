#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/config/kernel.py

from fastapi import Request

from app.config import settings
from kernel.kernel_message import ClientMessage, NodeType
from kernel.kernel_node import KernelNode

settings = settings.get()


class KernelClient(KernelNode):
    def __init__(self, master_address: str) -> None:
        super().__init__(NodeType.Client, root_path=settings.kernel_root)
        self.connect(master_address, to_master=True)

    async def create_kernel(self):
        flow = self.new_flow(future=True)
        self.send(ClientMessage.REQ_KERNEL, flow=flow, to_master=True)
        return await flow.future


def init(app) -> None:
    app.kc = KernelClient(
        f"tcp://{settings.kernel_master_host}:{settings.kernel_master_port}"
    )


async def stop(app) -> None:
    await app.kc.stop(io_stop=False)


def get_client(request: Request) -> KernelClient:
    return request.app.kc
