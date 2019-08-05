from dataclasses import dataclass, field
from typing import Dict, Union
import pymongo
from functools import wraps
from datetime import datetime
nullable_str = Union[str, None]
# TODO: add counters for approved and disapproved songs... and maybe something else


class AdminLevel:
    USER = 0
    ADMIN = 1
    SUPER_ADMIN = 2


@dataclass
class UserData:
    _id: int
    mention: nullable_str = None
    first_name: nullable_str = None
    second_name: nullable_str = None
    ban_timestamp: int = 0
    ban_length: int = 0
    admin_level: int = AdminLevel.USER
    tokens: Dict[str, int] = field(default_factory=dict)


class TelegramAuth:
    def __init__(self, mongodb_url: str):
        self.__mongodb_client = pymongo.MongoClient(mongodb_url)
        self.__mongodb = self.__mongodb_client['radio']
        self.__users = self.__mongodb['users']

    def get_user(self, user_id: int, is_authorized: bool = False):
        user = self.__users.find_one({'_id': user_id})
        if user is None:
            return TelegramUser(UserData(user_id), self, is_authorized)
        else:
            return TelegramUser(UserData(**user),  self, is_authorized)

    def update_user(self, user: UserData):
        # because it is NOT A PROTECTED MEMBER!!1!!1!! just uid.
        # noinspection PyProtectedMember
        self.__users.replace_one(filter={'_id': user._id}, replacement=user.__dict__, upsert=True)


# cause fuck you PyCharm
# noinspection PyProtectedMember
class TelegramUser:
    def __init__(self, user_data: UserData, telegram_auth: TelegramAuth, is_authorized: bool = False):
        self.__user_data: UserData = user_data
        self.__ta: TelegramAuth = telegram_auth
        self.__is_authorized = is_authorized

    def __update_data(self):
        self.__ta.update_user(self.__user_data)

    def ban(self, length: int):
        cur_time = timestamp()
        self.__user_data.ban_timestamp = cur_time
        self.__user_data.ban_length = cur_time + length
        self.__update_data()

    def set_first_name(self, name: str):
        self.__user_data.first_name = name
        self.__update_data()

    def set_second_name(self, second_name: str):
        self.__user_data.second_name = second_name
        self.__update_data()

    def set_admin_level(self, admin_level: int):
        self.__user_data.admin_level = admin_level
        self.__update_data()

    def add_token(self, life_time) -> str:
        pass  # TODO: generate token and return it

    def check_token(self, token: str) -> bool:
        pass  # TODO: check if token is valid and return bool

    def get_info(self) -> Dict[str, Union[str, int]]:
        return {'first_name': self.__user_data.first_name, 'second_name': self.__user_data.second_name,
                'mention': self.__user_data.mention, 'id': self.__user_data._id,
                'admin_level': self.__user_data.admin_level}

    def is_authorized(self) -> bool:
        return self.__is_authorized

    def authorize(self):
        self.__is_authorized = True

    def get_ban(self) -> Dict[str, int]:
        return {'ban_timestamp': self.__user_data.ban_timestamp, 'ban_length': self.__user_data.ban_length}


class ForbiddenError(BaseException):
    def __init__(self, arg='Insufficient permission level'):
        self.message = arg

    def __str__(self):
        return self.message


class BannedError(BaseException):
    def __init__(self, user: Dict[str, Union[str, int]] = None):
        self.message = 'This user is banned to do this action'
        if user is not None:
            # cause I'll tell it once more - THIS IS NOT A PROTECTED MEMBER!!11!!!1!1
            # noinspection PyProtectedMember
            self.message = f'User {user["first_name"] or ""} {user["second_name"] or ""} with id {user["id"]}'\
                           ' is banned to do this action'

    def __str__(self):
        return self.message


def timestamp():
    return int(datetime.utcnow().timestamp())


def check_admin_level(admin_level: int):
    def level_checker(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                user: TelegramUser = kwargs['user']
            except KeyError:
                user: TelegramUser = tuple(filter(lambda x: isinstance(x, TelegramUser), args))[0]
            if user.get_info()['admin_level'] < admin_level:
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
        user_ban_info = user.get_ban()
        if timestamp() < user_ban_info['ban_length'] + user_ban_info['ban_timestamp']:
            raise BannedError(user.get_info())
        else:
            return func(*args, **kwargs)
    return wrapper
