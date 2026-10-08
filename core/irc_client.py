from __future__ import annotations
from core.irc_line import IrcLine, IrcSenderUser, parse_line
from typing import Optional, Self
from ssl import create_default_context as ssl_create_default_context
from sys import stderr
from base64 import b64encode
from asyncio import (
    StreamReader,
    StreamWriter,
    open_connection,
    gather as asyncio_gather,
    sleep as asyncio_sleep,
    wait_for,
)
from textwrap import wrap as textwrap_wrap


class Connection:
    reader: StreamReader
    writer: StreamWriter

    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        self.reader = reader
        self.writer = writer

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.writer.close()


class IrcClient:
    nick: str
    ident: str
    real_name: str
    buf: bytearray
    connection: Optional[Connection]
    sasl_user: Optional[str]
    sasl_password: Optional[str]
    message_queue: list[tuple[str, str]]

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
    ) -> None:
        self.nick = nick
        self.ident = ident
        self.real_name = real_name
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.sasl_user = sasl_user
        self.sasl_password = sasl_password
        self.buf = bytearray()
        self.connection = None
        self.message_queue = []

    async def connect(self) -> Connection:
        if self.use_ssl:
            ssl_ctx = ssl_create_default_context()
        else:
            ssl_ctx = None

        reader, writer = await wait_for(
            open_connection(self.host, self.port, ssl=ssl_ctx), timeout=5
        )

        return Connection(reader, writer)

    async def read_line(self) -> IrcLine:
        assert self.connection is not None

        while True:
            nl_pos = self.buf.find(b"\r\n")

            if nl_pos != -1:
                line = self.buf[:nl_pos].decode("u8", "ignore")
                self.buf = self.buf[nl_pos + 2 :]
                return parse_line(line)

            pkt = await self.connection.reader.read(512)

            if len(pkt) == 0:
                raise ConnectionResetError()

            self.buf += pkt

    def send_line(self, line: str) -> None:
        assert self.connection is not None
        self.connection.writer.write(line.encode("u8", "ignore") + b"\r\n")

    def send_message(self, channel: str, message: str) -> None:
        for part in textwrap_wrap(message, width=300):
            self.message_queue.append((channel, part))

    # Only used in IrcBot
    async def handle_irc_line(self, line: IrcLine) -> None:
        pass

    async def run_message_queue(self) -> None:
        while True:
            if len(self.message_queue) > 0:
                channel, message = self.message_queue.pop(0)
                self.send_line(f"PRIVMSG {channel} :{message}")

            await asyncio_sleep(1)

    async def run_recv(self) -> None:
        while True:
            line = await wait_for(self.read_line(), timeout=120)

            if line.cmd == "PING":
                pong_payload = " ".join(line.args)
                self.send_line(f"PONG :{pong_payload}")
            elif line.cmd == "NICK":
                if (
                    isinstance(line.sender, IrcSenderUser)
                    and line.sender.nick == self.nick
                ):
                    self.nick = line.args[0]

            await self.handle_irc_line(line)

    async def run_ping(self) -> None:
        while True:
            self.send_line("PING :pybot")
            await asyncio_sleep(60)

    def is_connected(self) -> bool:
        return self.connection is not None

    async def run(self) -> None:
        while True:
            try:
                with await self.connect() as connection:
                    self.connection = connection
                    self.send_line(f"CAP REQ :account-tag")
                    self.send_line(f"CAP REQ :sasl")
                    self.send_line(f"CAP END")

                    sasl_user = self.sasl_user
                    sasl_password = self.sasl_password

                    if sasl_user is not None or sasl_password is not None:
                        assert (
                            sasl_user is not None
                        ), "Both sasl_user and sasl_user must be set"

                        assert (
                            sasl_password is not None
                        ), "Both sasl_user and sasl_password must be set"

                        auth = (
                            f"{self.sasl_user}\0{self.sasl_user}\0{self.sasl_password}"
                        )
                        encoded = b64encode(auth.encode()).decode()
                        self.send_line(f"AUTHENTICATE PLAIN")
                        self.send_line(f"AUTHENTICATE {encoded}")

                    self.send_line(f"USER {self.ident} 0 * :{self.real_name}")
                    self.send_line(f"NICK {self.nick}")
                    await asyncio_gather(
                        self.run_recv(), self.run_ping(), self.run_message_queue()
                    )
            except ConnectionResetError:
                print("[ERROR] Connection reset by peer", file=stderr)
            except TimeoutError:
                print("[ERROR] Connection timed out", file=stderr)

            await asyncio_sleep(10)
