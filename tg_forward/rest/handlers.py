"""HTTP REST handlers module"""

from logging import getLogger

from aiohttp import web
from aiohttp.web import Request
from aiotg import Bot, Chat

from tg_forward.security import Token


class RestHandlers:
    """REST handlers"""
    def __init__(self, token: Token, bot: Bot):
        self.token = token
        self.bot = bot
        self.logger = getLogger("tg-fwd")

    def _to_tid_wrap(self, token: str) -> int:
        """Wrapper with logging and cache info

        :param token: app token
        :type token: str
        :return: telegram chat id
        :rtype: int
        """
        self.logger.info("Converting token to chat id")
        chat_id = self.token.to_tid(token)
        self.logger.debug("Cache info: %s", self.token.to_tid.cache_info())
        return chat_id

    async def send_message(self, request: Request):
        """Send message via GET or POST"""
        self.logger.info("Recieved send message request, method %s", request.method)

        options = dict()

        try:
            if request.method == "POST":
                body = await request.json()
                self.logger.debug("Request body: %s", body)

                token = body["token"]
                message = body["message"]
                parse_mode = body.get("format")
                silent_mode = body.get("silent")
            elif request.method == "GET":
                self.logger.debug("Request query: %s", request.query_string)

                token = request.query["t"]
                message = request.query["m"]
                parse_mode = request.query.get("f")
                silent_mode = request.query.get("s")

            if len(message) > 4096:
                self.logger.warning("Message to long: %i. Abort!", len(message))
                raise ValueError("Message to long")

            if parse_mode:
                if parse_mode not in {"Markdown", "HTML"}:
                    raise ValueError("Invalid `format` value. Use `Markdown` or `HTML`")
                self.logger.info("Add 'parse_mode' option %s", parse_mode)
                options["parse_mode"] = parse_mode

            if silent_mode:
                self.logger.info("Add 'disable_notification' as %s", silent_mode)
                options["disable_notification"] = silent_mode.lower() in {"true", "1", "t", "yes"}

            self.logger.info("Send message with options %s", options)
            status = await self.bot.send_message(self._to_tid_wrap(token), message, **options)
            self.logger.debug("Send result: %s", status)
            return web.json_response(
                {
                    "ok": status["ok"],
                    "messageID": status["result"]["message_id"]
                }
            )

        except (KeyError, ValueError) as err:
            self.logger.error("Invalid params: %s", err)
            raise web.HTTPBadRequest(reason="invalid params")
        except Exception as err:
            self.logger.error("Unknown error: %s", err)
            raise web.HTTPInternalServerError

    async def update_message(self, request: Request):
        """Change sended message"""
        try:
            self.logger.info("Recieved change message request, method %s", request.method)

            token = request.query["t"]
            message_id = int(request.query["mid"])
            text = request.query["m"]

            Chat(self.bot, self._to_tid_wrap(token)).edit_text(message_id, text)
            return web.json_response({"ok": True})
        except (ValueError, KeyError) as err:
            self.logger.error("Invalid query params: %s", err)
            raise web.HTTPBadRequest(reason="invalid query params")
        except Exception as err:
            self.logger.error("Unknown error: %s", err)
            raise web.HTTPInternalServerError

    async def delete_message(self, request: Request):
        """Delete message"""
        try:
            self.logger.info("Recieved delete message request, method %s", request.method)

            token = request.query["t"]
            message_id = int(request.query["mid"])

            Chat(self.bot, self._to_tid_wrap(token)).delete_message(message_id)
            return web.json_response({"ok": True})
        except (ValueError, KeyError) as err:
            self.logger.error("Invalid query params: %s", err)
            raise web.HTTPBadRequest(reason="invalid query params")
        except Exception as err:
            self.logger.error("Unknown error: %s", err)
            raise web.HTTPInternalServerError

    async def incomming_message(self, request: Request):
        """Handler for incomming message from tg bot"""
        self.logger.debug("Raw message: %s", await request.json())
        return await self.bot.webhook_handle(request)
