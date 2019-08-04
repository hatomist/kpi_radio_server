from dataclasses import dataclass, field
from typing import Dict, Union
import pymongo
nullable_str = Union[str, None]


class AdminLevel:
    NOT_ADMIN = 0
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
    admin_level: AdminLevel = AdminLevel.NOT_ADMIN
    tokens: Dict[str, int] = field(default_factory=dict)


class TelegramAuth:
    def __init__(self, mongodb_url: str):
        self.__mongodb_client = pymongo.MongoClient(mongodb_url)
        self.__mongodb = self.__mongodb_client['radio']
        self.__users = self.__mongodb['users']

    def get_user(self, user_id: int):
        got_user = self.__users.find_one({'_id': user_id})
        if got_user is None:
            return TelegramUser(user_id)
        else:
            return TelegramUser(**got_user)

    def update_user(self, user: TelegramUser):
        # because it is NOT A PROTECTED MEMBER!!1!!1!! just uid.
        # noinspection PyProtectedMember
        self.__users.replace_one(filter={'_id': user._id}, replacement=user.__dict__, upsert=True)
