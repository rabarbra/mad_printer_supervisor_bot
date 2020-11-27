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
import telebot
import cherrypy
import requests
from models import User
from data import db_session

WEBHOOK_HOST = '212.80.216.227'
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_cert.pem'
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token)

bot=telebot.TeleBot(config.token)

class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if db_session.query(exists().where(User.chat_id == message.chat.id)).scalar():
        user = User.query.filter_by(chat_id = message.chat.id).first()
    else:
        user = User(message.chat.id)
    msg = bot.send_message(message.chat.id, config.messages[0])
    bot.register_next_step_handler(msg, process_step, 0)

@bot.message_handler(func=lambda message: True)
def process_all(message):
    if message.content_type == "text":
        if message.text == "Сначала":
            send_welcome(message)
        if message.text == "Поменять фото":
            msg = bot.send_message(message.chat.id, config.messages[8])
            bot.register_next_step_handler(msg, process_step, 8)

@bot.message_handler(content_types=['photo'])
def process_photos(message):
    existing_ids = tuple(user_dict.keys())
    if message.chat.id in existing_ids:
        handle_photo(message, {**user_dict[message.chat.id]})

def process_step(message, step):
    try:
        markup = telebot.types.ReplyKeyboardMarkup()
        markup.row("Пропустить")
        markup.row("Сначала", "Поменять фото")
        chat_id = message.chat.id
        if message.content_type == "text":
            if message.text == "Сначала" or message.text == "/start" or message.text == "/help":
                send_welcome(message)
                return()
            if message.text == "Поменять фото":
                msg = bot.send_message(message.chat.id, config.messages[8], reply_markup = markup)
                bot.register_next_step_handler(msg, process_step, 8)
                return()
        if step == 0:
            user = {"name" : message.text}
            user_dict[chat_id] = user
            msg = bot.send_message(message.chat.id, config.messages[step + 1], reply_markup = markup)
            bot.register_next_step_handler(msg, process_step, step + 1)
        elif step == 8:
            existing_ids = tuple(user_dict.keys())
            if chat_id in existing_ids:
                user = user_dict[chat_id]
            else:
                send_welcome(message)
            for step in steps:
                if step not in user:
                   user[step] = "Пропустить"
            handle_photo(message, {**user})
        else:
            user = user_dict[chat_id]
            user[steps[step]] = message.text
            msg = bot.send_message(message.chat.id, config.messages[step + 1], reply_markup = markup)
            bot.register_next_step_handler(msg, process_step, step + 1)
    except Exception as e:
        bot.reply_to(message, "Эх, ошибка...\nПопробуй ещё раз.")
        print(e)

bot.enable_save_next_step_handlers(delay = 2)
bot.load_next_step_handlers()

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, certificate=open(WEBHOOK_SSL_CERT, 'r'))

cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
