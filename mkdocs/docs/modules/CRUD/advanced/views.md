# Views

Module with generic base views for all CRUD actions: create, retrieve, list, update, partial update and delete.

Any of those views can be created simply using `make_model_view`:
```python
view = RetrieveFastAPIView.make_model_view(peewee.Model)
view.add_to_app(FastAPI)
```

## RetrieveFastAPIView

View that will return object data by it's primary key. Inherits `BaseReadFastAPIView`.

Static attributes:

- `METHOD` - `'GET'`
- `URL` - `'/{pk}/'` model primary key (`pk`) as URL parameter.

Implements:

- `__call__(pk: Any)` - accepts primary key from URL parameter. Utilizes `_get_instance` from `BaseReadFastAPIView` to retrieve instance.

### Example

```python
import peewee as pw
import pydantic as pd
from fastapi import FastAPI
from fastapiwee.crud.views import RetrieveFastAPIView
from fastapiwee.pwpd import PwPdModel

DB = pw.SqliteDatabase(':memory:')


class Cucumber(pw.Model):
    id = pw.AutoField()
    size = pw.IntegerField()
    taste = pw.CharField(null=True)

    class Meta:
        database = DB


class CucumberData(PwPdModel):
    class Config:
        pw_model = Cucumber

    @pd.validator('size')
    def validate_size(cls, v, **kwargs):
        """Make sure size is big enough"""
        return v ** 2


class CucumberRetrieveView(RetrieveFastAPIView):
    MODEL = Cucumber
    _RESPONSE_MODEL = CucumberData

    def _get_instance(self, pk: int) -> pw.Model:
        """Mock data to not use a database"""
        return Cucumber(
            id=pk,
            size=10,
            taste='tasty',
        )


app = FastAPI()

CucumberRetrieveView().add_to_app(app)
```

## ListFastAPIView

View that will return list of all objects from `_get_query` method. Inherits `BaseReadFastAPIView`.

Static attributes:

- `METHOD` - `'GET'`
- `URL` - `'/'`

Implements:

- `__call__` - Utilizes `_get_query` from `FastAPIView` to retrieve query and converts it to list.
- `@property response_model` - wraps base `response_model` to List.

### Example

```python
import peewee as pw
import pydantic as pd
from fastapi import FastAPI
from fastapiwee.crud.views import ListFastAPIView
from fastapiwee.pwpd import PwPdModel

DB = pw.SqliteDatabase(':memory:')


class Cucumber(pw.Model):
    id = pw.AutoField()
    size = pw.IntegerField()
    taste = pw.CharField(null=True)

    class Meta:
        database = DB


class CucumberData(PwPdModel):
    class Config:
        pw_model = Cucumber

    @pd.validator('size')
    def validate_size(cls, v, **kwargs):
        """Make sure size is big enough"""
        return v ** 2


class CucumberListView(ListFastAPIView):
    MODEL = Cucumber
    _RESPONSE_MODEL = CucumberData

    def _get_query(self):
        """Mock data to not use a database"""
        return (Cucumber(
            id=i,
            size=10 + i,
            taste='tasty',
        ) for i in range(10))


app = FastAPI()

CucumberListView().add_to_app(app)
```

## CreateFastAPIView

View that will create new object. Inherits `BaseWriteFastAPIView`.

Static attributes:

- `METHOD` - `'POST'`
- `URL` - `'/'`
- `STATUS_CODE` - [`201` Created](https://developer.mozilla.org/ru/docs/Web/HTTP/Status/201)

Implements:

- `__call__` - Calls `create` method. Default implementation in `BaseWriteFastAPIView`.

### Example

```python
import peewee as pw
import pydantic as pd
from fastapi import FastAPI
from fastapiwee.crud.views import CreateFastAPIView
from fastapiwee.pwpd import PwPdWriteModel

DB = pw.SqliteDatabase(':memory:')


class Cucumber(pw.Model):
    id = pw.AutoField()
    size = pw.IntegerField()
    taste = pw.CharField(null=True)

    class Meta:
        database = DB


class CucumberData(PwPdWriteModel):
    class Config:
        pw_model = Cucumber

    @pd.validator('size')
    def validate_size(cls, v, **kwargs):
        """Make sure size is big enough"""
        if v < 10:
            raise ValueError(f'Size {v} is too small. Should be at least 10')
        return v


class CucumberCreateView(CreateFastAPIView):
    MODEL = Cucumber
    _SERIALIZER = CucumberData

    def create(self) -> pw.Model:
        """Create DB tables before execution"""
        DB.create_tables([Cucumber])
        return super().create()


app = FastAPI()

CucumberCreateView().add_to_app(app)
```

## UpdateFastAPIView

View that will update all fields of the object. Inherits `BaseWriteFastAPIView`.

Static attributes:

- `METHOD` - `'PUT'`
- `URL` - `'/{pk}/'` model primary key (`pk`) as URL parameter.

Implements:

- `__call__` - Calls `update` method. Default implementation in `BaseWriteFastAPIView`.

### Example

```python
import peewee as pw
import pydantic as pd
from fastapi import FastAPI
from fastapiwee.crud.views import UpdateFastAPIView
from fastapiwee.pwpd import PwPdWriteModel

DB = pw.SqliteDatabase(':memory:')


class Cucumber(pw.Model):
    id = pw.AutoField()
    size = pw.IntegerField()
    taste = pw.CharField(null=True)

    class Meta:
        database = DB


class CucumberData(PwPdWriteModel):
    class Config:
        pw_model = Cucumber

    @pd.validator('size')
    def validate_size(cls, v, **kwargs):
        """Make sure size is big enough"""
        if v < 10:
            raise ValueError(f'Size {v} is too small. Should be at least 10')
        return v


class CucumberUpdateView(UpdateFastAPIView):
    MODEL = Cucumber
    _SERIALIZER = CucumberData

    def __call__(self, pk):
        """Create DB tables and dummy data before execution"""
        DB.create_tables([Cucumber])

        for i in range(10):
            Cucumber.create(
                size=i,
                taste='tasty',
            )

        return super().__call__(pk)


app = FastAPI()

CucumberUpdateView().add_to_app(app)
```

## PartialUpdateFastAPIView

View that will update specified fields of the object (all fields are not required). Inherits `BaseWriteFastAPIView`.

Static attributes:

- `METHOD` - `'PATCH'`
- `URL` - `'/{pk}/'` model primary key (`pk`) as URL parameter.

Implements:

- `__call__` - Calls `update` method with argument `partial = True`. Default implementation in `BaseWriteFastAPIView`.
- `@property serializer` - If `_SERIALIZER` is not specified will make a `PwPdPartUpdateModel` for a specified `MODEL`.

### Example

```python
import peewee as pw
import pydantic as pd
from fastapi import FastAPI
from fastapiwee.crud.views import PartialUpdateFastAPIView
from fastapiwee.pwpd import PwPdPartUpdateModel

DB = pw.SqliteDatabase(':memory:')


class Cucumber(pw.Model):
    id = pw.AutoField()
    size = pw.IntegerField()
    taste = pw.CharField(null=True)

    class Meta:
        database = DB


class CucumberData(PwPdPartUpdateModel):
    class Config:
        pw_model = Cucumber

    @pd.validator('size')
    def validate_size(cls, v, **kwargs):
        """Make sure size is big enough"""
        if v < 10:
            raise ValueError(f'Size {v} is too small. Should be at least 10')
        return v


class CucumberPartUpdateView(PartialUpdateFastAPIView):
    MODEL = Cucumber
    _SERIALIZER = CucumberData

    def __call__(self, pk):
        """Create DB tables and dummy data before execution"""
        DB.create_tables([Cucumber])

        for i in range(10):
            Cucumber.create(
                size=i,
                taste='tasty',
            )

        return super().__call__(pk)


app = FastAPI()

CucumberPartUpdateView().add_to_app(app)
```

## DeleteFastAPIView

View that will delete object by it's primary key. Inherits `BaseDeleteFastAPIView`.

Static attributes:

- `METHOD` - `'DELETE'`
- `URL` - `'/{pk}/'` model primary key (`pk`) as URL parameter.

### Example

```python
import peewee as pw
from fastapi import FastAPI, HTTPException
from fastapiwee.crud.views import DeleteFastAPIView

DB = pw.SqliteDatabase(':memory:')


class Cucumber(pw.Model):
    id = pw.AutoField()
    size = pw.IntegerField()
    taste = pw.CharField(null=True)

    class Meta:
        database = DB


class CucumberDeleteView(DeleteFastAPIView):
    MODEL = Cucumber

    def __call__(self, pk):
        """Create DB tables and dummy data before execution"""
        DB.create_tables([Cucumber])

        for i in range(20):
            Cucumber.create(
                size=i,
                taste='tasty',
            )

        return super().__call__(pk)

    def delete(self, pk):
        instance = self._get_instance(pk)
        if instance.size > 10:
            raise HTTPException(400, 'That Cucumber is too big for you to delete it')
        instance.delete_instance()


app = FastAPI()

CucumberDeleteView().add_to_app(app)
```
