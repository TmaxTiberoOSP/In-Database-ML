#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/util/sql_reader.py

from io import TextIOWrapper


def sql_reader(file: TextIOWrapper):
    result = []

    sql = ""
    for line in file.readlines():
        if ";" in line:
            sql += line
            result.append(sql)
            sql = ""
        else:
            sql += line.rstrip()

    return result
