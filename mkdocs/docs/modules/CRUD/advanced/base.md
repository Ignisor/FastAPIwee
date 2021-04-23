# CRUD base

`base` is a module with generic base classes for views.

## `FastAPIView`

Abstract base of all views in that library.

Static attributes:

- `MODEL: pw.Model` - Peewee model for a view
- `_RESPONSE_MODEL: Optional[pd.BaseModel]` - Pydantic model for a response
- `URL: str` - Endpoint URL
- `METHOD: str` - Endpoint method
- `STATUS_CODE: int` - Default 200. Status code for a successful response

Methods:

- `__call__` - abstract method, must be implemented. Main place to put execution logic for a view
- `_get_query` - Default: all model instances (`self.MODEL.select()`). Method to retrieve query. Useful to filter available objects.
- `@property response_model` - Property to retrieve Pydantic model for a response.
- `_get_api_route_params` - Method to retrieve FastAPI route params.
- `add_to_app(app: Union[FastAPI, APIRouter])` - Method to add endpoint to application.
- `make_model_view(model: pw.Model)` - Class method to create new view for a `model` without explicitly defining a class.

## `BaseReadFastAPIView`

Abstract base for "read" action views. Inherits `FastAPIView`.

Methods:

- `@property response_model` - If `_RESPONSE_MODEL` is not specified will make a `PwPdModel` for a specified `MODEL`.
- `_get_instance(pk: Any)` - Method to retrieve instance from query by it's primary key.

## `BaseWriteFastAPIView`

Abstract base for "write" action views. Inherits `BaseReadFastAPIView`.

Static attributes:

- `_SERIALIZER: Optional[pd.BaseModel]` - Pydantic model for a request body serialization.

Attributes:

- `_obj_data` - Instance of pydantic model (from `serializer` property) with data from request body.

Methods:

- `@property serializer` - If `_SERIALIZER` is not specified will make a `PwPdWriteModel` for a specified `MODEL`.
- `create` - Method for create action. Will create an instance of `MODEL` in database with data from `_obj_data` attribute.
- `update(pk: Any, partial: bool = False)` - Method for update action. Will create an update values of `MODEL` in database by it's primary key with data from `_obj_data` attribute. If `partial` is `True` will only use fields that were specified in the request.
- `_get_api_route_params` - Extends default parameters with dependency to set `_obj_data` attribute.

## `BaseDeleteFastAPIView`

Abstract base for "delete" action views. Inherits `BaseReadFastAPIView`.

Static attributes:

- `STATUS_CODE = 204` - `STATUS_CODE` set to [204 No Content](https://developer.mozilla.org/ru/docs/Web/HTTP/Status/204). Since by default no content will be returned in response.

Methods:

- `@property response_model` - Returns None, since no content in response will be returned.
- `__calll__(pk: Any)` - Calls `delete` mothod.
- `delete(pk: Any)` - Deletes a `MODEL` instance by it's primary key. Utilizes `_get_instance` from `BaseReadFastAPIView` to retrieve an instance.
- `_get_api_route_params` - Removes `response_model` from default parameters. And sets `response_class` to `starlette.responses.Response` for empty response.
