import string
from collections.abc import Mapping
from typing import Any, List, Optional, Type

import peewee as pw
from pydantic.main import (
    BaseConfig,
    BaseModel as PdBaseModel,
    ModelMetaclass,
    inherit_config,
)
from pydantic.utils import GetterDict


def deep_update(d: dict, u: dict) -> dict:
    for k, v in u.items():
        if isinstance(v, Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def letter_hash(obj: Any):
    numbers = str(hash(obj))
    negative = numbers.startswith('-')
    numbers = numbers[negative:]

    letters = ''

    for i in range(0, len(numbers), 2):
        num = int(numbers[i:i+2])
        if num > (len(string.ascii_letters) - 1):
            letters += string.ascii_letters[int(numbers[i])]
            letters += string.ascii_letters[int(numbers[i+1])]
        else:
            letters += string.ascii_letters[num]

    return ''.join(letters)


class _FieldTranslator:
    FIELDS_MAPPING = {
        pw.IntegerField: int,
        pw.FloatField: float,
        pw.BooleanField: bool,
    }

    def __init__(self, field: pw.Field, nest_fk: bool = False, all_optional: bool = False):
        self.field = field
        self.nest_fk = nest_fk
        self.all_optional = all_optional

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

        if not self.is_required or self.all_optional:
            pd_type = Optional[pd_type]

        return pd_type

    @property
    def is_required(self) -> bool:
        return self.field.primary_key or (not self.field.null)


class PwPdMeta(ModelMetaclass):
    def __new__(mcs, cls_name, bases, namespace, **kwargs):
        config = namespace.get('Config', BaseConfig)
        for base in reversed(bases):
            if issubclass(base, PdBaseModel) and base != PdBaseModel:
                config = inherit_config(base.__config__, config)

        # retrieve config values
        pw_model = getattr(config, 'pw_model', None)

        if pw_model is None:
            return super().__new__(mcs, cls_name, bases, namespace, **kwargs)
            # return cls

        pw_fields = set(getattr(
            config,
            'pw_fields',
            set(pw_model._meta.fields.keys()) | set(f.backref for f in pw_model._meta.backrefs.keys())
        ))
        pw_exclude = set(getattr(config, 'pw_exclude', set()))
        exclude_pk = getattr(config, 'pw_exclude_pk', False)
        nest_fk = getattr(config, 'pw_nest_fk', False)
        nest_backrefs = getattr(config, 'pw_nest_backrefs', False)
        all_optional = getattr(config, 'pw_all_optional', False)

        allowed_fields = pw_fields - pw_exclude

        # collect peewee model fields
        fields = dict()
        for name, field in pw_model._meta.fields.items():
            if any((
                name not in allowed_fields,
                name in namespace or name in namespace.get('__annotations__', {}),
                exclude_pk and field.primary_key,
            )):
                continue

            if isinstance(field, pw.ForeignKeyField) and not nest_fk:
                name += '_id'

            fields[name] = _FieldTranslator(field, nest_fk, all_optional)

        # collect backrefs
        if nest_backrefs:
            for field, model in pw_model._meta.backrefs.items():
                if field.backref not in allowed_fields:
                    continue

                fields[field.backref] = List[PwPdModel.make_serializer(model)]

        namespace_new = {'__annotations__': {}}  # create new namespace to keep peewee fields first in order
        for name, type_ in fields.items():
            if isinstance(type_, _FieldTranslator):
                value = type_.field.default
                annotation = type_.pd_type
            else:
                value = None
                annotation = type_

            if value is not None:
                namespace_new[name] = value

            namespace_new['__annotations__'][name] = annotation

        namespace_new = deep_update(namespace_new, namespace)

        return super().__new__(mcs, cls_name, bases, namespace_new, **kwargs)


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
        name = model.__name__ + cls.__name__ + (letter_hash(repr(config_values)) if config_values else '')

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
