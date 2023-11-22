#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_message.py

import struct
from enum import Enum, auto

from typing_extensions import Self


class NodeType(Enum):
    Master = "master"
    Provider = "provider"
    Kernel = "kernel"
    Client = "client"

    def type(self, value: str) -> bool:
        return self.value == value


class NodeMessage(Enum):
    # Connection
    DISCONNECT = auto()
    GREETING = auto()
    GREETING_REPLY = auto()

    # Master <-> Provider
    SETUP_PROVIDER = auto()
    SPWAN_KERNEL = auto()
    SPWAN_KERNEL_REPLY = auto()

    # Client <-> Master
    REQ_KERNEL = auto()
    RES_KERNEL = auto()

    # Provider <-> Kernel
    READY_KERNEL = auto()

    def type(self, value: int) -> bool:
        return self.value == value

    def pack(self) -> bytes:
        return struct.pack("<H", self.value)

    def unpack(value) -> (int, Self):
        value = struct.unpack("<H", value)[0]
        return value, NodeMessage(value)


class KernelMessageAuto(Enum):
    def _generate_next_value_(name, *_):
        return NodeMessage[name].value

    def pack(self):
        return struct.pack("<H", self.value)


class MasterMessage(KernelMessageAuto):
    SETUP_PROVIDER = auto()
    SPWAN_KERNEL = auto()
    RES_KERNEL = auto()


class ClientMessage(KernelMessageAuto):
    REQ_KERNEL = auto()


class ProviderMessage(KernelMessageAuto):
    SPWAN_KERNEL_REPLY = auto()


class KernelMessage(KernelMessageAuto):
    READY_KERNEL = auto()
