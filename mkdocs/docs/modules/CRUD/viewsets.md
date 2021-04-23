# Viewsets

Viewset is a collection of views. Simplest usecase is to use `AutoFastAPIViewSet` to create a CRUD endpoints for a peewee model.

## AutoFastAPIViewSet

Will automatically make default create, retrieve, list, update, partial update and delete API endpoints for the specified Peewee model.

### Usage

```python
AutoFastAPIViewSet(model: Type[peewee.Model], app: FastAPI, actions: Optional[Set[str]])
```

- `model: Type[peewee.Model]` - Peewee model for which endpoints will be created.
- `app: FastAPI` - FastAPI application
- `actions: Set[str]` - Optional. Set of actions, possible values: 'retrieve', 'list', 'create', 'update', 'part_update', 'delete'.

### Actions

- `retrieve`

    **HTTP method:** `GET` <br>
    **URL:** `/{model_name}/{pk}/` <br>
    Retrieve an instance data by it's primary key.

- `list`

    **HTTP method:** `GET` <br>
    **URL:** `/{model_name}/` <br>
    Retrieve a list of all instances data.

- `create`

    **HTTP method:** `POST` <br>
    **URL:** `/{model_name}/` <br>
    **Request body:** JSON data <br>
    Create a new model instance.

- `update`

    **HTTP method:** `PUT` <br>
    **URL:** `/{model_name}/{pk}/` <br>
    **Request body:** JSON data <br>
    Full update of a model instance by it's primary key.

- `part_update`

    **HTTP method:** `PATCH` <br>
    **URL:** `/{model_name}/{pk}/` <br>
    **Request body:** JSON data <br>
    Partial update of a model instance by it's primary key. (Only specified fields will be updated).

- `delete`

    **HTTP method:** `DELETE` <br>
    **URL:** `/{model_name}/{pk}/` <br>
    Delete a model instance by it's primary key.


### Example

```python
import peewee as pw
from fastapi import FastAPI
from fastapiwee import AutoFastAPIViewSet

DB = pw.SqliteDatabase(':memory:')


class TestModel(pw.Model):
    id = pw.AutoField()
    text = pw.TextField()
    number = pw.IntegerField(null=True)
    is_test = pw.BooleanField(default=True)

    class Meta:
        database = DB


app = FastAPI()

AutoFastAPIViewSet(TestModel, app)
```

That will create next endpoints:

- `GET` `/test_model/{pk}/`<br>
    **Response:**<br>
    `200`<br>
    ```JSON
    {
        "id": 0,
        "text": "string",
        "number": 0,
        "is_test": true
    }
    ```

- `GET` `/test_model/`<br>
    **Response:**<br>
    `200`<br>
    ```JSON
    [
        {
            "id": 0,
            "text": "string",
            "number": 0,
            "is_test": true
        }
    ]
    ```

- `POST` `/test_model/`<br>
    **Body:**<br>
    ```JSON
    {
        "text": "string",
        "number": 0,
        "is_test": true
    }
    ```
    **Response:**<br>
    `201`<br>
    ```JSON
    [
        {
            "id": 0,
            "text": "string",
            "number": 0,
            "is_test": true
        }
    ]
    ```

- `PUT` `/test_model/{pk}`<br>
    **Body:**<br>
    ```JSON
    {
        "text": "string",
        "number": 0,
        "is_test": true
    }
    ```
    **Response:**<br>
    `200`<br>
    ```JSON
    {
        "id": 0,
        "text": "string",
        "number": 0,
        "is_test": true
    }
    ```

- `PATCH` `/test_model/{pk}`<br>
    **Body:**<br>
    ```JSON
    {
        "text": "string",
        "number": 0,
        "is_test": true
    }
    ```
    **Response:**<br>
    `200`<br>
    ```JSON
    {
        "id": 0,
        "text": "string",
        "number": 0,
        "is_test": true
    }
    ```

- `DELETE` `/test_model/{pk}`<br>
    **Response:**<br>
    `204`

For a more detailed example refer to [example.py](https://github.com/Ignisor/FastAPIwee/blob/main/example.py)

## BaseFastAPIViewSet

For a more specific usecases you can extend or use `BaseFastAPIViewSet` class. It takes views as input and will create a router and add it to the app.

### Usage

```python
BaseFastAPIViewSet(views: List[Type[FastAPIView]]).add_to_app(app: FastAPI)
```

- `views: List[Type[FastAPIView]]` - List of views to add to the app.
- `app: FastAPI` - FastAPI app to which views will be added.

### Example

`BaseFastAPIViewSet` can be used to define views with custom serializers and logic. User creation for example.

```python
import peewee as pw
import pydantic as pd
from fastapi import FastAPI
from fastapiwee.crud.views import CreateFastAPIView, RetrieveFastAPIView
from fastapiwee.crud.viewsets import BaseFastAPIViewSet
from fastapiwee.pwpd import PwPdWriteModel

DB = pw.SqliteDatabase(':memory:')


class User(pw.Model):
    id = pw.AutoField()
    email = pw.TextField()
    password = pw.TextField()  # Never store passwords as an unencrypted plain text data
    bio = pw.TextField(null=True)

    class Meta:
        database = DB


class SignUpData(PwPdWriteModel):
    password2: str

    class Config:
        pw_model = User
        pw_exclude = {'bio'}

    @pd.validator('email')
    def check_email(cls, v, **kwargs):
        """Simple and dumb email validator for example"""
        if '@' not in v:
            raise ValueError('invalid email')

        return v

    @pd.validator('password2')
    def passwords_match(cls, v, values, **kwargs):
        if v != values['password']:
            raise ValueError('passwords do not match')
        return v


class SignUpView(CreateFastAPIView):
    MODEL = User
    _SERIALIZER = SignUpData

    def create(self) -> pw.Model:
        DB.create_tables([User])
        return self.MODEL.create(**self._obj_data.dict(exclude={'password2'}))


app = FastAPI()

viewset = BaseFastAPIViewSet(views=[SignUpView, RetrieveFastAPIView.make_model_view(User)])
viewset.add_to_app(app)
```
