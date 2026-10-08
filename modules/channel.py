from __future__ import annotations
from typing import TYPE_CHECKING, Any
from core.module import Module
from core.irc_line import IrcLine, IrcSenderUser
from core.config import Config

if TYPE_CHECKING:
    from core.irc_bot import IrcBot


class ModuleConfig(Config):
    channels: list[str] = []


class ModuleMain(Module):
    config: ModuleConfig

    def __init__(self, name: str, bot: IrcBot) -> None:
        super().__init__(name, bot)
        self.register_irc_line_handler("001", self.handle_connect)
        self.config = self.read_config(ModuleConfig)

        self.register_irc_command_handler(
            "join",
            self.handle_join,
            "<channel>",
            "Joins a specified channel",
            admin_only=True,
            min_args=1,
        )

        self.register_irc_command_handler(
            "part",
            self.handle_part,
            "(<channel>)",
            "Leave the specified or current channel",
            admin_only=True,
        )

    async def handle_connect(self, line: IrcLine) -> None:
        for channel in self.config.channels:
            self.bot.send_line(f"JOIN {channel}")

    async def handle_join(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        target_channel = args[0]
        self.bot.send_line(f"JOIN {target_channel}")

        if target_channel not in self.config.channels:
            self.config.channels.append(target_channel)

        self.write_config(self.config)

    async def handle_part(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        target_channel = channel if len(args) == 0 else args[0]
        self.bot.send_line(f"PART {target_channel}")

        if target_channel in self.config.channels:
            self.config.channels.remove(target_channel)

        self.write_config(self.config)
