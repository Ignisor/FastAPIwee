from typing import Any, List, Optional, Type

import peewee as pw
from pydantic.fields import Undefined
from pydantic.main import (
    BaseModel as PdBaseModel,
    ModelField as PdModelField,
    ModelMetaclass,
)
from pydantic.utils import GetterDict


class _FieldTranslator:
    FIELDS_MAPPING = {
        pw.IntegerField: int,
        pw.FloatField: float,
        pw.BooleanField: bool,
    }

    def __init__(self, field: pw.Field, nest_fk: bool = False):
        self.field = field
        self.nest_fk = nest_fk

    @property
    def pd_type(self) -> str:
        field = self.field

        if isinstance(self.field, pw.ForeignKeyField):
            if self.nest_fk:
                return PwPdModel.make_serializer(self.field.rel_model)

            field = self.field.rel_field

        for field_ancestor in field.__class__.__mro__:
            pd_type = self.FIELDS_MAPPING.get(field_ancestor)
            if pd_type is not None:
                break
        else:
            pd_type = str

        if not self.is_required:
            pd_type = Optional[pd_type]

        return pd_type

    @property
    def is_required(self) -> bool:
        return self.field.primary_key or (not self.field.null)


class PwPdMeta(ModelMetaclass):
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # retrieve config values
        pw_model = getattr(cls.__config__, 'pw_model', None)

        if pw_model is None:
            return cls

        pw_fields = set(getattr(
            cls.__config__,
            'pw_fields',
            set(pw_model._meta.fields.keys()) | set(f.backref for f in pw_model._meta.backrefs.keys())
        ))
        pw_exclude = set(getattr(cls.__config__, 'pw_exclude', set()))
        exclude_pk = getattr(cls.__config__, 'pw_exclude_pk', False)
        nest_fk = getattr(cls.__config__, 'pw_nest_fk', False)
        nest_backrefs = getattr(cls.__config__, 'pw_nest_backrefs', False)
        all_optional = getattr(cls.__config__, 'pw_all_optional', False)

        allowed_fields = pw_fields - pw_exclude

        # collect peewee model fields
        fields = dict()
        for name, field in pw_model._meta.fields.items():
            if any((
                name not in allowed_fields,
                name in cls.__fields__,
                exclude_pk and field.primary_key,
            )):
                continue

            if isinstance(field, pw.ForeignKeyField) and not nest_fk:
                name += '_id'

            fields[name] = _FieldTranslator(field, nest_fk)

        # collect backrefs
        if nest_backrefs:
            for field, model in pw_model._meta.backrefs.items():
                if field.backref not in allowed_fields:
                    continue

                fields[field.backref] = List[PwPdModel.make_serializer(model)]

        # populate peewee model fields for pydantic model
        for name, type_ in fields.items():
            if isinstance(type_, _FieldTranslator):
                value = type_.field.default
                annotation = type_.pd_type
            else:
                value = None
                annotation = type_

            cls.__fields__[name] = PdModelField.infer(
                name=name,
                value=Undefined if value is None else value,
                annotation=annotation,
                class_validators={},
                config=cls.__config__,
            )
            if all_optional:
                cls.__fields__[name].required = False

        return cls


class PwPdGetterDict(GetterDict):
    def get(self, key: Any, default: Any) -> Any:
        res = getattr(self._obj, key, default)
        if isinstance(res, pw.ModelSelect):  # handle backrefs
            return list(res)
        return res


class PwPdModel(PdBaseModel, metaclass=PwPdMeta):
    __CACHE = dict()

    class Config:
        extra = 'forbid'
        orm_mode = True
        getter_dict = PwPdGetterDict

    @classmethod
    def make_serializer(cls, model: Type[pw.Model], **config_values) -> Type['PwPdModel']:
        name = model.__name__ + cls.__name__

        if name not in cls.__CACHE:
            class Config:
                pw_model = model

            for key, value in config_values.items():
                if key == 'pw_model':
                    raise ValueError('`pw_model` can not be overriden with config values, use `model` argument')

                setattr(Config, key, value)

            cls.__CACHE[name] = type(name, (cls, ), {'Config': Config})

        return cls.__CACHE[name]


class PwPdWriteModel(PwPdModel):
    """Shortcut for write model config"""
    class Config:
        pw_exclude_pk = True
        pw_nest_fk = False
        pw_nest_backrefs = False


class PwPdPartUpdateModel(PwPdWriteModel):
    """Shortcut for update model config (nothing is required)"""
    class Config:
        pw_all_optional = True


class PwPdModelFactory:
    def __init__(self, model: pw.ModelBase):
        self._model = model
        self._read_pd = None
        self._write_pd = None

    @property
    def model(self):
        return self._model

    @property
    def read_pd(self):
        if self._read_pd is None:
            self._read_pd = PwPdModel.make_serializer(
                self._model
            )

        return self._read_pd

    @property
    def write_pd(self):
        if self._write_pd is None:
            self._write_pd = PwPdWriteModel.make_serializer(
                self._model,
            )

        return self._write_pd
