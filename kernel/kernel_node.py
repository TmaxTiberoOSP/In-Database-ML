#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_node.py

import asyncio
import errno
import logging
import os
import shutil
import signal
from abc import abstractmethod
from asyncio import Future
from io import TextIOWrapper
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

MASTER_IDENTITY: bytes = b"master"


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
        self.kwargs = kwargs

        self._flag_cleanup = False

    def set_cleanup(self) -> None:
        self._flag_cleanup = True


class ServingFile(object):
    file: TextIOWrapper
    is_write: bool = False

    def __init__(
        self,
        path: str,
        is_write: bool = False,
    ) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)

        self.file = open(path, "wb" if is_write else "rb")
        self.is_write = is_write

    def read(self, length: int = 1024 * 1024) -> int:
        if self.is_write:
            raise  # XXX

        data = self.file.read(length)

        if not data:
            self.file.close()

        return data

    def write(self, data: bytes) -> int:
        if not self.is_write:
            raise  # XXX

        size = len(data)

        if size:
            self.file.write(data)
        else:
            self.file.close()

        return size


class KernelNode(object):
    is_active: bool
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

        self.is_active = False

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
        self.listen(NodeMessage.REQ_FILE_SERVING, self._on_req_file_serving)
        self.listen(NodeMessage.RES_FILE_SERVING, self._on_res_file_serving)
        self.listen(NodeMessage.STREAM_FILE, self._on_stream_file)
        self.listen(NodeMessage.FETCH_FILE, self._on_fetch_file)
        self.listen(NodeMessage.REQ_CLEAR_WORKSPACE, self._on_req_clear_workspace)
        self.listen(NodeMessage.RES_CLEAR_WORKSPACE, self._on_res_clear_workspace)

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
        key, type = NodeMessage.unpack(rtype)

        flow = None
        if flow_id:
            if flow_id in self._flows:
                flow = self._flows[flow_id]
            else:
                flow = self.new_flow(prev_id=flow_id)

        body = None
        if rbody:
            body = jsonapi.loads(rbody[1]) if bool(rbody[0]) else rbody[1]

        if type is not NodeMessage.STREAM_FILE:
            # print("  >", raw)  # XXX: logger
            pass

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

        if type is not NodeMessage.STREAM_FILE:
            # print("<D ", payload)  # XXX: logger
            pass

        self._stream.send_multipart(payload)

        if flow and flow._flag_cleanup:
            del self._flows[flow.id]

    async def send_file(
        self,
        source_path: str,
        remote_path: str,
        to_master: bool = False,
        id: bytes | None = None,
    ) -> str:
        flow = self.new_flow(future=True)
        flow.args = ServingFile(source_path)

        self.send(
            NodeMessage.REQ_FILE_SERVING,
            id=id,
            to_master=to_master,
            json_body=remote_path,
            flow=flow,
        )

        return await flow.future

    async def clear_workspace(
        self,
        to_master: bool = False,
        id: bytes | None = None,
    ):
        flow = self.new_flow(future=True)

        self.send(
            NodeMessage.REQ_CLEAR_WORKSPACE,
            id=id,
            to_master=to_master,
            json_body=None,
            flow=flow,
        )

        return await flow.future

    def run(self, io_stop: bool = True) -> None:
        def signal_handler(*_):
            self._ioloop.add_callback_from_signal(self.stop, io_stop=io_stop)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        self.is_active = True
        while self.is_active and io_stop:
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
        if self.is_active:
            self.is_active = False

            await self.on_stop()
            for id in self._connected:
                self.send(NodeMessage.DISCONNECT, id=id)

            self._stream.flush()
            self._stream.close()

            try:
                walk = list(os.walk(self.root_path))
                for path, _, _ in walk[::-1]:
                    if len(os.listdir(path)) == 0:
                        shutil.rmtree(path)
            except:
                pass

            if io_stop:
                self._ioloop.stop()

    @abstractmethod
    async def on_stop(self) -> Any:
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

    # File
    def _on_req_file_serving(self, id, target_path, flow: Flow):
        flow.args = ServingFile(f"{self.root_path}/{target_path}", is_write=True)

        self.send(
            NodeMessage.RES_FILE_SERVING,
            id=id,
            json_body=f"{self.root_path}/{target_path}",
            flow=flow,
        )

    def _on_res_file_serving(self, id, remote_path, flow: Flow):
        file: ServingFile = flow.args
        flow.kwargs["remote_path"] = remote_path

        self.send(NodeMessage.STREAM_FILE, id=id, body=file.read(), flow=flow)

    def _on_stream_file(self, id, body, flow: Flow):
        file: ServingFile = flow.args

        if body:
            file.write(body)
            self.send(NodeMessage.FETCH_FILE, id=id, flow=flow)
        else:
            self.del_flow(flow)

    def _on_fetch_file(self, id, _, flow: Flow):
        file: ServingFile = flow.args

        body = file.read()
        self.send(NodeMessage.STREAM_FILE, id=id, body=body, flow=flow)

        if not body:
            flow.future.set_result(flow.kwargs["remote_path"])
            self.del_flow(flow)

    def _on_req_clear_workspace(self, id, _, flow: Flow):
        try:
            walk = list(os.walk(self.root_path))
            for path, _, _ in walk[::-1]:
                shutil.rmtree(path)
        except:
            pass

        self.send(
            NodeMessage.RES_CLEAR_WORKSPACE,
            id=id,
            json_body=None,
            flow=flow,
        )

    def _on_res_clear_workspace(self, id, _, flow: Flow):
        flow.future.set_result(True)
        self.del_flow(flow)
