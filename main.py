#!/usr/bin/env python
# -*- coding: utf-8 -*-
# main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.router as router
from app.config import database, kernel, settings

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

app.include_router(router.kernel)

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
