"""Safe additive error envelope; preserve the legacy detail field."""

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse


class OrbitalAPIError(HTTPException):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(status, message)
        self.code = code


async def orbital_error_handler(request: Request, error: OrbitalAPIError):
    return JSONResponse(
        status_code=error.status_code,
        content={
            "detail": error.detail,
            "error": {"code": error.code, "message": error.detail},
        },
    )


async def request_error_handler(request: Request, error: RequestValidationError):
    # Never echo submitted input, context objects, credentials or exception strings.
    issues = [
        {"loc": list(e["loc"]), "type": e["type"], "msg": "Invalid value"}
        for e in error.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "detail": issues,
            "error": {
                "code": "request_validation",
                "message": "Invalid request parameters",
                "issues": issues,
            },
        },
    )


async def response_error_handler(request: Request, error: ResponseValidationError):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Scientific response could not be validated",
            "error": {
                "code": "response_validation",
                "message": "Scientific response could not be validated",
            },
        },
    )
