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
            "nick",
            self.handle_nick,
            "<message>",
            "Change bot nick",
            admin_only=True,
            min_args=1,
        )

    async def handle_nick(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        nick = args[0]
        self.bot.send_line(f"NICK {nick}")
