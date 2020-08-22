from fastapi import FastAPI
from fastapi.responses import JSONResponse
from eXception import *
from fastapi.exceptions import RequestValidationError,ValidationError,HTTPException

def register_ExceptionHandler(app: FastAPI) -> None:
    @app.exception_handler(RedisException)
    async def _(request, exc):
        return JSONResponse(
            status_code=500, content={
                'errCode': -10,
                "errMsg": "连接 redis 错误"
            })

    @app.exception_handler(SessionExpiredException)
    async def _(request, exc):
        return JSONResponse(
            status_code=401, content={
                'errCode': -1,
                "errMsg": "会话已过期"
            })

    @app.exception_handler(ValidationError)
    async def _(request, exc):
        return JSONResponse(
            status_code=422, content={
                'errCode': 422,
                "errMsg": "请求参数错误",
                "detail": str(exc)
            })

    @app.exception_handler(RequestValidationError)
    async def _(request, exc):
        return JSONResponse(
            status_code=422, content={
                'errCode': 422,
                "errMsg": "请求参数错误",
                "detail": str(exc)
            })
    @app.exception_handler(HTTPException)
    async def _(request, exc):
        return JSONResponse(
            status_code=500, content={
                'errCode': 500,
                "errMsg": "Internal Server Error",
                "detail": str(exc)
            })
