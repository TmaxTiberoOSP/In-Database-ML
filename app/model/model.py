#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/model.py

import json

from fastapi import HTTPException
from jaydebeapi import Connection, DatabaseError
from pydantic import BaseModel


def default_str(dict, key, defulat="") -> str:
    return dict[key] if key in dict else defulat


class Component(BaseModel):
    type: str
    name: str
    params: str
    code: str

    def __init__(self, json_raw) -> None:
        obj = json.loads(json_raw)
        super().__init__(
            type=obj["type"],
            name=obj["name"],
            params=default_str(obj, "params"),
            code=default_str(obj, "code"),
        )

    def is_container(self):
        return self.type in [
            "Module",
            "Sequential",
            "ModuleList",
            "ModuleDict",
            "ParameterList",
        ]


class Model(BaseModel):
    id: int
    name: str
    desc: str
    layers: list[Component]
    loss_fn: Component
    optimizer: Component

    def __init__(self, id, name, desc, loss_fn_raw, optimizer_raw) -> None:
        super().__init__(
            id=id,
            name=name,
            desc=desc,
            layers=[],
            loss_fn=Component(loss_fn_raw),
            optimizer=Component(optimizer_raw),
        )

    def append_layer(self, json_raw) -> None:
        self.layers.append(Component(json_raw))

    def get_source_classname(self):
        return self.name[0].upper() + self.name[1:]

    def get_source_name(self):
        return self.name.lower()


def get_model_from_db(model_id: int, db: Connection) -> Model:
    try:
        cursor = db.cursor()

        cursor.execute(f"SELECT * FROM sys.ML_MODEL WHERE ID={model_id}")
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="model not found")

        model = Model(*result)

        cursor.execute(f"SELECT LAYER FROM sys.ML_MODEL_LAYER WHERE MID={model_id}")
        result = cursor.fetchall()

        for (json_raw,) in result:
            model.append_layer(json_raw)

        return model
    except DatabaseError as e:
        raise HTTPException(status_code=404, detail=f"model not found: {e}")
    finally:
        cursor.close()
