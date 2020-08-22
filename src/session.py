import re
from typing import List
from fastapi import Query
from fastapi.param_functions import Depends
from redis import Redis
from eXception import *
import json


class SessionUser():
    def __init__(self, id: int, nickName: str, isAdmin=False) -> None:
        self.id = id
        self.nickName = nickName
        self.isAdmin = isAdmin

    @property
    def toDict(self):
        return{
            "id": self.id,
            'nickName': self.nickName
        }


class SessionGroup():
    def __init__(self, gid: int, name: str, isAdmin: bool, own: SessionUser, member: List[SessionUser]) -> None:
        self.gid = gid
        self.name = name
        self.isAdmin = isAdmin
        self.own = own
        self.member = member

    @property
    def toDict(self):
        member = []
        for m in self.member:
            member.append(m.toDict)
        return{
            "gid": self.gid,
            'name': self.name,
            'isAdmin': self.isAdmin,
            'own': self.own,
            'member': member
        }


class Session():
    def __init__(self, sessionString: str) -> None:
        try:
            self._sessionDic = json.loads(sessionString)
        except json.decoder.JSONDecodeError:
            raise APIException("解析 Session 对象发生错误")
        if "user" in self._sessionDic.keys():
            self.user = SessionUser(**{
                'id': self._sessionDic['user']['uid'],
                'nickName': self._sessionDic['user']['nickName']
            })
        else:
            raise APIException("解析 Session 对象发生错误")
        if "groups" in self._sessionDic.keys():
            self.groups = []
            for group in self._sessionDic["groups"]:
                member = []
                for m in group['member']:
                    member.append(SessionUser(
                        m['uid'], m['nickName'], m['isAdmin']))
                self.groups.append(SessionGroup(**{
                    'gid': group['gid'],
                    'name': group['name'],
                    'isAdmin': group['isAdmin'],
                    'own': SessionUser(group["own"]['uid'], group["own"]['nickName']),
                    'member': member
                }))
        else:
            raise APIException("解析 Session 对象发生错误")

    @property
    def toDict(self):
        groups = []
        for g in self.groups:
            groups.append(g.toDict)
        return{
            "name": self.user.toDict,
            'groups': groups
        }

    def getNickName(self, gid, uid):
        for group in self.groups:
            if gid == group.gid:
                for member in group.member:
                    if uid == member.id:
                        return member.nickName
        else:
            return None


def inquireList(value, l: List, key):
    for li in l:
        if value == li.toDict[key]:
            return li
    else:
        return False
