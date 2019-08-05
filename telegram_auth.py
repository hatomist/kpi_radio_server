from dataclasses import dataclass, field
from typing import Dict, Union
import pymongo
from functools import wraps
from datetime import datetime
nullable_str = Union[str, None]


class AdminLevel:
    USER = 0
    ADMIN = 1
    SUPER_ADMIN = 2


@dataclass
class TelegramUser:
    _id: int
    mention: nullable_str = None
    first_name: nullable_str = None
    second_name: nullable_str = None
    ban_timestamp: int = 0
    ban_length: int = 0
    admin_level: AdminLevel = AdminLevel.USER
    tokens: Dict[str, int] = field(default_factory=dict)


class TelegramAuth:
    def __init__(self, mongodb_url: str):
        self.__mongodb_client = pymongo.MongoClient(mongodb_url)
        self.__mongodb = self.__mongodb_client['radio']
        self.__users = self.__mongodb['users']

    def get_user(self, user_id: int):
        user = self.__users.find_one({'_id': user_id})
        if user is None:
            return TelegramUser(user_id)
        else:
            return TelegramUser(**user)

    def update_user(self, user: TelegramUser):
        # because it is NOT A PROTECTED MEMBER!!1!!1!! just uid.
        # noinspection PyProtectedMember
        self.__users.replace_one(filter={'_id': user._id}, replacement=user.__dict__, upsert=True)


class ForbiddenError(BaseException):
    def __init__(self, arg='Insufficient permission level'):
        self.message = arg

    def __str__(self):
        return self.message


class BannedError(BaseException):
    def __init__(self, user: TelegramUser = None):
        self.message = 'This user is banned to do this action'
        if user is not None:
            # cause I'll tell it once more - THIS IS NOT A PROTECTED MEMBER!!11!!!1!1
            # noinspection PyProtectedMember
            self.message = f'User {user.first_name or ""} {user.second_name or ""} with id {user._id}'\
                           ' is banned to do this action'

    def __str__(self):
        return self.message


def timestamp():
    return int(datetime.utcnow().timestamp())


def check_admin_level(admin_level: AdminLevel):
    def level_checker(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                user: TelegramUser = kwargs['user']
            except KeyError:
                user: TelegramUser = tuple(filter(lambda x: isinstance(x, TelegramUser), args))[0]
            if user.admin_level < admin_level:
                raise ForbiddenError
            else:
                return func(*args, **kwargs)
        return wrapper
    return level_checker


def check_ban(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            user: TelegramUser = kwargs['user']
        except KeyError:
            user: TelegramUser = tuple(filter(lambda x: isinstance(x, TelegramUser), args))[0]
        if timestamp() < user.ban_length + user.ban_timestamp:
            raise BannedError(user)
        else:
            return func(*args, **kwargs)
    return wrapper
