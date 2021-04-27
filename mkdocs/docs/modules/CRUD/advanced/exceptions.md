# Exceptions

This module contains generic exception handlers.

## ExceptionHandler

Abstract base for other exception handlers.

Static attributes:

- `EXCEPTION: Type[Exception]` - Exception to handle.

Methods:

- `__call__(request: Request, exc: Exception)` - Handler implementation goes here. Must return response object.
- `@classmethod add_to_app(app: FastAPI)` - Method to add handler to the application.

### Example:

```python
from fastapi import Request, Response
from fastapi.responses import JSONResponse


class CucumberTooSmall(Exception):
    pass


class CucumberExceptionHandler(ExceptionHandler):
    EXCEPTION = CucumberTooSmall

    def __call__(self, request: Request, exc: Exception) -> Response:
        return JSONResponse(
            status_code=400,
            content={
                'msg': 'Cucumber is too small for that action!',
                'type': 'cucumber_small',
            },
        )
```

## NotFoundExceptionHandler

Handles exception `peewee.DoesNotExist`, returns `JSONResponse` with status code `404` ([HTTP Not Found](https://developer.mozilla.org/docs/Web/HTTP/Status/404)).

Implements `__call__` method.

Added to the app automatically when `add_to_app` method on view or viewset used. **Will not be added when `add_to_app` view method used with `fastapi.Router`.**
