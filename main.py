from __future__ import annotations
from core.irc_bot import IrcBot
from core.config import Config, read_config
from asyncio import run as asyncio_run
from typing import Any
from traceback import print_exception
from sys import argv, stderr


class BotConfig(Config):
    nick: str
    ident: str
    real_name: str
    modules: list[str]
    admin_accounts: list[str]
    admin_hosts: list[str]
    host: str
    port: int
    use_ssl: bool
    command_prefix: str
    data_directory: str

    def __init__(self, values: dict[Any, Any]) -> None:
        nick = values.get("nick", "pybot")
        assert type(nick) == str, "nick should be a str"

        ident = values.get("ident", "bot")
        assert type(ident) == str, "ident should be a str"

        real_name = values.get("real_name", "Python IRC Bot")
        assert type(real_name) == str, "real_name should be a str"

        data_directory = values.get("data_directory", "Libera")
        assert type(data_directory) == str, "data_directory should be a str"

        host = values.get("host", "irc.libera.chat")
        assert type(host) == str, "host should be a str"

        port = values.get("port", 6697)
        assert type(port) == int, "port should be a int"

        use_ssl = values.get("use_ssl", True)
        assert type(use_ssl) == bool, "use_ssl should be a bool"

        sasl_user = values.get("sasl_user", None)
        assert (
            type(sasl_user) == str or sasl_user is None
        ), "sasl_user should be a string or unset"

        sasl_password = values.get("sasl_password", None)
        assert (
            type(sasl_password) == str or sasl_password is None
        ), "sasl_password should be a string or unset"

        command_prefix = values.get("command_prefix", ".")
        assert type(command_prefix) == str, "command_prefix should be a str"

        admin_hosts = values.get("admin_hosts", [])
        assert type(admin_hosts) == list, "admin_hosts should be a list of str"

        for val in admin_hosts:
            assert type(val) == str, "admin_hosts should be a list of str"

        admin_accounts = values.get("admin_accounts", [])
        assert type(admin_accounts) == list, "admin_accounts should be a list of str"

        for val in admin_accounts:
            assert type(val) == str, "admin_accounts should be a list of str"

        modules = values.get("modules", ["channel", "help"])
        assert type(modules) == list, "modules should be a list of str"

        for val in modules:
            assert type(val) == str, "modules should be a list of str"

        self.nick = nick
        self.ident = ident
        self.real_name = real_name
        self.data_directory = data_directory
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.sasl_user = sasl_user
        self.sasl_password = sasl_password
        self.command_prefix = command_prefix
        self.admin_hosts = admin_hosts
        self.admin_accounts = admin_accounts
        self.modules = modules


async def main() -> None:
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <config>", file=stderr)
        return

    config = read_config(argv[1], BotConfig)

    bot = IrcBot(
        config.nick,
        config.ident,
        config.real_name,
        config.host,
        config.port,
        config.use_ssl,
        config.sasl_user,
        config.sasl_password,
        config.modules,
        config.admin_accounts,
        config.admin_hosts,
        config.command_prefix,
        config.data_directory,
    )
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio_run(main())
    except KeyboardInterrupt:
        pass
