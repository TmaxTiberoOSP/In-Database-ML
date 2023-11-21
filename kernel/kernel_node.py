#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_node.py

import errno
import logging
import os
import signal
from abc import abstractmethod
from time import time
from typing import Any, Callable, Dict
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


class KernelNode(object):
    is_active: bool = False
    type: NodeType
    port: int
    root_path: str

    _ioloop: IOLoop
    _identity: bytes
    _stream: ZMQStream
    _handles: Dict[int, Callable] = {}
    _connected: Dict[bytes, time] = {}

    def __init__(
        self,
        type: NodeType,
        port: int | None = None,
        root_path: str = f"{os.path.expanduser('~')}/.kernel_node",
    ) -> None:
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
            self.port = port
            socket.bind(f"tcp://*:{port}")
        else:
            self.port = socket.bind_to_random_port("tcp://*")

        os.makedirs(root_path, exist_ok=True)
        self._root_path = root_path

        self._ioloop = IOLoop.current()
        self._identity = socket.getsockopt_string(IDENTITY).encode()
        self._stream = ZMQStream(socket, io_loop=self._ioloop)
        self._stream.on_recv(self._on_recv)

        self.listen(NodeMessage.GREETING, self._on_connect)

    def listen(self, type: NodeMessage, handler: Callable) -> None:
        if type.value in self._handles:
            raise  # XXX: custom error
        else:
            self._handles[type.value] = handler

    def _on_recv(self, raw: list[bytes]) -> None:
        id, rtype, *rbody = raw

        self._connected[id] = time()
        key, _ = NodeMessage.unpack(rtype)

        body = None
        if rbody:
            body = jsonapi.loads(rbody[1]) if bool(rbody[0]) else rbody[1]

        print("  >", raw)  # XXX: logger
        if key in self._handles:
            self._handles[key](id, body)

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
        to_master: bool = False,
        id: bytes | None = None,
    ) -> None:
        # | identity | message_type | body_type | body |
        payload = []
        payload.append(MASTER_IDENTITY if to_master else id)
        payload.append(type.pack())  # message_type

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

        for id in self._connected:
            self.send(NodeMessage.DISCONNECT, id=id)

        self._stream.flush()
        self._stream.close()

        if io_stop:
            self._ioloop.stop()

    def _on_connect(self, *args, **kwargs) -> None:
        self.on_connect(*args, **kwargs)
        self.send(NodeMessage.GREETING_REPLY, id=args[0])

    @abstractmethod
    def on_connect(self, *_, **__) -> Any:
        pass

    def _on_disconnect(self, *args, **kwargs) -> None:
        self.on_disconnect(*args, **kwargs)
        del self._connected[args[0]]

    @abstractmethod
    def on_disconnect(self, *_, **__) -> Any:
        pass
