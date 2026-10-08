from __future__ import annotations
from typing import TYPE_CHECKING, Any
from core.module import Module
from core.irc_line import IrcLine, IrcSenderUser
from core.config import Config
from random import choice
from re import match as re_match, sub as re_sub

if TYPE_CHECKING:
    from core.irc_bot import IrcBot


class ModuleConfigEntry:
    channel: str
    message: str

    def __init__(self, channel: str, message: str) -> None:
        self.channel = channel
        self.message = message


class ModuleConfig(Config):
    patterns: list[ModuleConfigEntry]

    def __init__(self, values: dict[Any, Any]) -> None:
        patterns = values.get("patterns", [])
        parsed_patterns: list[ModuleConfigEntry] = []
        assert type(patterns) == list, "patterns should be a list of dict"

        for val in patterns:
            assert type(val) == dict, "patterns should be a list of dict"

            channel = val.get("channel", None)
            assert type(channel) == str, "patterns entry should have a channel str"

            message = val.get("message", None)
            assert type(message) == str, "patterns entry should have a message str"

            parsed_patterns.append(ModuleConfigEntry(channel, message))

        self.patterns = parsed_patterns


class ModuleMain(Module):
    config: ModuleConfig
    message_set: set[str]

    def __init__(self, name: str, bot: IrcBot) -> None:
        super().__init__(name, bot)
        self.register_irc_line_handler("JOIN", self.handle_join)
        self.config = self.read_config(ModuleConfig)

        self.register_irc_command_handler(
            "advert_add",
            self.handle_advert_add,
            "<channel> <message>",
            "Add an advertisement pattern",
            admin_only=True,
            min_args=3,
        )

        self.register_irc_command_handler(
            "advert_del",
            self.handle_advert_del,
            "<channel> <message>",
            "Delete an advertisement pattern",
            admin_only=True,
            min_args=3,
        )

        self.register_irc_command_handler(
            "advert_list",
            self.handle_advert_list,
            None,
            "List advertisement patterns",
        )

    async def handle_join(self, line: IrcLine) -> None:
        if not isinstance(line.sender, IrcSenderUser):
            return

        channel = line.args[0]

        for entry in self.config.patterns:
            if entry.channel == channel:
                nick = line.sender.nick
                await self.bot.send_message(nick, entry.message)

    async def handle_advert_add(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        channel = args[0]
        message = " ".join(args[1:])

        for entry in self.config.patterns:
            if entry.channel == channel and entry.message == message:
                await self.bot.send_message(channel, "Pattern already exists.")
                return

        self.config.patterns.append(ModuleConfigEntry(channel, message))
        self.write_config(self.config)
        await self.bot.send_message(channel, "Pattern added.")

    async def handle_advert_del(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        channel = args[0]
        message = " ".join(args[1:])

        for i, entry in enumerate(self.config.patterns):
            if entry.channel == channel and entry.message == message:
                await self.bot.send_message(channel, "Pattern deleted.")
                del self.config.patterns[i]
                self.write_config(self.config)
                return

        await self.bot.send_message(channel, "No such pattern exists.")

    async def handle_advert_list(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        if len(self.config.patterns) == 0:
            await self.bot.send_message(
                channel, "No word trigger entries in the database"
            )

        for entry in self.config.patterns:
            await self.bot.send_message(
                channel,
                f"channel: {entry.channel}, entry: {entry.message}",
            )
