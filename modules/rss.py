from __future__ import annotations
from typing import TYPE_CHECKING, Any
from core.module import Module
from core.irc_line import IrcLine, IrcSenderUser
from core.config import Config
from asyncio import Task, create_task, sleep as asyncio_sleep, CancelledError
from feedparser import parse as feedparser_parse
from re import sub as re_sub

if TYPE_CHECKING:
    from core.irc_bot import IrcBot


class ModuleConfigEntry:
    channel: str
    link: str

    def __init__(self, channel: str, link: str) -> None:
        self.channel = channel
        self.link = link


class ModuleConfig(Config):
    entries: list[ModuleConfigEntry]
    sent: dict[str, set[str]]

    def __init__(self, values: dict[Any, Any]) -> None:
        entries = values.get("entries", [])
        parsed_entries: list[ModuleConfigEntry] = []
        assert type(entries) == list, "entries should be a list of dict"

        for val in entries:
            assert type(val) == dict, "entries should be a list of dict"

            channel = val.get("channel", None)
            assert type(channel) == str, "entries entry should have a channel str"

            link = val.get("link", None)
            assert type(link) == str, "entries entry should have a link str"

            parsed_entries.append(ModuleConfigEntry(channel, link))

        sent = values.get("sent", dict())
        assert type(sent) == dict, "sent should be a dict of str to list of str"

        for key, val in sent.items():
            assert type(key) == str, "sent should be a dict of str to list of str"
            assert type(val) == list, "sent should be a dict of str to list of str"

            for sub_val in val:
                assert (
                    type(sub_val) == str
                ), "sent should be a dict of str to list of str"

            sent[key] = set(val)

        self.entries = parsed_entries
        self.sent = sent


class ModuleMain(Module):
    config: ModuleConfig
    task: Task

    def __init__(self, name: str, bot: IrcBot) -> None:
        super().__init__(name, bot)
        self.config = self.read_config(ModuleConfig)
        self.task = create_task(self.main_loop())

        self.register_irc_command_handler(
            "rss_add",
            self.handle_rss_add,
            "<channel> <link>",
            "Add an RSS entry",
            admin_only=True,
            min_args=2,
        )

        self.register_irc_command_handler(
            "rss_del",
            self.handle_rss_del,
            "<channel> <link>",
            "Delete an RSS entry",
            admin_only=True,
            min_args=2,
        )

        self.register_irc_command_handler(
            "rss_list",
            self.handle_rss_list,
            "",
            "List RSS entries",
        )

        self.write_config(self.config)

    def unload(self) -> None:
        self.task.cancel()

    async def main_loop(self) -> None:
        try:
            while True:
                await asyncio_sleep(60)

                if not self.bot.is_connected():
                    continue

                for entry in self.config.entries:
                    # TODO track sent messages per channel
                    try:
                        parsed = feedparser_parse(entry.link)
                    except Exception as err:
                        self.bot.send_message(
                            entry.channel,
                            f"[ERROR] Failed to parse feed for {entry.link}: {err}",
                        )
                        continue

                    if entry.channel not in self.config.sent:
                        self.config.sent[entry.channel] = set()
                        self.write_config(self.config)

                    for rss_entry in parsed.entries:
                        link = rss_entry.link
                        description = rss_entry.description

                        if link in self.config.sent[entry.channel]:
                            continue

                        self.config.sent[entry.channel].add(link)
                        self.write_config(self.config)

                        description = re_sub(r"</?[A-z]+ ?/?>", "", description)
                        description = description.replace(" : ", ": ")

                        for part in description.split("\n"):
                            part = re_sub(r"\s+", " ", part)
                            part = part.strip()

                            if len(part) == 0:
                                continue

                            self.bot.send_message(entry.channel, part)
                            await asyncio_sleep(1)

                        self.bot.send_message(entry.channel, link)
                        await asyncio_sleep(1)
                        self.bot.send_message(entry.channel, " ")
                        await asyncio_sleep(1)

        except CancelledError:
            pass

    async def handle_rss_add(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        channel = args[0]
        link = args[1]

        for entry in self.config.entries:
            if entry.channel == channel and entry.link == link:
                self.bot.send_message(channel, "Entry already exists.")
                return

        self.config.entries.append(ModuleConfigEntry(channel, link))
        self.write_config(self.config)
        self.bot.send_message(channel, "Entry added.")

    async def handle_rss_del(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        channel = args[0]
        link = args[1]

        for i, entry in enumerate(self.config.entries):
            if entry.channel == channel and entry.link == link:
                self.bot.send_message(channel, "Entry deleted.")
                del self.config.entries[i]
                self.write_config(self.config)
                return

        self.bot.send_message(channel, "No such entry exists.")

    async def handle_rss_list(
        self, tags: dict[str, str], sender: IrcSenderUser, channel: str, args: list[str]
    ) -> None:
        for entry in self.config.entries:
            self.bot.send_message(channel, f"{entry.channel}: {entry.link}")