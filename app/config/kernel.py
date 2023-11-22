#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/config/kernel.py

from typing import Dict

from fastapi import Request
from jupyter_client.session import Session
from tornado import ioloop
from zmq import DEALER, REQ, SUB
from zmq.eventloop.zmqstream import ZMQStream

from app.config import settings
from kernel.kernel_message import ClientMessage, MasterMessage, NodeType
from kernel.kernel_node import Flow, KernelNode

settings = settings.get()


class KernelConnection(KernelNode):
    alive: bool

    _process_key: bytes
    _session: Session
    _channels: Dict[str, ZMQStream]
    _pong: bool = False

    def __init__(self, kernel_id, connection) -> None:
        context = super().__init__(
            NodeType.Connection,
            root_path=f"{settings.kernel_root}/{kernel_id}",
        )

        self._process_key = connection["process_key"].encode()
        self.connect(
            f"tcp://{connection['ip']}:{connection['process']}",
            id=self._process_key,
        )

        self._session = Session(key=connection["session_key"].encode())

        self._session = Session(key=connection["session_key"].encode())
        self._channels = {"shell": None, "iopub": None, "hb": None}
        for ch, type in [
            ("shell", DEALER),
            ("iopub", SUB),
            ("hb", REQ),
        ]:
            socket = context.socket(type)
            socket.connect(f"tcp://{connection['ip']}:{connection[ch]}")
            self._channels[ch] = ZMQStream(socket)

        self._channels["iopub"].socket.subscribe(b"")
        for ch in ["iopub", "shell"]:
            self._channels[ch].on_recv_stream(self.on_recv_session)

        self.alive = False
        self._start_hb()

    def _start_hb(self):
        hb = self._channels["hb"]

        def pong(_):
            self._pong = False

        hb.on_recv(pong)

        def ping():
            if self._pong:
                self.stop()
            else:
                hb.send(b"ping")
                self._pong = True

        self._hb_handle = ioloop.PeriodicCallback(ping, 3.0 * 1000)  # 3sc

        def start_ping():
            if self.alive:
                self._hb_handle.start()

        self._hb_start_handle = ioloop.IOLoop.current().call_later(1.0, start_ping)
        self.alive = True

    def _stop_hb(self):
        try:
            self._hb_handle.stop()
            ioloop.IOLoop.current().remove_timeout(self._hb_start_handle)
            self._channels["hb"].on_recv(None)
        except:
            pass

    def stop(self):
        if not self.alive:
            return

        self.alive = False
        self._stop_hb()

        for stream in self._channels.values():
            stream.close()

    def on_recv_session(self, *_):
        pass


class KernelClient(KernelNode):
    kernels: Dict[str, KernelConnection] = {}

    def __init__(self, master_address: str) -> None:
        super().__init__(NodeType.Client, root_path=settings.kernel_root)
        self.connect(master_address, to_master=True)

        # Master Events
        self.listen(MasterMessage.RES_KERNEL, self.on_res_kernel)

    def on_res_kernel(self, _, connection, flow: Flow, **__) -> None:
        flow.set_cleanup()

        kernel = KernelConnection(**connection)
        flow.future.set_result(kernel)
        self.del_flow(flow)

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
