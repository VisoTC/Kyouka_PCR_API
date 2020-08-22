import json
import hashlib
from ExceptionHandler import register_ExceptionHandler
from PCR.ReturnClass import *
from orm.damage import Damage
import uvicorn
import orm
import PCR
from config import HTTP_PORT, HTTP_HOST
import time
from eXception import *
from session import Session, inquireList
from datetime import timedelta
import sys
from fastapi import FastAPI, Depends, Request
from redis import register_redis, Redis
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PCR API 服务")
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    'https://pcr.tonyliu.net/'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


register_redis(app)
register_ExceptionHandler(app)


def getRedis() -> Redis:
    return app.state.redis


async def getSession(token: str, redis: Redis = Depends(getRedis)):
    """
    获得会话对象
    """
    if not await redis.expire("KyoukaAPI@%s" % token, 60*15):  # 将未初始化的临时 token 延长有效期
        raise SessionExpiredException
    token = await redis.get("KyoukaAPI@%s" % token)
    if token != "":
        try:
            return Session(token)
        except json.decoder.JSONDecodeError:
            raise APIException("解析 Session 对象发生错误")
    else:
        raise APIException("会话未登录")


@app.get('/')
async def api_root():
    return {
        "Name": "PCR API 服务"
    }


@app.get('/loginCode', dependencies=[Depends(orm.get_db)])
async def getLoginCode(redis: Redis = Depends(getRedis)):
    """
    开始会话
    """
    token = hashlib.sha256(
        (str(int(time.time()*1000)) + "KyoukaAPI").encode()).hexdigest()
    code = hashlib.sha1((str(int(time.time()*1000)) +
                         "KyoukaAPICode").encode()).hexdigest()
    code = code[:8]
    await redis.set("KyoukaAPI@Code@%s" % code, token, expire=30*15)
    return {
        'code': code,
        'token': token
    }


@app.get('/login/{code}')
async def getLoginToken(code: str, redis: Redis = Depends(getRedis)):
    """
    检查会话是否已被确认
    """
    if not await redis.expire("KyoukaAPI@Code@%s" % code, 30):  # 将未初始化的临时 code 延长有效期
        return {
            'state': "EXPIRED"
        }
    token = (await redis.get("KyoukaAPI@Code@%s" % code)).decode()
    a = await redis.expire("KyoukaAPI@%s" % token, 60*15)
    if await redis.exists("KyoukaAPI@%s" % token) == 0:
        return{
            'state': "WAITTING"
        }
    session = await getSession(token, redis)
    return {
        'state': "LOGIN",
        'info': await info(session)
    }


@app.get('/info')
async def info(session: Session = Depends(getSession)):
    """
    获得当前用户信息
    """
    groups = []
    for g in session.groups:
        groups.append({'name': g.name, 'gid': g.gid, 'isAdmin': g.isAdmin})
    return{
        'nickName': session.user.nickName,
        'groups': groups
    }


@app.get('/currentBossInfo', dependencies=[Depends(orm.get_db)])
def currentBossInfo(gid: int, period: str, session: Session = Depends(getSession)):
    """
    获得当前 BOSS 状态
    :param gid: 群 ID
    :param period: 期名
    """
    if not inquireList(gid, session.groups, 'gid'):
        raise APIException("没有权限访问这个群组的信息")
    #
    stage = 1
    step = 1
    damageTotal = 0
    for row in Damage.select().where(Damage.period == period,
                                     Damage.group == str(gid)).order_by(Damage.time.desc()):
        if row.stage > stage:
            stage = row.stage
            step = row.step
            damageTotal = 0
        if row.step > step and row.stage == stage:
            step = row.step
            damageTotal = 0
        if row.stage < stage or row.step < step:
            continue
        damageTotal += row.damage
    #
    info = BossInfoReturn(stage, step, damageTotal, hpIsDamage=True)
    return{
        'stage': info.stage,
        'step': info.step,
        'fullHP': info.fullHP,
        'hp': info.hp
    }


@app.get('/queryDamageAsMember', dependencies=[Depends(orm.get_db)])
def queryDamageAsMember(gid: int, period: str, date: str = None, session: Session = Depends(getSession)):
    """
    查询群内所有成员伤害信息
    若非管理员将只会返回自己的数据
    :param gid: 群 ID
    :param period: 期名
    :param date: 【可选】日期，若输入 all 或者留空查询所有日期，输入 today 查询今日
    """
    group = inquireList(gid, session.groups, 'gid')
    if not group:
        raise APIException("没有权限访问这个群组的信息")
    #
    if date is None:
        today = datetime.now(tz=tz_UTC(8))
        if today.hour < 5:
            today = today - timedelta(hours=5)
        queryStartTime = queryStartTime = datetime(
            today.year, today.month, today.day, 5, 0, 0, tzinfo=tz_UTC(8))
    else:
        if (date == 'all'):
            return allQueryDamageAsMember(gid, period, session)
        else:
            queryStartTime = datetime(
                int(date[0:4]), int(date[4:6]), int(date[6:8]), 5, 0, 0, tzinfo=tz_UTC(8))
    queryEndTime = int(
        (queryStartTime + timedelta(days=1)).timestamp() * 1000)
    queryStartTime = int(queryStartTime.timestamp()*1000)
    DamageLog: List[DamageLogReturn] = []

    if group.isAdmin:
        q = Damage.select().where(Damage.period == period,
                                  Damage.group == gid,
                                  Damage.time >= queryStartTime,
                                  Damage.time < queryEndTime)
    else:
        q = Damage.select().where(Damage.period == period,
                                  Damage.group == gid,
                                  Damage.member == session.user.id,
                                  Damage.time >= queryStartTime,
                                  Damage.time < queryEndTime)

    for row in q:
        DamageLog.append({
            'id': row.id,
            'time': row.time,
            'member': row.member,
            'nickName': session.getNickName(gid, row.member),
            'stage': row.stage,
            'step': row.step,
            'damage': row.damage,
            'kill': row.kill
        })
    return {'total': len(DamageLog), 'allUser': group.isAdmin, 'list': DamageLog}
    #


@app.get('/allQueryDamageAsMember', dependencies=[Depends(orm.get_db)])
def allQueryDamageAsMember(gid: int, period: str, session: Session = Depends(getSession)):
    """
    查询群内所有成员全部伤害信息
    :param gid: 群 ID
    :param period: 期名 
    """
    group = inquireList(gid, session.groups, 'gid')
    if not group:
        raise APIException("没有权限访问这个群组的信息")
    #
    DamageLog: List[DamageLogReturn] = []
    if group.isAdmin:
        q = Damage.select().where(Damage.period == period,
                                  Damage.group == gid)
    else:
        q = Damage.select().where(Damage.period == period,
                                  Damage.member == session.user.id,
                                  Damage.group == gid)
    for row in q:
        DamageLog.append({
            'id': row.id,
            'time': row.time,
            'member': row.member,
            'nickName': session.getNickName(gid, row.member),
            'stage': row.stage,
            'step': row.step,
            'damage': row.damage,
            'kill': row.kill
        })
    return {'total': len(DamageLog), 'allUser': group.isAdmin,
            'list': DamageLog}


if __name__ == '__main__':
    uvicorn.run(app='main:app', host='127.0.0.1',
                port=8000, reload=True, debug=True)
