from __future__ import annotations
from typing import TYPE_CHECKING, Any
from core.module import Module
from core.irc_line import IrcLine, IrcSenderUser
from core.config import Config
from random import choice
from re import match as re_match, sub as re_sub

if TYPE_CHECKING:
    from core.irc_bot import IrcBot


class ModuleConfigEntry:
    sender_pattern: str
    word_pattern: str
    response: str

    def __init__(self, sender_pattern: str, word_pattern: str, response: str) -> None:
        self.sender_pattern = sender_pattern
        self.word_pattern = word_pattern
        self.response = response


class ModuleConfig(Config):
    patterns: list[ModuleConfigEntry]

    def __init__(self, values: dict[Any, Any]) -> None:
        patterns = values.get("patterns", [])
        parsed_patterns: list[ModuleConfigEntry] = []
        assert type(patterns) == list, "patterns should be a list of dict"

        for val in patterns:
            assert type(val) == dict, "patterns should be a list of dict"

            sender_pattern = val.get("sender_pattern", None)
            assert (
                type(sender_pattern) == str
            ), "patterns entry should have a sender_pattern str"

            word_pattern = val.get("word_pattern", None)
            assert (
                type(word_pattern) == str
            ), "patterns entry should have a word_pattern str"

            response = val.get("response", None)
            assert type(response) == str, "patterns entry should have a response str"

            parsed_patterns.append(
                ModuleConfigEntry(sender_pattern, word_pattern, response)
            )

        self.patterns = parsed_patterns


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
            if re_match(entry.sender_pattern, sender_repr):
                if re_match(entry.word_pattern, message):
                    response = re_sub(entry.word_pattern, entry.response, message)
                    self.bot.send_message(channel, response)

    async def handle_word_trigger_add(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
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
            ModuleConfigEntry(sender_pattern, word_pattern, response)
        )
        self.write_config(self.config)
        self.bot.send_message(channel, "Pattern added.")

    async def handle_word_trigger_del(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
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
