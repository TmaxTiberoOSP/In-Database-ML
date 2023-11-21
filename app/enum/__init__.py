#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/enum/__init__.py

from enum import Enum


class AutoNameEnum(Enum):
    def _generate_next_value_(name, *_):
        return name