#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_master.py

from typing import Dict, Set

from kernel.kernel_message import (
    ClientMessage,
    MasterMessage,
    NodeType,
    ProviderMessage,
)
from kernel.kernel_node import Flow, KernelNode


class KernelMaster(KernelNode):
    providers: Set[bytes]
    clients: Set[bytes]
    settings: Dict = {
        "limit": 0,
    }

    def __init__(self, port: int, root_path: str, limit: int) -> None:
        super().__init__(NodeType.Master, port=port, root_path=root_path)

        self.providers = set()
        self.clients = set()
        self.settings["limit"] = limit

        # Provider Events
        self.listen(
            ProviderMessage.SPWAN_KERNEL_REPLY, self.on_provider_spwan_kernel_reply
        )

        # Client Events
        self.listen(ClientMessage.REQ_KERNEL, self.on_client_request_kernel)

    def on_connect(self, id, type, **_) -> None:
        if NodeType.Provider.type(type):
            self.providers.add(id)
            self.send(MasterMessage.SETUP_PROVIDER, json_body=self.settings, id=id)
            print(f"providers: {self.providers}")  # XXX: logger
        elif NodeType.Client.type(type):
            self.clients.add(id)
            print(f"clients: {self.clients}")  # XXX: logger
        else:
            pass  # XXX: logger

    def on_disconnect(self, id, _, **__) -> None:
        if id in self.providers:
            self.providers.remove(id)
            print(f"providers: {self.providers}")  # XXX: logger
        elif id in self.clients:
            self.clients.remove(id)
            print(f"clients: {self.clients}")  # XXX: logger
        else:
            pass  # XXX: logger

    # Provider Events
    def on_provider_spwan_kernel_reply(
        self, provider_id, connection, flow=Flow, **_
    ) -> None:
        flow.set_cleanup()
        client_id = flow.args

        self.send(
            MasterMessage.RES_KERNEL,
            id=client_id,
            json_body=connection,
            flow=flow,
        )

        if connection:
            self.providers.add(provider_id)

    # Client Events
    def on_client_request_kernel(self, client_id, body, flow: Flow, **__) -> None:
        if self.providers:
            flow.args = client_id

            self.send(
                MasterMessage.SPWAN_KERNEL,
                id=self.providers.pop(),
                json_body=body,
                flow=flow,
            )
        else:
            flow.set_cleanup()

            self.send(
                MasterMessage.RES_KERNEL,
                id=client_id,
                json_body=None,
                flow=flow,
            )


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
