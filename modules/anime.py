from __future__ import annotations
from typing import TYPE_CHECKING
from core.module import Module
from core.irc_line import IrcSenderUser
from asyncio import to_thread
from random import choice
from urllib.parse import quote_plus
from requests import get as requests_get
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from core.irc_bot import IrcBot

BASE_URL = "https://danbooru.donmai.us"
TIMEOUT = 15
USER_AGENT = "pybot2/1.0 (IRC Bot)"


def normalize_tags(raw: str) -> str:
    tags = ["_".join(t.strip().split()) for t in raw.split(",")]
    tags = [t for t in tags if t]
    tags = ["order:random", "rating:general", *tags]
    return " ".join(tags)


def scrape_posts(tags: str) -> list[str]:
    params = {"tags": tags}
    headers = {"User-Agent": USER_AGENT}
    resp = requests_get(
        f"{BASE_URL}/posts", params=params, headers=headers, timeout=TIMEOUT
    )

    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links: list[str] = []

    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        post_id = href.split("?")[0].rstrip("/").split("/")[-1]

        if href.startswith("/posts/") and post_id.isdigit():
            links.append(f"{BASE_URL}/posts/{post_id}")

    return list(set(links))


def scrape_direct_image(post_url: str) -> str | None:
    headers = {"User-Agent": USER_AGENT}
    resp = requests_get(post_url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tag = soup.find("meta", attrs={"property": "og:image"})

    if tag is not None:
        return str(tag.get("content", None))
    else:
        return None


class ModuleMain(Module):
    def __init__(self, name: str, bot: IrcBot) -> None:
        super().__init__(name, bot)

        self.register_irc_command_handler(
            "anime",
            self.handle_anime,
            "<tag>, <tag>, ...",
            "Search Danbooru for tags",
            min_args=1,
        )

    async def handle_anime(
        self,
        tags: dict[str, str | None],
        sender: IrcSenderUser,
        channel: str,
        args: list[str],
    ) -> None:
        query = normalize_tags(" ".join(args))

        if not query:
            self.bot.send_message(channel, "Usage: anime <tag>, <tag>, ...")
            return

        try:
            posts = await to_thread(scrape_posts, query)
        except Exception as err:
            self.bot.send_message(channel, f"Danbooru search failed: {err}")
            return

        if not posts:
            search_url = f"{BASE_URL}/posts?tags={quote_plus(query)}"
            self.bot.send_message(channel, f"No results for: {query} ({search_url})")
            return

        post_url = choice(posts)

        try:
            result = await to_thread(scrape_direct_image, post_url)

            if result:
                self.bot.send_message(channel, result)
            else:
                self.bot.send_message(channel, "No results.")

        except Exception as err:
            self.bot.send_message(channel, f"Fetch failed: {err}")
            return
