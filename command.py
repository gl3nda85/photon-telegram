import json
import codecs
import requests
from bs4 import BeautifulSoup, SoupStrainer
import re
import subprocess
from telegram.ext.dispatcher import run_async
from telegram.ext import Updater
from html import escape
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import conf

rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8984"%(conf.rpc_username, conf.rpc_password))

updater = Updater(token=conf.bot_token)
dispatcher = updater.dispatcher

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

def commands(bot, update):
	user = update.message.from_user.username 
	bot.send_message(chat_id=update.message.chat_id, text="Initiating commands /tip & /withdraw have a specfic format,\n use them like so:" + "\n \n Parameters: \n <user> = target user to tip \n <amount> = amount of Photon to utilise \n <address> = Photon address to withdraw to \n \n Tipping format: \n /tip <user> <amount> \n \n Withdrawing format: \n /withdraw <address> <amount>")

def help(bot, update):
	bot.send_message(chat_id=update.message.chat_id, text="The following commands are at your disposal: /hi , /commands , /deposit , /tip , /withdraw , /price , /marketcap or /balance")

def deposit(bot, update):
	user = update.message.from_user.username
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		result = rpc_connection.getaccountaddress(user)
		bot.send_message(chat_id=update.message.chat_id, text="@{0} your depositing address is: {1}".format(user,result))

def tip(bot,update):
	user = update.message.from_user.username
	target = update.message.text[5:]
	amount =  target.split(" ")[1]
	target =  target.split(" ")[0]
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		testMachine = '@photontestbot'
		machine = "@PhotonTipBot"	
		if "@" in target:
			target = target[1:]
			print(target)
			user = update.message.from_user.username
			result  = rpc_connection.getbalance(user)
			balance = float(result)
			amount = float(amount)
			if balance < amount:
				bot.send_message(chat_id=update.message.chat_id, text="@{0} you have insufficent funds.".format(user))
			elif amount <= 0:
				bot.send_message(chat_id=update.message.chat_id, text="@{0} please use a value greater than 0".format(user))
			elif target == user:
				bot.send_message(chat_id=update.message.chat_id, text="You can't tip yourself silly.")
			else:
				if target == machine or target == testMachine:
					tx = rpc_connection.sendfrom(user, conf.contribution_address, amount)
					bot.send_message(chat_id=update.message.chat_id, text="Thanks for contributing to the tip bot!")
				else:	
					tx = rpc_connection.move(user, target, amount)
					balance = str(balance)
					amount = str(amount)
					bot.send_message(chat_id=update.message.chat_id, text="@{0} tipped @{1} of {2} PHO".format(user, target, amount))
		else: 
			bot.send_message(chat_id=update.message.chat_id, text="Error that user is not applicable. please make sure you tag the user with @")

def balance(bot,update):
	quote_page = requests.get('https://api.coinmarketcap.com/v2/ticker/175/?convert=ltc')
	jsonResult = quote_page.json()
	data = jsonResult['data']
	ltcPrice = float(data['quotes']['LTC']['price'])
	usdPrice = float(data['quotes']['USD']['price'])
	user = update.message.from_user.username
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		result  = rpc_connection.getbalance(user)
		clean = float(result)
		balance  = float(clean)
		fiat_balance = balance * usdPrice
		fiat_balance = str(round(fiat_balance,3))
		ltc_balance = balance * ltcPrice
		ltc_balance = str(round(ltc_balance,3))
		balance =  str(round(balance,3))
		bot.send_message(chat_id=update.message.chat_id, text="@{0} your current balance is: {1} PHO ≈  ${2} or {3} LTC".format(user,balance,fiat_balance, ltc_balance))

def price(bot,update):
	quote_page = requests.get('https://api.coinmarketcap.com/v2/ticker/175/?convert=ltc')
	jsonResult = quote_page.json()
	data = jsonResult['data']
	ltcPriceChange = data['quotes']['LTC']['percent_change_1h']
	ltcPrice = float(data['quotes']['LTC']['price'])
	usdPrice = float(data['quotes']['USD']['price'])
	bot.send_message(chat_id=update.message.chat_id, text="Photon is valued at {0} LTC and {1} USD Δ %{2}".format(ltcPrice, usdPrice, ltcPriceChange))

def withdraw(bot,update):
	user = update.message.from_user.username
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		target = update.message.text[9:]
		address = target[:35]
		address = ''.join(str(e) for e in address)
		target = target.replace(target[:35], '')
		amount = float(target)
		result  = rpc_connection.getbalance(user)
		clean = float(result)
		balance = float(clean)
		if balance < amount:
			bot.send_message(chat_id=update.message.chat_id, text="@{0} you have insufficent funds.".format(user))
		else:
			tx = rpc_connection.sendfrom(user, address, amount)
			amount = str(amount)
			bot.send_message(chat_id=update.message.chat_id, text="@{0} has successfully withdrew to address: {1} of {2} PHO" .format(user,address,amount))

def hi(bot,update):
	user = update.message.from_user.username
	bot.send_message(chat_id=update.message.chat_id, text="Hello @{0}, how are you doing today?".format(user))

def moon(bot,update):
  bot.send_message(chat_id=update.message.chat_id, text="Moon mission inbound!")

def marketcap(bot,update):
	quote_page = requests.get('https://api.coinmarketcap.com/v2/ticker/175/?convert=ltc')
	jsonResult = quote_page.json()
	data = jsonResult['data']

	ltcMarketCap = data['quotes']['LTC']['market_cap']
	usdMarketCap = data['quotes']['USD']['market_cap']
	bot.send_message(chat_id=update.message.chat_id, text="The current market cap of Photon is valued at {0} LTC and ${1} USD" .format(ltcMarketCap, usdMarketCap))


def contribute(bot, update):
	   bot.send_message(chat_id=update.message.chat_id, text='Thanks for your interest in contributing!\n\n'
                                                          'This project is run as a labour of love, but if you would like to help '
                                                          'cover my almost nonexistent server costs or buy me a coffee feel free to tip the bot:\n\n'
                                                          '/tip @PhotonTipBot <amount> \n\n'
                                                          'or contribute directly to:\n\n'
                                                          '{0} \n\n'
                                                          'Thanks for using the Photon Tipbot!'.format(conf.contribution_address))


from telegram.ext import CommandHandler

commands_handler = CommandHandler('commands', commands)
dispatcher.add_handler(commands_handler)

moon_handler = CommandHandler('moon', moon)
dispatcher.add_handler(moon_handler)

hi_handler = CommandHandler('hi', hi)
dispatcher.add_handler(hi_handler)

withdraw_handler = CommandHandler('withdraw', withdraw)
dispatcher.add_handler(withdraw_handler)

marketcap_handler = CommandHandler('marketcap', marketcap)
dispatcher.add_handler(marketcap_handler)

deposit_handler = CommandHandler('deposit', deposit)
dispatcher.add_handler(deposit_handler)

price_handler = CommandHandler('price', price)
dispatcher.add_handler(price_handler)

tip_handler = CommandHandler('tip', tip)
dispatcher.add_handler(tip_handler)

balance_handler = CommandHandler('bal', balance)
dispatcher.add_handler(balance_handler)

help_handler = CommandHandler('help', help)
dispatcher.add_handler(help_handler)

contribute_handler = CommandHandler('contribute', contribute)
dispatcher.add_handler(contribute_handler)

updater.start_polling()

