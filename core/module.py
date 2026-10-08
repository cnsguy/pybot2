from __future__ import annotations
from core.irc_line import IrcLine, IrcSenderUser
from core.config import ConfT, read_config, write_config
from typing import TYPE_CHECKING, Callable, Awaitable, Optional, Any, TypeVar
from os.path import join as path_join
from pydantic import BaseModel

if TYPE_CHECKING:
    from core.irc_bot import IrcBot

IrcLineHandler = Callable[[IrcLine], Awaitable[None]]
IrcCommandHandler = Callable[
    [dict[str, str], IrcSenderUser, str, list[str]], Awaitable[None]
]


class ModuleCommand:
    name: str
    handler: IrcCommandHandler
    usage: Optional[str]
    description: str
    admin_only: bool
    min_args: int

    def __init__(
        self,
        name: str,
        handler: IrcCommandHandler,
        usage: Optional[str],
        description: str,
        admin_only: bool,
        min_args: int,
    ) -> None:
        self.name = name
        self.handler = handler
        self.usage = usage
        self.description = description
        self.admin_only = admin_only
        self.min_args = min_args

    def help(self):
        if self.usage is not None:
            return f"{self.name} {self.usage}: {self.description}"
        else:
            return f"{self.name}: {self.description}"


class Module:
    name: str
    bot: IrcBot
    line_handlers: dict[str, IrcLineHandler]
    commands: dict[str, ModuleCommand]

    def __init__(self, name: str, bot: IrcBot) -> None:
        self.name = name
        self.bot = bot
        self.line_handlers = {}
        self.commands = {}

    def unload(self) -> None:
        pass

    def register_irc_line_handler(self, cmd: str, handler: IrcLineHandler) -> None:
        self.line_handlers[cmd] = handler

    def config_file_path(self) -> str:
        file_name = f"{self.name}.json"
        file_path = path_join("data", self.bot.data_directory, "modules", file_name)
        return file_path

    def read_config(self, config_class: type[ConfT]) -> ConfT:
        file_path = self.config_file_path()
        return read_config(file_path, config_class)

    def write_config(self, config: ConfT) -> None:
        file_path = self.config_file_path()
        write_config(file_path, config)

    def register_irc_command_handler(
        self,
        command_name: str,
        handler: IrcCommandHandler,
        usage: Optional[str],
        description: str,
        admin_only: bool = False,
        min_args: int = 0,
    ) -> None:
        self.commands[command_name] = ModuleCommand(
            command_name, handler, usage, description, admin_only, min_args
        )

    async def handle_irc_line(self, irc_line: IrcLine) -> None:
        handler = self.line_handlers.get(irc_line.cmd, None)

        if handler is None:
            return

        await handler(irc_line)

    async def handle_irc_command(
        self,
        tags: dict[str, str],
        sender: IrcSenderUser,
        command_name: str,
        channel: str,
        args: list[str],
    ) -> None:
        command = self.commands.get(command_name, None)

        if command is None:
            return

        if command.admin_only and not self.bot.check_admin(sender, tags):
            self.bot.send_message(channel, "Unauthorized")
            return

        if len(args) < command.min_args:
            self.bot.send_message(channel, command.help())
            return

        await command.handler(tags, sender, channel, args)
