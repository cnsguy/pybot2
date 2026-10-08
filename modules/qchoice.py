from __future__ import annotations
from typing import TYPE_CHECKING
from core.module import Module
from core.config import Config
from core.irc_line import IrcSenderUser
from asyncio import to_thread
from requests import get as requests_get, RequestException
from time import monotonic

if TYPE_CHECKING:
    from core.irc_bot import IrcBot

LEGACY_API_URL = "https://qrng.anu.edu.au/API/jsonI.php"
RATE_LIMITED_MARKER = "limited to 1 requests per minute"
RATE_LIMIT = 60
POOL_SIZE = 64
TIMEOUT = 10


class RateLimitError(Exception):
    pass


def fetch_quantum_bytes(count: int) -> list[int]:
    params: dict[str, str | int] = {"length": count, "type": "uint8"}
    response = requests_get(LEGACY_API_URL, params=params, timeout=TIMEOUT)

    if RATE_LIMITED_MARKER in response.text:
        raise RateLimitError("the ANU API allows one request per minute")

    response.raise_for_status()
    payload = response.json()

    if not payload.get("success", False):
        raise ValueError("QRNG API reported failure")

    data = payload.get("data", None)

    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("QRNG API returned no data")

    return [int(value) for value in data]


class ModuleMain(Module):
    pool: list[int]
    last_fetch: float

    def __init__(self, name: str, bot: IrcBot) -> None:
        super().__init__(name, bot)
        self.pool = []
        self.last_fetch = 0.0

        self.register_irc_command_handler(
            "qchoice",
            self.handle_qchoice,
            "<option>, <option>, ...",
            "Split the universe",
            min_args=1,
        )

    def rate_limit_remaining(self) -> int:
        elapsed = monotonic() - self.last_fetch
        return max(0, int(RATE_LIMIT - elapsed) + 1)

    async def draw_index(self, count: int) -> int:
        limit = 256 - (256 % count)

        while True:
            while self.pool:
                value = self.pool.pop()

                if value < limit:
                    return value % count

            wait = self.rate_limit_remaining()

            if wait > 0:
                raise RateLimitError(f"retry in {wait}s")

            self.pool = await to_thread(fetch_quantum_bytes, POOL_SIZE)
            self.last_fetch = monotonic()

    async def handle_qchoice(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        options = [option.strip() for option in " ".join(args).split(",")]
        options = [option for option in options if option]

        if len(options) < 2:
            self.bot.send_message(channel, "Usage: qchoice <option>, <option>, ...")
            return

        try:
            index = await self.draw_index(len(options))
        except (RateLimitError, RequestException, ValueError) as err:
            self.bot.send_message(channel, f"Failed to divide timelines: {err}")
            return

        self.bot.send_message(channel, f"In this timeline: {options[index]}")
