"""Bot module"""

from aiotg import Chat
from logging import getLogger

from tg_forward.security import Token


class BotHandlers:
    """Bot handlers"""
    def __init__(self, token: Token, base_api_url: str):
        self.token = token
        self.logger = getLogger("tg-fwd")
        self._api_url = base_api_url

    async def ping_handler(self, chat: Chat, math):
        """Healthcheck handler"""
        self.logger.info("Recived ping request -> return pong")
        return chat.reply("pong")

    async def token_handler(self, chat: Chat, math):
        """Telegram id to API token handler"""
        self.logger.info("Recieved convert to token request")
        self.logger.debug("Raw: %s", chat.sender.items())
        token = self.token.to_token(tid=chat.sender["id"])
        self.logger.debug("Cache info: %s", self.token.to_token.cache_info())
        return chat.reply(token)

    async def help_handler(self, chat: Chat, math):
        """Help command handler"""
        self.logger.info("Recieved help request")
        help_msg = (
            "*Message forward bot*\n"
            "*/token* -- get your API token\n\n"
            "Please readme [Manual]({url})"
        ).format(url=self._api_url)
        return chat.reply(help_msg, parse_mode="Markdown")
