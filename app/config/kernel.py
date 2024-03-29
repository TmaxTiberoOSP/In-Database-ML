#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/config/kernel.py

import asyncio
from enum import Enum, unique
from typing import Any, Dict, List

from anyio import sleep
from fastapi import FastAPI, Request
from jupyter_client.session import Session
from tornado import ioloop
from zmq import DEALER, REQ, SUB
from zmq.eventloop.zmqstream import ZMQStream

from app.config.settings import get
from kernel.kernel_message import ClientMessage, MasterMessage, NodeType
from kernel.kernel_node import Flow, KernelNode

settings = get()


@unique
class Status(Enum):
    IDLE = "idle"
    BUSY = "busy"


class KernelConnection(KernelNode):
    id: str  # uuid4
    alive: bool
    status: Status
    executed: int
    executing: int
    reply: Dict[str, List[str]]
    reply_futures: Dict[str, asyncio.Future]

    _client: Any
    _process_key: bytes
    _session: Session
    _channels: Dict[str, ZMQStream]
    _pong: bool = False
    _hb_start_handle: Any
    _hb_handle: ioloop.PeriodicCallback

    def __init__(self, client, kernel_id, connection) -> None:
        context = super().__init__(
            NodeType.Connection,
            root_path=f"{settings.kernel_root}/{kernel_id}",
        )

        self._client = client

        self.id = kernel_id
        self.alive = False
        self.status = Status.IDLE
        self.executed = 0
        self.executing = 0
        self.reply = {}
        self.reply_futures = {}

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

        self._start_hb()

    def _start_hb(self):
        hb = self._channels["hb"]

        def pong(_):
            self._pong = False

        hb.on_recv(pong)

        async def ping():
            if self._pong:
                await self.stop()
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

    async def stop(self):
        if not self.alive:
            return

        self.alive = False
        self._stop_hb()

        for stream in self._channels.values():
            stream.close()

        del self._client.kernels[self.id]

        await super().stop(io_stop=False)

    def on_recv_session(self, _, msg_list) -> None:
        _, msg_list = self._session.feed_identities(msg_list)
        msg = self._session.deserialize(msg_list)
        type = msg["msg_type"]

        if type == "execute_reply":
            self.executing = msg["content"]["execution_count"]
        elif type == "status":
            self.status = Status(msg["content"]["execution_state"])

        if "msg_id" in msg["parent_header"]:
            id = msg["parent_header"]["msg_id"]
            if id in self.reply:
                if type == "stream":
                    self.reply[id].extend(msg["content"]["text"].split("\n")[:-1])
                elif type == "error":
                    self.reply[id].append("\n".join(msg["content"]["traceback"]))
                elif type == "execute_reply":
                    self.reply_futures[id].set_result(self.reply[id])

    async def execute(self, code, msg_id: str | None = None) -> str:
        while not self.status is Status.IDLE:
            await sleep(0.1)

        msg = self._session.msg(
            "execute_request",
            {
                "code": code,
                "silent": False,
                "allow_stdin": False,
                "store_history": False,
            },
        )

        if msg_id:
            msg["header"]["msg_id"] = msg_id
        else:
            msg_id = msg["msg_id"]

        self.reply[msg_id] = []
        self.reply_futures[msg_id] = asyncio.get_running_loop().create_future()
        self.executed += 1
        self.executing += 1

        self._session.send(self._channels["shell"], msg)

        reply = await self.reply_futures[msg_id]
        del self.reply_futures[msg_id]

        return reply

    async def send_file(self, *args, **kwargs):
        await super().send_file(*args, id=self._process_key, **kwargs)


class KernelClient(KernelNode):
    kernels: Dict[str, KernelConnection] = {}

    def __init__(self, master_address: str) -> None:
        super().__init__(NodeType.Client, root_path=settings.kernel_root)
        self.connect(master_address, to_master=True)

        # Master Events
        self.listen(MasterMessage.RES_KERNEL, self.on_res_kernel)

    def on_res_kernel(self, _, connection, flow: Flow) -> None:
        kernel = None

        if connection:
            kernel = KernelConnection(self, **connection)
            kernel.run(io_stop=False)
            self.kernels[kernel.id] = kernel

        flow.future.set_result(kernel)
        self.del_flow(flow)

    async def create_kernel(self) -> KernelConnection:
        flow = self.new_flow(future=True)

        self.send(
            ClientMessage.REQ_KERNEL,
            json_body={
                "db": settings.get_db_info(),
                "log": settings.get_log_info(),
            },
            flow=flow,
            to_master=True,
        )

        return await flow.future

    async def on_stop(self) -> Any:
        for kernel in [*self.kernels.values()]:
            await kernel.stop()

    def get(self, id: str) -> KernelConnection:
        return self.kernels[id]

    def get_kernels(self) -> list:
        return [
            {
                "kid": kernel.id,
                "executed": kernel.executed,
                "executing": kernel.executing,
                "status": kernel.status,
                "alive": kernel.alive,
                "reply": kernel.reply,
            }
            for kernel in self.kernels.values()
        ]


def init(app: FastAPI) -> None:
    client = KernelClient(
        f"tcp://{settings.kernel_master_host}:{settings.kernel_master_port}"
    )
    client.run(io_stop=False)
    app.kc = client


async def stop(app) -> None:
    await app.kc.stop(io_stop=False)


def get_client(request: Request) -> KernelClient:
    return request.app.kc
