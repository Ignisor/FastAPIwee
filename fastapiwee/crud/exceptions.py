from abc import ABC
from typing import Type

import peewee as pw
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse


class ExceptionHandler(ABC):
    EXCEPTION: Type[Exception]

    def __call__(self, request: Request, exc: Exception) -> Response:
        raise NotImplementedError

    @classmethod
    def add_to_app(cls, app: FastAPI):
        app.add_exception_handler(cls.EXCEPTION, cls())


class NotFoundExceptionHandler(ExceptionHandler):
    EXCEPTION = pw.DoesNotExist

    def __call__(self, request: Request, exc: Exception) -> Response:
        return JSONResponse(
            status_code=404,
            content={
                'msg': 'Instance not found',
                'type': 'not_found',
            },
        )
