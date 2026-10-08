from __future__ import annotations
from typing import TYPE_CHECKING, Any
from core.module import Module
from core.irc_line import IrcLine, IrcSenderUser
from core.config import Config
from random import choice
from re import match as re_match, sub as re_sub, finditer as re_finditer

if TYPE_CHECKING:
    from core.irc_bot import IrcBot


class ModuleConfigEntry(Config):
    sender_pattern: str
    word_pattern: str
    response: str


class ModuleConfig(Config):
    patterns: list[ModuleConfigEntry] = []


class ModuleMain(Module):
    config: ModuleConfig
    message_set: set[str]

    def __init__(self, name: str, bot: IrcBot) -> None:
        super().__init__(name, bot)
        self.register_irc_line_handler("PRIVMSG", self.handle_privmsg)
        self.config = self.read_config(ModuleConfig)

        self.register_irc_command_handler(
            "word_trigger_add",
            self.handle_word_trigger_add,
            "<sender pattern> <message pattern> <response>",
            "Add a word trigger pattern",
            admin_only=True,
            min_args=3,
        )

        self.register_irc_command_handler(
            "word_trigger_del",
            self.handle_word_trigger_del,
            "<sender pattern> <message pattern> <response>",
            "Delete a word trigger pattern",
            admin_only=True,
            min_args=3,
        )

        self.register_irc_command_handler(
            "word_trigger_list",
            self.handle_word_trigger_list,
            None,
            "List word trigger patterns",
        )

    async def handle_privmsg(self, line: IrcLine) -> None:
        if not isinstance(line.sender, IrcSenderUser):
            return

        sender_repr = line.sender.original()
        channel = line.args[0]
        message = line.args[1]

        # XXX hack
        if channel == self.bot.nick:
            channel = line.sender.nick

        for entry in self.config.patterns:
            try:
                if re_match(entry.sender_pattern, sender_repr):
                    for matching in re_finditer(entry.word_pattern, message):
                        response = re_sub(
                            entry.word_pattern, entry.response, matching.group(0)
                        )
                        self.bot.send_message(channel, response)

            except Exception as err:
                self.bot.send_message(
                    channel, f"Error running word trigger '{entry}': {err}"
                )

    async def handle_word_trigger_add(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        sender_pattern = args[0]
        word_pattern = args[1]
        response = " ".join(args[2:])

        for entry in self.config.patterns:
            if (
                entry.sender_pattern == sender_pattern
                and entry.word_pattern == word_pattern
                and entry.response == response
            ):
                self.bot.send_message(channel, "Pattern already exists.")
                return

        self.config.patterns.append(
            ModuleConfigEntry(
                sender_pattern=sender_pattern,
                word_pattern=word_pattern,
                response=response,
            )
        )
        self.write_config(self.config)
        self.bot.send_message(channel, "Pattern added.")

    async def handle_word_trigger_del(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        sender_pattern = args[0]
        word_pattern = args[1]
        response = " ".join(args[2:])

        for i, entry in enumerate(self.config.patterns):
            if (
                entry.sender_pattern == sender_pattern
                and entry.word_pattern == word_pattern
                and entry.response == response
            ):
                self.bot.send_message(channel, "Pattern deleted.")
                del self.config.patterns[i]
                self.write_config(self.config)
                return

        self.bot.send_message(channel, "No such pattern exists.")

    async def handle_word_trigger_list(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        if len(self.config.patterns) == 0:
            self.bot.send_message(channel, "No word trigger entries in the database")

        for entry in self.config.patterns:
            self.bot.send_message(
                channel,
                f"sender: {entry.sender_pattern}, entry: {entry.word_pattern}, response: {entry.response}",
            )
