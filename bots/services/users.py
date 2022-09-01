from typing import List

from bots.repositories import TGUserRepository, VKUserRepository
from bots.schemes import TGUser, VKUser
from bots.utils.strings import strings


class TGUserService:
    def __init__(self, tg_user_repository: TGUserRepository):
        self._repository = tg_user_repository

    async def get_all_users(self) -> List[TGUser]:
        return await self._repository.all()

    async def get_user_or_create(self, chat_id: int) -> TGUser:
        user = await self._repository.get_or_none(chat_id=chat_id)
        if user is None:
            user = await self._repository.create(
                TGUser(
                    chat_id=chat_id
                )
            )
        return user

    async def switch_notify(self, user: TGUser) -> None:
        user.notify = not user.notify
        await self._repository.update(user)

    async def set_study_group(self, user: TGUser, group: str) -> str:
        if user.group == group:
            return strings.error.group_not_changed.format(group)
        user.group = group
        await self._repository.update(user)
        return strings.info.group_set.format(group)


class VKUserServices:
    def __init__(self, vk_user_repository: VKUserRepository):
        self._repository = vk_user_repository

    async def get_all_users(self) -> List[VKUser]:
        return await self._repository.all()

    async def get_user_or_create(self, chat_id: int, **kwargs) -> VKUser:
        user = await self._repository.get_or_none(chat_id=chat_id)
        if user is None:
            user = await self._repository.create(
                VKUser(
                    chat_id=chat_id,
                    **kwargs
                )
            )
        return user

    async def switch_notify(self, user: VKUser) -> None:
        user.notify = not user.notify
        await self._repository.update(user)

    async def set_study_group(self, user: VKUser, group: str) -> str:
        if user.group == group:
            return strings.error.group_not_changed.format(group)
        user.group = group
        await self._repository.update(user)
        return strings.info.group_set.format(group)
