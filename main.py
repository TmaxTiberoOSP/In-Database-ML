#!/usr/bin/env python
# -*- coding: utf-8 -*-
# main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

import app.router as router
from app.config import database, kernel, settings
from app.config.tibero import get_db_connection

settings = settings.get()


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init()
    kernel.init(app)
    yield
    await kernel.stop(app)


app = FastAPI(
    title=settings.app_name,
    description="Python Server for In-Database Machine Learning",
    version="0.0.1",
    lifespan=lifespan,
)

app.include_router(router.model)
app.include_router(router.kernel)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    db_conn = [*get_db_connection.__annotations__.keys()]
    db_conn.remove("return")

    def is_with_db_conn(param):
        return not param["name"] in db_conn

    for api in openapi_schema["paths"].values():
        for method in api.values():
            if "parameters" in method:
                method["parameters"] = [*filter(is_with_db_conn, method["parameters"])]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import argparse
    from pathlib import Path

    from uvicorn import run

    parser = argparse.ArgumentParser(description=f"Launch {settings.app_name}")
    parser.add_argument("--dev", action="store_true")
    args = parser.parse_args()

    run(
        f"{Path(__file__).stem}:app",
        host=settings.host,
        port=settings.port,
        reload=args.dev,
    )
