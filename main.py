#!/usr/bin/env python3

import sqlite3

import requests
import telebot
from telebot import types


DB_NAME = 'db.db'
YANDEX_TRANSLATER_TOKEN = 'trnsl.1.1.20170710T073529Z.631faefc04fe7462.e35d5f3184457b9be37d18e1198f62ead9f39156'
BOT_TOKEN = '599109013:AAEOT1vLJsyyWRFc6V0UeZ5KIzEiDIj8Z8I'
bot = telebot.TeleBot(BOT_TOKEN)

TRANSLATE = []


def get_dollar_value():
	url = 'https://www.cbr-xml-daily.ru/daily_json.js'
	json_res = requests.get(url).json()
	return json_res['Valute']['USD']['Value']


def rus_to_en(text):
	url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
	params = {
		'key': YANDEX_TRANSLATER_TOKEN,
		'text': text,
		'lang': 'en',
	}
	res = requests.post(url, params=params).json()
	return res['text']


with sqlite3.connect(DB_NAME) as connection:
	cursor = connection.cursor()
	sql = '''CREATE TABLE IF NOT EXISTS known_users (
		id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		uid INTEGER UNIQUE NOT NULL)'''
	cursor.execute(sql)
	connection.commit()


@bot.message_handler(commands=['start'])
def start_command(message):
	cid = message.chat.id
	uid = message.from_user.id

	with sqlite3.connect(DB_NAME) as connection:
		cursor = connection.cursor()
		sql = '''INSERT OR IGNORE INTO known_users (uid) VALUES (?)'''
		cursor.execute(sql, (uid,))
		connection.commit()

	text = 'Главное меню'
	markup = types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True, row_width=1)
	markup.add(types.KeyboardButton('ID'))
	markup.add(types.KeyboardButton('Переводчик'))
	markup.add(types.KeyboardButton('Курс валют'))
	return bot.send_message(cid, text, reply_markup=markup)


@bot.message_handler(content_types=['text'])
def text_handler(message):
	cid = message.chat.id
	uid = message.from_user.id

	if message.text == '⬅️ Назад':
		if uid in TRANSLATE:
			TRANSLATE.remove(uid)
		text = 'Главное меню'
		markup = types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True, row_width=1)
		markup.add(types.KeyboardButton('ID'))
		markup.add(types.KeyboardButton('Переводчик'))
		markup.add(types.KeyboardButton('Курс валют'))
		return bot.send_message(cid, text, reply_markup=markup)

	if uid in TRANSLATE:
		translate_text = rus_to_en(message.text)
		return bot.send_message(cid, translate_text)

	# Handle main buttons
	if message.text == 'ID':
		with sqlite3.connect(DB_NAME) as connection:
			cursor = connection.cursor()
			sql = '''SELECT * FROM known_users'''
			res = cursor.execute(sql).fetchall()
			connection.commit()
		print(res)
		count = len(res)
		text = 'Количество пользователей бота: *{!s}*'.format(count)
		return bot.send_message(cid, text, parse_mode='markdown')
	elif message.text == 'Переводчик':
		text = 'Напишите текст на русском языке - получите на английском.'
		text += ' Для отмены используйте кнопку "Назад"'
		markup = types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True, row_width=1)
		markup.add(types.KeyboardButton('⬅️ Назад'))
		TRANSLATE.append(uid)
		return bot.send_message(cid, text, reply_markup=markup)
	elif message.text == 'Курс валют':
		value = get_dollar_value()
		text = 'Цена 1$ на текущий момент - {!s}р.'.format(value)
		return bot.send_message(cid, text)


def main():
	bot.polling(none_stop=True)


if __name__ == '__main__':
	main()
