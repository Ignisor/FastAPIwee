from abc import ABC, ABCMeta
import re

from fastapi.params import Depends
from starlette.responses import Response
from fastapiwee.pwpd import PwPdModelFactory
from typing import Any, Optional, Union

import peewee as pw
import pydantic as pd
from fastapi import FastAPI, APIRouter


class FastAPIView(ABC):
    MODEL: pw.Model
    _RESPONSE_MODEL: Optional[pd.BaseModel] = None
    URL: str
    METHOD: str
    STATUS_CODE: int = 200

    def __init__(self):
        self._response_model = self._RESPONSE_MODEL

    def __call__(self) -> Any:
        raise NotImplementedError

    def _get_query(self):
        return self.MODEL.select()

    @property
    def response_model(self):
        raise NotImplementedError

    def _get_api_route_params(self) -> dict:
        return {
            'path': self.URL,
            'endpoint': self,
            'methods': [self.METHOD],
            'response_model': self.response_model,
            'status_code': self.STATUS_CODE,
            'name': re.sub(r'(?<!^)(?=[A-Z])', '_', self.__class__.__name__.replace('FastAPIView', '')).lower(),
        }

    def add_to_app(self, app: Union[FastAPI, APIRouter]):
        app.add_api_route(
            **self._get_api_route_params()
        )

    @classmethod
    def make_model_view(cls, model):
        return type(model.__name__ + cls.__name__, (cls, ), {'MODEL': model})


class BaseReadFastAPIView(FastAPIView, metaclass=ABCMeta):
    @property
    def response_model(self):
        if self._response_model is None:
            self._response_model = PwPdModelFactory(self.MODEL).read_pd

        return self._response_model

    def _get_instance(self, pk: Any) -> pw.Model:
        return self._get_query().where(self.MODEL._meta.primary_key == pk).get()


class BaseWriteFastAPIView(BaseReadFastAPIView, metaclass=ABCMeta):
    _SERIALIZER: Optional[pd.BaseModel] = None

    def __init__(self):
        super().__init__()
        self._serializer = self._SERIALIZER
        self._obj_data = None

    @property
    def serializer(self):
        if self._serializer is None:
            self._serializer = PwPdModelFactory(self.MODEL).write_pd

        return self._serializer

    def create(self) -> pw.Model:
        return self.MODEL.create(**self._obj_data.dict())

    def update(self, pk: Any, partial=False) -> pw.Model:
        instance = self._get_instance(pk)
        for name, value in self._obj_data.dict(exclude_unset=partial).items():
            setattr(instance, name, value)

        instance.save()

        return instance

    def _get_api_route_params(self) -> dict:
        def data_dependency(data: self.serializer):
            self._obj_data = data

        params = super()._get_api_route_params()
        params |= {
            'dependencies': [Depends(data_dependency)],
        }

        return params


class BaseDeleteFastAPIView(BaseReadFastAPIView):
    STATUS_CODE = 204

    @property
    def response_model(self):
        return None

    def __call__(self, pk: Any):
        self.delete(pk)

    def delete(self, pk):
        instance = self._get_instance(pk)
        instance.delete_instance()

    def _get_api_route_params(self) -> dict:
        params = super()._get_api_route_params()
        del params['response_model']
        params |= {
            'response_class': Response
        }

        return params
