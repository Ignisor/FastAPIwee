import logging
import re
from abc import ABC
from typing import List, Optional

import peewee as pw
from fastapi import APIRouter, FastAPI

from fastapiwee.crud._base import FastAPIView
from fastapiwee.crud.views import (
    CreateFastAPIView,
    DeleteFastAPIView,
    ListFastAPIView,
    PartialUpdateFastAPIView,
    RetrieveFastAPIView,
    UpdateFastAPIView
)


class BaseFastAPIViewSet(ABC):
    VIEWS: Optional[List[FastAPIView]] = None

    def __init__(self, views: Optional[List[FastAPIView]] = None):
        if self.VIEWS is not None and views is not None:
            logging.warning('`VIEWS` class-level constant variable will be ignored, '
                            'since `views` argument is set on initialization.')
        self._views = views or self.VIEWS
        assert self._views, 'Views must be not null nor empty. ' \
                            'Either define `VIEWS` class-level constant variable or `views` argument on initialization.'

        self._router = None

    @property
    def router(self):
        if self._router is None:
            self._router = APIRouter(**self._get_api_router_params())
            for view in self._views:
                view.add_to_app(self._router)

        return self._router

    def _get_api_router_params(self):
        return dict()

    def add_to_app(self, app: FastAPI):
        app.include_router(self.router)


class AutoFastAPIViewSet(BaseFastAPIViewSet):
    _ACTIONS_MAP = {
        'retrieve': RetrieveFastAPIView,
        'list': ListFastAPIView,
        'create': CreateFastAPIView,
        'update': UpdateFastAPIView,
        'part_update': PartialUpdateFastAPIView,
        'delete': DeleteFastAPIView,
    }

    def __init__(
        self,
        model: pw.Model,
        app: FastAPI,
        actions: set = ('retrieve', 'list', 'create', 'update', 'part_update', 'delete'),
    ):
        actions = set(actions)
        self.model = model
        super().__init__(list(self._make_views(actions)))
        self.add_to_app(app)

    def _get_api_router_params(self):
        params = super()._get_api_router_params()
        params |= {
            'prefix': '/' + re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()  # model name to snake_case
        }

        return params

    def _make_views(self, actions: set):
        for action_name in actions:
            action_view = self._ACTIONS_MAP[action_name]
            model_view = action_view.make_model_view(self.model)

            yield model_view()
