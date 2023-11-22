#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_node.py

import asyncio
import errno
import logging
import os
import signal
from abc import abstractmethod
from asyncio import Future
from time import time
from typing import Any, Callable, Dict, Tuple
from uuid import uuid4

from tornado.ioloop import IOLoop
from zmq import IDENTITY, ROUTER, ROUTER_MANDATORY
from zmq import Context as ZMQContext
from zmq import ZMQError
from zmq.eventloop.zmqstream import ZMQStream
from zmq.utils import jsonapi

from kernel.kernel_message import NodeMessage, NodeType

MASTER_IDENTITY: bytes = b"matser"


class KernelNodeFilter(logging.Filter):
    def filter(self, record) -> bool:
        return not record.getMessage().endswith("Host unreachable")


class Flow(object):
    id: bytes  # {identity}/{seq}
    args: Tuple
    kwargs: Dict[str, Any]
    future: Future | None = None
    callback: Callable | None = None
    prev_id: bytes | None = None  # uuid

    _seq: int = 0
    _flag_cleanup: bool

    def __init__(self, id: bytes, *args, **kwargs) -> None:
        if "prev_id" in kwargs:
            self.id = kwargs.pop("prev_id")
        else:
            self.id = f"{id.decode()}/{Flow._seq}".encode()
            Flow._seq += 1

        self.args = args
        if "future" in kwargs:
            kwargs.pop("future")
            self.future = asyncio.get_running_loop().create_future()
        if "callback" in kwargs:
            self.callback = kwargs.pop("callback")
        self.kwarg = kwargs

        self._flag_cleanup = False

    def set_cleanup(self) -> None:
        self._flag_cleanup = True


class KernelNode(object):
    is_active: bool = False
    type: NodeType
    root_path: str

    _port: int
    _ioloop: IOLoop
    _identity: bytes
    _stream: ZMQStream
    _handles: Dict[int, Callable]
    _connected: Dict[bytes, time]
    _flows: Dict[bytes, Flow]

    def __init__(
        self,
        type: NodeType,
        port: int | None = None,
        root_path: str = f"{os.path.expanduser('~')}/.kernel_node",
    ) -> ZMQContext:
        context = ZMQContext()
        socket = context.socket(ROUTER)
        socket.setsockopt(ROUTER_MANDATORY, 1)

        logging.getLogger("tornado.general").addFilter(KernelNodeFilter())

        # IDENTITY 설정 (Master의 경우 고정)
        self.type = type
        if type is NodeType.Master:
            socket.setsockopt_string(IDENTITY, MASTER_IDENTITY.decode())
        else:
            socket.setsockopt_string(IDENTITY, f"{type.value} {uuid4()}")

        if port:
            self._port = port
            socket.bind(f"tcp://*:{port}")
        else:
            self._port = socket.bind_to_random_port("tcp://*")

        os.makedirs(root_path, exist_ok=True)
        self.root_path = root_path

        self._ioloop = IOLoop.current()
        self._identity = socket.getsockopt_string(IDENTITY).encode()
        self._stream = ZMQStream(socket, io_loop=self._ioloop)
        self._stream.on_recv(self._on_recv)

        self._handles = {}
        self.listen(NodeMessage.DISCONNECT, self._on_disconnect)
        self.listen(NodeMessage.GREETING, self._on_connect)

        self._connected = {}
        self._flows = {}

        return context

    def listen(self, type: NodeMessage, handler: Callable) -> None:
        if type.value in self._handles:
            raise  # XXX: custom error
        else:
            self._handles[type.value] = handler

    def _on_recv(self, raw: list[bytes]) -> None:
        id, rtype, flow_id, *rbody = raw

        self._connected[id] = time()
        key, _ = NodeMessage.unpack(rtype)

        flow = None
        if flow_id:
            if flow_id in self._flows:
                flow = self._flows[flow_id]
            else:
                flow = self.new_flow(prev_id=flow_id)

        body = None
        if rbody:
            body = jsonapi.loads(rbody[1]) if bool(rbody[0]) else rbody[1]

        print("  >", raw)  # XXX: logger
        if key in self._handles:
            self._handles[key](id, body, flow=flow)

    def connect(
        self,
        address,
        to_master: bool = False,
        id: bytes | None = None,
    ) -> None:
        self._stream.connect(address)
        self._ioloop.call_later(
            0.5,
            lambda: self.send(
                NodeMessage.GREETING,
                json_body=self.type.value,
                to_master=to_master,
                id=id,
            ),
        )

    def send(
        self,
        type: NodeMessage,
        body: Any = None,
        json_body: Any = None,
        flow: Flow | None = None,
        to_master: bool = False,
        id: bytes | None = None,
    ) -> None:
        # | identity | message_type | flow_id | body_type | body |
        payload = []
        payload.append(MASTER_IDENTITY if to_master else id)
        payload.append(type.pack())  # message_type
        payload.append(flow.id if flow else b"")  # flow_id

        if body and json_body:
            raise  # XXX: custom error
        elif body:
            payload.append(bytes(False))
            payload.append(body)
        elif json_body:
            payload.append(bytes(True))
            payload.append(jsonapi.dumps(json_body))

        print("<D ", payload)  # XXX: logger
        self._stream.send_multipart(payload)

        if flow and flow._flag_cleanup:
            del self._flows[flow.id]

    def run(self) -> None:
        def signal_handler(*_):
            self._ioloop.add_callback_from_signal(self.stop)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        self.is_active = True
        while self.is_active:
            try:
                self._ioloop.start()
            except ZMQError as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    raise
            except Exception as e:
                if self.is_active:
                    # print(e) # XXX: logger
                    break
                else:
                    raise
            else:
                break

    async def stop(self, io_stop: bool = True) -> None:
        self.is_active = False

        self.on_stop()
        for id in self._connected:
            self.send(NodeMessage.DISCONNECT, id=id)

        self._stream.flush()
        self._stream.close()

        if io_stop:
            self._ioloop.stop()

    @abstractmethod
    def on_stop(self, *_, **__) -> Any:
        pass

    def _on_connect(self, *args, **kwargs) -> None:
        self.send(NodeMessage.GREETING_REPLY, id=args[0])
        self.on_connect(*args, **kwargs)

    @abstractmethod
    def on_connect(self, *_, **__) -> Any:
        pass

    def _on_disconnect(self, *args, **kwargs) -> None:
        self.on_disconnect(*args, **kwargs)
        del self._connected[args[0]]

    @abstractmethod
    def on_disconnect(self, *_, **__) -> Any:
        pass

    def _gen_unique_id(self, ids: list):
        id = str(uuid4())
        while id in ids:
            id = str(uuid4())
        return id

    # Flow
    def new_flow(self, *args, **kwargs) -> Flow:
        flow = Flow(self._identity, *args, **kwargs)
        self._flows[flow.id] = flow
        return flow

    def del_flow(self, flow: Flow) -> None:
        if flow.id in self._flows:
            del self._flows[flow.id]
