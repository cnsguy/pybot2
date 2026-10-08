from __future__ import annotations
from typing import TYPE_CHECKING, Any
from core.module import Module
from core.irc_line import IrcLine, IrcSenderUser
from random import choice
from re import match as re_match, sub as re_sub

if TYPE_CHECKING:
    from core.irc_bot import IrcBot


class ModuleMain(Module):
    def __init__(self, name: str, bot: IrcBot) -> None:
        super().__init__(name, bot)

        self.register_irc_command_handler(
            "mod_load",
            self.handle_mod_load,
            "<module>",
            "Load a module",
            admin_only=True,
            min_args=1,
        )

        self.register_irc_command_handler(
            "mod_remove",
            self.handle_mod_remove,
            "<module>",
            "Remove a module",
            admin_only=True,
            min_args=1,
        )

        self.register_irc_command_handler(
            "mod_reload",
            self.handle_mod_reload,
            "<module>",
            "Reload a module",
            admin_only=True,
            min_args=1,
        )

    async def handle_mod_load(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        module_name = args[0]

        if module_name in self.bot.modules:
            self.bot.send_message(channel, "Module is already loaded.")
            return

        try:
            self.bot.load_module(module_name)
            self.bot.send_message(channel, "Module loaded.")
        except ModuleNotFoundError:
            self.bot.send_message(channel, "No such module exists")

    async def handle_mod_remove(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        module_name = args[0]

        if module_name not in self.bot.modules:
            self.bot.send_message(channel, "Module is not loaded.")
            return

        self.bot.remove_module(module_name)
        self.bot.send_message(channel, "Module removed.")

    async def handle_mod_reload(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        await self.handle_mod_remove(tags, sender, channel, args)
        await self.handle_mod_load(tags, sender, channel, args)
