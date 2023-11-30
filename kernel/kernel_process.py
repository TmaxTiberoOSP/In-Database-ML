#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_process.py
import asyncio
import os
import signal
from multiprocessing import Process

import jaydebeapi
from ipykernel.kernelapp import IPKernelApp
from setproctitle import setproctitle

from app.config.tibero import get_db_connection
from kernel.kernel_message import KernelMessage, NodeType
from kernel.kernel_node import Flow, KernelNode


class KernelProcessServer(KernelNode):
    _provider_id: bytes
    _connection_id: bytes | None
    _process: Process
    _conn: jaydebeapi.Connection | None
    log_id: str | None

    def __init__(
        self,
        provider_address: str,
        provider_id: bytes,
        root_path: str,
        process: Process,
    ) -> None:
        super().__init__(NodeType.Kernel, root_path=root_path)
        self.connect(provider_address, id=provider_id)

        self._provider_id = provider_id
        self._connection_id = None
        self._process = process
        self._conn = (
            get_db_connection(**process.info["db"]) if "db" in process.info else None
        )
        self.log_id = None

    async def on_stop(self):
        if self._conn:
            self._conn.close()

    def on_connect(self, id, type, **_) -> None:
        if NodeType.Connection.type(type):
            self._connection_id = id
        else:
            pass  # XXX: logger

    def on_disconnect(self, id, _, **__) -> None:
        if id == self._connection_id:
            self._process.stop()

    def send_to_provider(self, *args, **kwargs) -> None:
        self.send(*args, id=self._provider_id, **kwargs)

    def send_to_connect(self, *args, **kwargs) -> None:
        self.send(*args, id=self._connection_id, **kwargs)

    def send_file_to_connect(self, source_path: str, remote_path: str) -> None:
        asyncio.ensure_future(
            self.send_file(source_path, remote_path, id=self._connection_id)
        )

    def new_db_connection(self) -> jaydebeapi.Connection:
        if "db" in self._process.info:
            return get_db_connection(**self._process.info["db"])
        else:
            raise Exception("db info not found")

    def log(self, *args, stdout=True) -> None:
        message = "".join(map(str, args))

        if self._conn and self.log_id is not None and "log" in self._process.info:
            log = self._process.info["log"]
            cursor = self._conn.cursor()

            cursor.execute(
                f"INSERT INTO {log['table']} ({log['id_column']}, {log['log_column']}) VALUES (?, ?);",
                (self.log_id, message),
            )
            self._conn.commit()

            cursor.close()

        if stdout:
            print(message)


class KernelProcess(Process):
    id: bytes

    kernel_id: str  # uuid4
    info: dict
    _provider_path: str
    _provider_host: str
    _provider_port: int
    _provider_id: bytes
    _req_flow: Flow

    def __init__(
        self,
        kernel_id: str,
        info: dict,
        provider_path: str,
        provider_host: str,
        provider_port: int,
        provider_id: bytes,
        flow: Flow,
    ) -> None:
        super(KernelProcess, self).__init__()

        self.kernel_id = kernel_id
        self.info = info
        self._provider_path = provider_path
        self._provider_host = provider_host
        self._provider_port = provider_port
        self._provider_id = provider_id
        self._req_flow = flow

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        os.setpgrp()
        setproctitle(f"python kernel {self.kernel_id}")

        server = KernelProcessServer(
            f"tcp://{self._provider_host}:{self._provider_port}",
            self._provider_id,
            f"{self._provider_path}/{self.kernel_id}",
            self,
        )

        IPKernelApp.no_stdout = True
        IPKernelApp.no_stderr = True

        app = IPKernelApp.instance()
        app.ip = self._provider_host
        app.user_ns = {
            "kernel_id": self.kernel_id,
            "_ROOT_PATH": server.root_path,
            "_SERVER": server,
        }

        app.initialize()
        app.cleanup_connection_file()

        loop.call_later(
            0.5,
            lambda: server.send_to_provider(
                KernelMessage.READY_KERNEL,
                json_body={
                    "kernel_id": self.kernel_id,
                    "connection": {
                        "session_key": app.session.key.decode(),
                        "ip": app.ip,
                        "hb": app.hb_port,
                        "iopub": app.iopub_port,
                        "shell": app.shell_port,
                        "process_key": server._identity.decode(),
                        "process": server._port,
                    },
                },
                flow=self._req_flow,
            ),
        )

        def signal_handler(*_):
            app.kernel.do_shutdown(False)

        signal.signal(signal.SIGTERM, signal_handler)

        server.run(io_stop=False)
        app.start()

    def stop(self) -> None:
        print(f"stop {self.kernel_id}")  # XXX: logger
        if self.is_alive():
            try:
                os.kill(self.pid, signal.SIGTERM)
            except:
                pass
