from __future__ import annotations
from core.irc_client import IrcClient
from core.irc_line import IrcLine, IrcSenderUser
from core.module import Module
from typing import Optional, cast
from sys import modules as sys_modules, stderr
from traceback import format_exception


class IrcBot(IrcClient):
    module_names: list[str]
    admin_accounts: list[str]
    admin_hosts: list[str]
    command_prefix: str
    data_directory: str
    debug_channel: Optional[str]
    modules: dict[str, Module]

    def __init__(
        self,
        nick: str,
        ident: str,
        real_name: str,
        host: str,
        port: int,
        use_ssl: bool,
        sasl_user: Optional[str],
        sasl_password: Optional[str],
        module_names: list[str],
        admin_accounts: list[str],
        admin_hosts: list[str],
        command_prefix: str,
        data_directory: str,
        debug_channel: Optional[str],
    ) -> None:
        super().__init__(
            nick,
            ident,
            real_name,
            host,
            port,
            use_ssl,
            sasl_user,
            sasl_password,
        )
        self.module_names = module_names
        self.admin_accounts = admin_accounts
        self.admin_hosts = admin_hosts
        self.command_prefix = command_prefix
        self.data_directory = data_directory
        self.debug_channel = debug_channel
        self.modules = {}
        self.load_modules()

    def is_admin(self, account: str) -> bool:
        return account in self.admin_accounts

    def check_admin(self, sender: IrcSenderUser, tags: dict[str, str | None]) -> bool:
        account = tags.get("account", None)

        if account in self.admin_accounts:
            return True

        if sender.host in self.admin_hosts:
            return True

        return False

    def load_module(self, module_name: str) -> None:
        if module_name in self.modules:
            return

        module = __import__(f"modules.{module_name}")
        module = getattr(module, module_name)
        module_main = getattr(module, "ModuleMain")
        self.modules[module_name] = module_main(module_name, self)

    def remove_module(self, module_name: str) -> None:
        module = self.modules.get(module_name, None)

        if module is None:
            return

        module.unload()
        del sys_modules[f"modules.{module_name}"]
        del self.modules[module_name]

    def load_modules(self) -> None:
        for module_name in self.module_names:
            self.load_module(module_name)

    @staticmethod
    def format_traceback(err: BaseException) -> str:
        return "".join(format_exception(err)).strip()

    @staticmethod
    def tail_lines(text: str, count: int) -> str:
        return "\n".join(text.splitlines()[-count:])

    def report_error(self, context: str, err: BaseException) -> None:
        trace = self.format_traceback(err)
        print(f"[ERROR] {context}\n{trace}", file=stderr)

        if self.debug_channel is not None and self.is_connected():
            self.send_message(
                self.debug_channel,
                f"[ERROR] {context}: {self.tail_lines(trace, 10)}",
            )

    async def handle_irc_command(self, line: IrcLine) -> None:
        assert line.sender is not None, "None sender in a PRIVMSG"

        if type(line.sender) != IrcSenderUser:
            return

        channel = line.args[0]

        if channel == self.nick:
            channel = line.sender.nick

        args = line.args[1].split(" ")

        if len(args) == 0:
            return

        cmd = args.pop(0)
        cmd = cmd[len(self.command_prefix) :]

        for key in list(self.modules.keys()):
            module = self.modules.get(key, None)

            # needed in case module gets removed at runtime
            if module is None:
                continue

            try:
                await module.handle_irc_command(
                    line.tags, line.sender, cmd, channel, args
                )
            except Exception as err:
                self.report_error(
                    f"module '{key}' command '{cmd}' for {line.sender.nick}", err
                )

    async def handle_irc_line(self, line: IrcLine) -> None:
        if (
            line.cmd == "PRIVMSG"
            and len(line.args) == 2
            and line.args[1].startswith(self.command_prefix)
        ):
            await self.handle_irc_command(line)

        print(line)

        for key in list(self.modules.keys()):
            module = self.modules.get(key, None)

            # needed in case module gets removed at runtime
            if module is None:
                continue

            try:
                await module.handle_irc_line(line)
            except Exception as err:
                self.report_error(f"module '{key}' on {line.cmd}", err)
