"""tg forward app"""

import logging
import os
import sys
from contextlib import suppress
from urllib.parse import urlparse

from aiohttp import web
from aiotg import Bot, BotApiError

from tg_forward.rest import RestHandlers
from tg_forward.security import Token
from tg_forward.tgbot import BotHandlers


def init_logger():
    """Create stream logger"""
    logger = logging.getLogger("tg-fwd")

    log_level = getattr(logging, os.environ.get("FWD_LOG_LEVEL", "INFO").upper())

    logger.setLevel(log_level)

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


async def bot_shutdown(app):
    """Bot shutdown handler"""
    logger = logging.getLogger("tg-fwd")
    logger.info("Bot shutdown handler")

    bot = app["bot"]

    logger.info("Delete bot webhook")
    with suppress(BotApiError):
        await bot.delete_webhook()
        logger.info("Delete bot webhook ... OK!")

    with suppress(Exception):
        await bot.session.close()
        logger.info("Bot session closed")


def main():
    """Main app"""
    logger = init_logger()

    # Loading settings
    try:
        setting = {
            "token": os.environ["FWD_TOKEN"],
            "keys_path": os.environ["FWD_KEYS_PATH"],
            "salt": int(os.environ["FWD_SALT"]),
            "webhook_url": os.environ["FWD_WEBHOOK_URL"],
            "listen_addr": os.environ.get("FWD_LISTEN_ADDR", "127.0.0.1"),
            "listen_port": int(os.environ.get("FWD_LISTEN_PORT", 8080)),
        }
    except KeyError as err:
        logger.critical("Setting %s not found. Exit!", err)
        sys.exit(1)
    except ValueError:
        logger.critical("Invalid setting value. Check `FWD_SALT` or `FWD_LISTEN_PORT`. Exit!")
        sys.exit(1)

    # Init token module
    base_dir = os.path.realpath(setting["keys_path"])
    if not os.path.isdir(base_dir):
        logger.critical("Invalid directory in `FWD_KEYS_PATH`: %s", base_dir)
        sys.exit(1)

    token = Token(
        pub_key_path=os.path.join(base_dir, "fwd_pub.pem"),
        priv_key_path=os.path.join(base_dir, "fwd_priv.pem"),
        salt=setting["salt"]
    )

    # Init bot module
    parsed_url = urlparse(setting["webhook_url"])
    bot = Bot(api_token=setting["token"])
    bot_handlers = BotHandlers(
        token=token,
        base_api_url="{p.scheme}://{p.netloc}".format(p=parsed_url)
    )

    bot.add_command("token", bot_handlers.token_handler)
    bot.add_command("ping", bot_handlers.ping_handler)
    bot.add_command("help", bot_handlers.help_handler)

    try:
        logger.info("Register webhook...")
        bot.set_webhook(setting["webhook_url"])
        logger.info("Register webhook... OK!")
    except BotApiError as err:
        logger.error("Register webhook... ERROR!")
        logger.critical("Unable to register webhook: %s", err)
        sys.exit(2)

    # Init web app
    app = web.Application()
    app["bot"] = bot
    app.on_cleanup.append(bot_shutdown)

    web_handlers = RestHandlers(token=token, bot=bot)
    app.add_routes(
        [
            web.post("/in", web_handlers.incomming_message),
            web.get("/v1/message", web_handlers.send_message),
            web.post("/v1/message", web_handlers.send_message),
            web.put("/v1/message", web_handlers.update_message),
            web.delete("/v1/message", web_handlers.delete_message),
        ]
    )

    web.run_app(
        app,
        host=setting["listen_addr"],
        port=setting["listen_port"],
        access_log=logger
    )

    logger.info("Web application closed. Exit!")


if __name__ == "__main__":
    main()
