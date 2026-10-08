from __future__ import annotations
from typing import TYPE_CHECKING, Any
from core.module import Module
from core.irc_line import IrcLine, IrcSenderUser
from core.config import Config, dump_config
from random import choice
from re import match as re_match
from requests import post as requests_post

if TYPE_CHECKING:
    from core.irc_bot import IrcBot


class ModuleConfig(Config):
    ignored: list[str] = []
    messages: list[str] = []


class ModuleMain(Module):
    config: ModuleConfig
    message_set: set[str]

    def __init__(self, name: str, bot: IrcBot) -> None:
        super().__init__(name, bot)
        self.register_irc_line_handler("PRIVMSG", self.handle_privmsg)
        self.config = self.read_config(ModuleConfig)

        self.message_set = set(self.config.messages)

        self.register_irc_command_handler(
            "talkbot_ignore",
            self.handle_talkbot_ignore,
            "<pattern>",
            "Don't trigger talkbot for a given user regex",
            admin_only=True,
            min_args=1,
        )

        self.register_irc_command_handler(
            "talkbot_unignore",
            self.handle_talkbot_unignore,
            "<pattern>",
            "Don't trigger talkbot for a given user regex",
            admin_only=True,
            min_args=1,
        )

        self.register_irc_command_handler(
            "talkbot_dump",
            self.handle_talkbot_dump,
            "-",
            "Upload talkbot db to x0.at",
        )

    async def handle_privmsg(self, line: IrcLine) -> None:
        if not isinstance(line.sender, IrcSenderUser):
            return

        sender_repr = line.sender.original()

        for ignore in self.config.ignored:
            if re_match(ignore, sender_repr):
                return

        channel = line.args[0]
        message = line.args[1]
        pattern = f"{self.bot.nick}:"
        pattern_start = message.find(pattern)

        if pattern_start == -1:
            return

        message = message[pattern_start + len(pattern) :].strip()

        # XXX hack
        if channel == self.bot.nick:
            channel = line.sender.nick

        if len(self.config.messages) > 0:
            response = choice(self.config.messages)
            self.bot.send_message(channel, response)

        if message not in self.message_set:
            self.message_set.add(message)
            self.config.messages.append(message)
            self.write_config(self.config)

    async def handle_talkbot_ignore(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        pattern = args[0]

        if pattern in self.config.ignored:
            self.bot.send_message(channel, "Pattern already exists.")
            return

        self.config.ignored.append(pattern)
        self.write_config(self.config)
        self.bot.send_message(channel, "Pattern added.")

    async def handle_talkbot_unignore(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        pattern = args[0]

        if pattern not in self.config.ignored:
            self.bot.send_message(channel, "Pattern doesn't exist.")
            return

        self.config.ignored.remove(pattern)
        self.write_config(self.config)
        self.bot.send_message(channel, "Pattern deleted.")

    async def handle_talkbot_dump(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        json = dump_config(self.config)

        try:
            resp = requests_post(
                "https://x0.at",
                files={
                    "file": (
                        "talkbot.json",
                        json.encode("u8", "ignore"),
                        "application/json",
                    )
                },
            )
            resp.raise_for_status()
            url = resp.text.strip()
            self.bot.send_message(channel, f"Uploaded to: {url}")
        except Exception as err:
            self.bot.send_message(channel, f"Failed to upload: {err}")
