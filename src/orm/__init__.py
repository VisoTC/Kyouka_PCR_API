from fastapi import Depends
from peewee import Model, MySQLDatabase, _ConnectionState
from config import MYSQL_CONNENT
from contextvars import ContextVar

# 异步修复 by FastAPI
db_state_default = {"closed": None, "conn": None,
                    "ctx": None, "transactions": None}
db_state = ContextVar("db_state", default=db_state_default.copy())


class PeeweeConnectionState(_ConnectionState):
    def __init__(self, **kwargs):
        super().__setattr__("_state", db_state)
        super().__init__(**kwargs)

    def __setattr__(self, name, value):
        self._state.get()[name] = value

    def __getattr__(self, name):
        return self._state.get()[name]


db = MySQLDatabase(**MYSQL_CONNENT)
db._state = PeeweeConnectionState()


async def reset_db_state():
    db._state._state.set(db_state_default.copy())
    db._state.reset()


def get_db(db_state=Depends(reset_db_state)):
    try:
        db.connect()
        yield
    finally:
        if not db.is_closed():
            db.close()

# END: 异步修复 by FastAPI


class BaseModel(Model):

    class Meta:
        database = db
