from botapitamtam import BotHandler
import sqlite3
import os
import urllib
import json
import logging
import re
#from googletrans import Translator
#from google_trans_new import google_translator
#translator = google_translator()
import translators as ts
from langdetect import detect
#import langid
#from textblob import TextBlob

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

config = 'config.json'
# base_url = 'https://translate.yandex.net/api/v1.5/tr.json/'
lang_all = {}
with open(config, 'r', encoding='utf-8') as c:
    conf = json.load(c)
    token = conf['access_token']
    # key = conf['key']

bot = BotHandler(token)
#translator = Translator()

if not os.path.isfile('users.db'):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE users
                      (id INTEGER PRIMARY KEY , lang TEXT)
                   """)
    conn.commit()
    c.close()
    conn.close()

conn = sqlite3.connect("users.db", check_same_thread=False)


def set_lang(lang, id):
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (id, lang) VALUES ({}, '{}')".format(id, lang))
        logger.info('Creating a new record for chat_id(user_id) - {}, lang - {}'.format(id, lang))
    except:
        c.execute("UPDATE users SET lang = '{}' WHERE id = {}".format(lang, id))
        logger.info('Update lang - {} for chat_id(user_id) - {}'.format(lang, id))
    conn.commit()
    c.close()
    return


def get_lang(id):
    c = conn.cursor()
    c.execute("SELECT lang FROM users WHERE id= {}".format(id))
    lang = c.fetchone()
    if lang:
        lang = lang[0]
    else:
        lang = None
    c.close()
    return lang


def url_encode(txt):
    return urllib.parse.quote(txt)


def translate(text, lang):
    translate_res = None
    if lang == 'auto':
        lang_res = 'ru'
    else:
        lang_res = lang
    try:
        #print(text)
        #lang_detect = translator.detect('next')
        #lang_detect = TextBlob(text).detect_language()
        lang_detect = detect(text)
        #print(lang_detect)
        #print(langid.classify(text)[0])
        #print(TextBlob(text).detect_language())
    except Exception as e:
        logger.error("Error detect lang: %s.", e)
        lang_detect = 'en'
    if lang == 'auto' and lang_detect == 'ru':
        lang_res = 'en'
    if lang == 'auto' and lang_detect == 'en':
        lang_res = 'ru'
    if lang_res != lang_detect:
        try:
            #translate_res = translator.translate(text=text, lang_tgt=lang_res).text
            #translate_res = ts.bing(text, from_language='auto', to_language=lang_res)
            translate_res = ts.google(text, to_language=lang_res, if_use_cn_host=False)
            #print(translate_res)
            #print(TextBlob(text).translate(to=lang_res))
        except Exception as e:
            logger.error("Error translate: %s.", e)
    return translate_res, lang_detect


def symbol_control(TXT):
    res = True
    TXT = re.sub("(?P<url>https?://[^\s]+)", '', TXT)
    TXT = re.sub('(\r|\n)', '', TXT)
    TXT = re.sub('[^A-Za-zА-Яа-я ]', '', TXT)
    TXT = re.sub('^ ', '', TXT)
    TXT = re.sub(' +', ' ', TXT)
    TXT = re.sub(' *$', '', TXT)
    if len(TXT) < 2:
        res = False
    return res


def main():
    res_len = 0
    while True:
        last_update = bot.get_updates()
        if last_update:
            type_upd = bot.get_update_type(last_update)
            chat_id = bot.get_chat_id(last_update)
            mid = bot.get_message_id(last_update)
            text = bot.get_text(last_update)
            if type_upd == 'bot_started':
                bot.send_message(
                    'Отправьте или перешлите боту текст. Язык переводимого текста определяется автоматически. '
                    'Перевод по умолчанию на русский. Для изменения направления перевода используйте команду /lang\n'
                    'Send or forward bot text. The language of the translated text is determined automatically. The '
                    'default translation into Russian. To change the translation direction, use the command /lang',
                    chat_id)
                set_lang('ru', chat_id)
            if chat_id:
                lang = get_lang(chat_id)
                if not lang and '-' in str(chat_id):
                    lang = 'ru'
                    set_lang('ru', chat_id)
                elif not lang:
                    lang = 'auto'
                    set_lang('auto', chat_id)
            else:
                lang = 'auto'
            if type_upd == 'message_construction_request':
                text_const = text
                sid = bot.get_session_id(last_update)
                if text_const:
                    translt, lang_detect = translate(text_const, 'en')
                    if translt:
                        bot.send_construct_message(sid, hint=None, text=translt)
                        logger.info('use constructor in chat_id: {}, lang: {}'.format(chat_id, lang_detect))
                    else:
                        bot.send_construct_message(sid, 'Введите текст для перевода на Английский и отправки в чат | '
                                                        'Enter the text to be translated into English and sent to chat')
                else:
                    bot.send_construct_message(sid, 'Введите текст для перевода на Английский и отправки в чат | '
                                                    'Enter the text to be translated into English and send to chat')
            if type_upd == 'message_callback':
                payload = bot.get_payload(last_update)
                callback_id = bot.get_callback_id(last_update)
                if payload:
                    set_lang(payload, chat_id)
                    lang = get_lang(chat_id)
                    if lang == 'ru':
                        bot.send_answer_callback(callback_id, 'Текст будет переводиться на Русский')
                        bot.delete_message(mid)
                    elif lang == 'auto':
                        bot.send_answer_callback(callback_id, 'Русский|English - автоматически|automatically')
                        bot.delete_message(mid)
                    else:
                        bot.send_answer_callback(callback_id, 'Text will be translated into English')
                        bot.delete_message(mid)
            if type_upd == 'message_created':
                name = bot.get_name(last_update)
                admins = bot.get_chat_admins(chat_id)
                text = bot.get_text(last_update)
                #print(text)
                #try:
                    #text = re.sub(r'[^\w\s,.?!/:~`@#$%^&*()_+={}№;"><]', '', str(txt))
                    #text = re.sub("(?P<url>https?://[^\s]+)", '', text)
                #except Exception as e:
                #    logger.error("Error text correct: %s.", e)
                #    text = txt
                if not admins or admins and name in [i['name'] for i in admins['members']]:
                    if text == '/lang' or text == '@gotranslatebot /lang':
                        buttons = [[{"type": 'callback',
                                     "text": 'Авто|Auto',
                                     "payload": 'auto'},
                                    {"type": 'callback',
                                     "text": 'Русский',
                                     "payload": 'ru'},
                                    {"type": 'callback',
                                     "text": 'English',
                                     "payload": 'en'}]]
                        bot.send_buttons('Направление перевода\nTranslation direction', buttons,
                                         chat_id)  # вызываем три кнопки с одним описанием
                        text = None
                    if text == '/lang ru' or text == '@gotranslatebot /lang ru':
                        set_lang('ru', chat_id)
                        bot.send_message('Текст будет переводиться на Русский', chat_id)
                        text = None
                    if text == '/lang en' or text == '@gotranslatebot /lang en':
                        set_lang('en', chat_id)
                        bot.send_message('Text will be translated into English', chat_id)
                        text = None
                    if text == '/lang auto' or text == '@gotranslatebot /lang auto':
                        set_lang('auto', chat_id)
                        bot.send_message('Русский|English - автоматически|automatically', chat_id)
                        text = None

                    att_type = bot.get_attach_type(last_update)
                    if text and att_type != 'share' and type_upd != 'message_constructed':  # and symbol_control(text)
                        translt, lang_detect = translate(text, lang)
                        if translt:
                            len_sym = len(translt)
                            if len_sym != 0:
                                res_len += len_sym
                                logger.info(
                                    'chat_id: {}, lang: {}, len symbols: {}, result {}'.format(chat_id, lang_detect,
                                                                                               len_sym,
                                                                                               res_len))
                                if '-' in str(chat_id):
                                    bot.send_reply_message(translt, mid, chat_id)
                                else:
                                    bot.send_message(translt, chat_id)
                            else:
                                bot.send_message('Перевод невозможен\nTranslation not available', chat_id)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.error('Stop')
        exit()
