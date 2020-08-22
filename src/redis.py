from fastapi import FastAPI
from aioredis import create_redis_pool, Redis
from eXception import *
import config
def register_redis(app: FastAPI) -> None:
    """
    把redis挂载到app对象上面
    :param app:
    :return:
    """

    @app.on_event('startup')
    async def startup_event():
        """
        获取链接
        :return:
        """
        app.state.redis = await create_redis_pool(config.REDIS_URL)

    @app.on_event('shutdown')
    async def shutdown_event():
        """
        关闭
        :return:
        """
        app.state.redis.close()
        await app.state.redis.wait_closed()