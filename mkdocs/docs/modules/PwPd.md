# PwPd module

PwPd - PeeweePydantic.
Module with adapters for transfering Peewee models to Pydantic models (a.k.a. serializer).

## PwPdModel

Base class for PwPd models adapters.

Inherits Pydantic `BaseModel` and thus supports Pydantic features.

### Config

Same as Pydantic models, behaviour of `PwPdModel` can be controlled via the Config class on a model.
For available Pydantic options refer to [Pydantic documentation](https://pydantic-docs.helpmanual.io/usage/model_config/).

Next Pydantic config options are set on `PwPdModel`:

- `orm_mode = True` - Required to work with ORM model such as Peewee.
- `extra = 'forbid'` - Will cause validation to fail if extra attributes are included.
- `getter_dict = PwPdGetterDict` - Custom getter dict to handle backrefs.

#### Additional PwPd options:

- `pw_model: Type[peewee.Model]`

    Required. Used to specify Peewee model for adapter.

- `pw_fields: set`

    Set of PeeWee model fields to add to the Pydantic model. If not specified - all fields are used.

- `pw_exclude: set`

    Set of PeeWee model fields to exclude from the the Pydantic model. If not specified - no fields are excluded.

- `pw_exclude_pk: bool`

    Default - `False`. Whether to exclude primary key field from Pydantic model or not. Used for "write" models (create/update).

- `pw_nest_fk: bool`

    Default - `False`. Whether to nest model data by foreign key or only return it's primary key value.

- `pw_nest_backrefs: bool`

    Default - `False`. Whether to nest backrefs data or ignore backrefs.

- `pw_all_optional: bool`

    Default - `False`. Wheter to set all fields optional or not. Used for partial update models, where any number of fields can be specified.

### Creating PwPd model

#### Defining model class

You can define a model class using PwPdModel as a base class. Defining a PwPdModel is similar to [defining Pydantic model](https://pydantic-docs.helpmanual.io/usage/models/). The only difference is `Config` options and automated definition of fields. You only need to define fields which behaviour you want to change.

It is required to set `pw_model` option in `Config` class.

Minimal usage example:

```python
class CucumberPwPdModel(PwPdModel):
    class Config:
        pw_model: peewee.Model = Cucumber
```

More complex example:

```python
import peewee as pw
from fastapiwee.pwpd import PwPdModel

DB = pw.SqliteDatabase(':memory:')


class TestModel(pw.Model):
    id = pw.AutoField()
    text = pw.TextField()
    number = pw.IntegerField(null=True)
    is_test = pw.BooleanField(default=True)

    class Meta:
        database = DB


# Define a PwPdModel (a.k.a. serializer)
class TestPwPdModel(PwPdModel):
    text: str = 'Something default'

    class Config:
        pw_model = TestModel
        pw_exclude_pk = True


# `text` field now has a default value and not required to specify
validated_data = TestPwPdModel(number=23)
new_instance = TestModel(**validated_data.dict())

assert new_instance.text == 'Something default'
assert new_instance.number == 23
```

#### Using make_serializer class method

`make_serializer` method can be used to create a generic Pydantic model from Peewee model. Method arguments can be used to override any of the `Config` options.

Usage: `PwPdModel.make_serializer(peewee.Model, **config_options)`

_Example:_

- Define a model:

    ```python
    import peewee as pw

    DB = pw.SqliteDatabase('/tmp/fastapiwee_example.db')


    class TestModel(pw.Model):
        id = pw.AutoField()
        text = pw.TextField()
        number = pw.IntegerField(null=True)
        is_test = pw.BooleanField(default=True)

        class Meta:
            database = DB
    ```

- Make a simple serializer and try it:

    ```python hl_lines="2 17-33"
    import peewee as pw
    from fastapiwee.pwpd import PwPdModel

    DB = pw.SqliteDatabase(':memory:')


    class TestModel(pw.Model):
        id = pw.AutoField()
        text = pw.TextField()
        number = pw.IntegerField(null=True)
        is_test = pw.BooleanField(default=True)

        class Meta:
            database = DB


    test_instance = TestModel(
        id=1,
        text='Cucumber',
        number=123,
    )

    # Make a simple serializer
    serializer = PwPdModel.make_serializer(TestModel)

    # Try it
    data = serializer.from_orm(test_instance)
    assert data.dict() == {
        'id': 1,
        'text': 'Cucumber',
        'number': 123,
        'is_test': True,
    }
    ```

- Make a customized serializer and try it:

    ```python hl_lines="35-45"
    import peewee as pw
    from fastapiwee.pwpd import PwPdModel

    DB = pw.SqliteDatabase(':memory:')


    class TestModel(pw.Model):
        id = pw.AutoField()
        text = pw.TextField()
        number = pw.IntegerField(null=True)
        is_test = pw.BooleanField(default=True)

        class Meta:
            database = DB


    test_instance = TestModel(
        id=1,
        text='Cucumber',
        number=123,
    )

    # Make a simple serializer
    serializer = PwPdModel.make_serializer(TestModel)

    # Try it
    data = serializer.from_orm(test_instance)
    assert data.dict() == {
        'id': 1,
        'text': 'Cucumber',
        'number': 123,
        'is_test': True,
    }

    # Make customized serializer
    serializer = PwPdModel.make_serializer(
        TestModel,
        pw_exclude_pk=True,
        pw_exclude={'is_test'},
        anystr_lower=True
    )

    # Try it
    data = serializer.from_orm(test_instance)
    assert data.dict() == {'text': 'cucumber', 'number': 123}
    ```

## Other base PwPd models

Module also contains another base classes that are inherit default PwPdModel (thus `make_serializer` can be used on them as well). The only difference is a default `Config` values.

### PwPdWriteModel

Base to create models for write actions (create/update). Excludes primary key field, will not nest foreign keys and backrefs.

Has next config:

```python
class Config:
    pw_exclude_pk = True
    pw_nest_fk = False
    pw_nest_backrefs = False
```

### PwPdPartialUpdateModel

Base to create models for partial update actions (e.g. `PATCH`). Inherits config from PwPdWriteModel, but all fields will be optional.

Has next config:

```python
class Config:
    pw_all_optional = True
```

## Factory

`PwPdModelFactory` class can be used to create "read" and "write" PwPd models for a single Peewee model.

Usage:
```python
from fastapiwee.pwpd import PwPdModelFactory

pwpd_factory = PwPdModelFactory(peewee.Model)

# equals to PwPdModel.make_serializer(peewee.Model)
read_serializer = pwpd_factory.read_pd()

# equals to PwPdWriteModel.make_serializer(peewee.Model)
write_serializer = pwpd_factory.write_pd()
```
