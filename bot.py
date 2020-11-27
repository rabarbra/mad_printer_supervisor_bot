#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
# File       : bot.py                                                          #
# License    : GNU GPL                                                         #
# Author     : rabarba <rabarbrablad@gmail.com>                                #
# Created    : 27.11.2020                                                      #
# Modified   : 27.11.2020                                                      #
# Modified by: rabarba <rabarbrablad@gmail.com>                                #
################################################################################
# -*- coding: utf-8 -*-
import config
import os
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_werbhook
from models import User
from data import db_session

WEBHOOK_HOST = '212.80.216.227'
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_cert.pem'
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token)
WEBHOOK_URL = "%s%s" % (WEBHOOK_URL_BASE, WEBHOOK_URL_PATH)

bot = Bot(token = config.token)
dp = Dispatcher(bot)

@db.message_handler()
async def echo(message: types.Message):
    return SendMessage(message.chat.id, message.text)

async def on_startup(db):
    await bot.send_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == "__main__":
    start_webhook(
            dispatcher = dp,
            webhook_path = WEBHOOK_URL_PATH,
            on_startup = on_startup,
            on_shutdown = on+shutdown,
            skip_updates = True,
            host = WEBHOOK_LISTEN,
            port = WEBHOOK_PORT,
        )

#cherrypy.config.update({
#    'server.socket_host': WEBHOOK_LISTEN,
#    'server.socket_port': WEBHOOK_PORT,
#    'server.ssl_module': 'builtin',
#    'server.ssl_certificate': WEBHOOK_SSL_CERT,
#    'server.ssl_private_key': WEBHOOK_SSL_PRIV
#})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
