from fastapiwee.pwpd import PwPdPartUpdateModel
from typing import Any, List

from fastapiwee.crud._base import (BaseDeleteFastAPIView, BaseReadFastAPIView, BaseWriteFastAPIView)


# Read
class RetrieveFastAPIView(BaseReadFastAPIView):
    METHOD = 'GET'
    URL = '/{pk}/'

    def __call__(self, pk: Any):
        return self._get_instance(pk)


# List
class ListFastAPIView(BaseReadFastAPIView):
    METHOD = 'GET'
    URL = '/'

    def __call__(self):
        return list(self._get_query())

    @property
    def response_model(self):
        return List[super().response_model]


# Create
class CreateFastAPIView(BaseWriteFastAPIView):
    METHOD = 'POST'
    URL = '/'

    def __call__(self):
        return self.create()


# Update
class UpdateFastAPIView(BaseWriteFastAPIView):
    METHOD = 'PUT'
    URL = '/{pk}/'

    def __call__(self, pk: Any):
        return self.update(pk)


# Partial update
class PartialUpdateFastAPIView(BaseWriteFastAPIView):
    METHOD = 'PATCH'
    URL = '/{pk}/'

    def __call__(self, pk: Any):
        return self.update(pk, partial=True)

    @property
    def serializer(self):
        if self._serializer is None:
            self._serializer = PwPdPartUpdateModel.make_serializer(self.MODEL)

        return self._serializer


# Delete
class DeleteFastAPIView(BaseDeleteFastAPIView):
    METHOD = 'DELETE'
    URL = '/{pk}/'
