from __future__ import annotations
from typing import Optional


class IrcSender:
    pass


class IrcSenderUser(IrcSender):
    nick: str
    ident: str
    host: str

    def __init__(self, nick: str, ident: str, host: str) -> None:
        self.nick = nick
        self.ident = ident
        self.host = host

    def original(self) -> str:
        return f"{self.nick}!{self.ident}@{self.host}"

    def __repr__(self) -> str:
        return self.original()


class IrcSenderServer(IrcSender):
    host: str

    def __init__(self, host: str) -> None:
        self.host = host

    def __repr__(self) -> str:
        return f"{self.host}"


class IrcLine:
    tags: dict[str, str]
    sender: Optional[IrcSenderUser | IrcSenderServer]
    cmd: str
    args: list[str]

    def __init__(
        self,
        tags: dict[str, str],
        sender: Optional[IrcSenderUser | IrcSenderServer],
        cmd: str,
        args: list[str],
    ) -> None:
        self.tags = tags
        self.sender = sender
        self.cmd = cmd
        self.args = args

    def __repr__(self) -> str:
        return f"{self.tags} {self.sender} {self.cmd} {self.args}"


def parse_line(line: str) -> IrcLine:
    splt = line.split(" ")
    tags = {}

    if splt[0].startswith("@"):
        tagstring = splt.pop(0)[1:]

        for tag in tagstring.split(","):
            key, val = tag.split("=")
            tags[key] = val

    sender: Optional[IrcSenderUser | IrcSenderServer]

    if splt[0].startswith(":"):
        sender_string = splt.pop(0)[1:]

        if "!" in sender_string:
            nick, rest = sender_string.split("!")
            ident, host = rest.split("@")
            sender = IrcSenderUser(nick, ident, host)
        else:
            sender = IrcSenderServer(sender_string)
    else:
        sender = None

    cmd = splt.pop(0)
    args = []

    for i in range(0, len(splt)):
        arg = splt[i]

        if arg.startswith(":"):
            final_arg = " ".join(splt[i:])[1:]
            args.append(final_arg)
            break

        args.append(arg)

    return IrcLine(tags, sender, cmd, args)
