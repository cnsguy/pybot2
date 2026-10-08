from __future__ import annotations
from typing import TYPE_CHECKING
from core.module import Module
from core.irc_line import IrcLine, IrcSenderUser

if TYPE_CHECKING:
    from core.irc_bot import IrcBot


class ModuleMain(Module):
    def __init__(self, name: str, bot: IrcBot) -> None:
        super().__init__(name, bot)

        self.register_irc_command_handler(
            "say",
            self.handle_say,
            "<message>",
            "Sends a message to the current channel",
            admin_only=True,
            min_args=1,
        )

        self.register_irc_command_handler(
            "say_to",
            self.handle_say_to,
            "<channel> <message>",
            "Sends a message to the specified channel",
            admin_only=True,
            min_args=2,
        )

    async def handle_say(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        self.bot.send_message(channel, " ".join(args))

    async def handle_say_to(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        channel = args[0]
        message = " ".join(args[1:])
        self.bot.send_message(channel, message)
