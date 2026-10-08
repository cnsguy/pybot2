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
            "help",
            self.handle_help,
            "(<command>)",
            "Get help",
        )

    async def handle_help(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        command_name = args[0] if len(args) > 0 else None

        if command_name is None:
            help = []

            for module_name, module in self.bot.modules.items():
                if len(module.commands) > 0:
                    commands = ", ".join(module.commands.keys())
                else:
                    commands = "-"

                help.append(f"[{module_name}] {commands}")

            help_message = " ".join(help)
            self.bot.send_message(channel, help_message)
            return
        else:
            for module_name, module in self.bot.modules.items():
                if command_name in module.commands:
                    command = module.commands[command_name]
                    self.bot.send_message(channel, command.help())
