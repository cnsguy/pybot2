from __future__ import annotations
from core.irc_bot import IrcBot
from core.config import Config, read_config
from asyncio import run as asyncio_run
from typing import Any, Optional
from traceback import print_exception
from sys import argv, stderr


class BotConfig(Config):
    nick: str = "pybot"
    ident: str = "bot"
    real_name: str = "Python IRC Bot"
    modules: list[str] = []
    admin_accounts: list[str] = []
    admin_hosts: list[str] = []
    host: str = "irc.libera.chat"
    port: int = 6697
    use_ssl: bool = True
    command_prefix: str = "."
    data_directory: str = "Libera"
    sasl_user: Optional[str] = None
    sasl_password: Optional[str] = None


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
