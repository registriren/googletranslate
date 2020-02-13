from botapitamtam import BotHandler
import urllib
import json
import logging
import re
from googletrans import Translator

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
translator = Translator()


def url_encode(txt):
    return urllib.parse.quote(txt)


def translate(text, lang):
    translate_res = None
    if lang == 'auto':
        lang_res = 'ru'
    else:
        lang_res = lang
    try:
        lang_detect = translator.detect(text).lang
    except Exception as e:
        logger.error("Error detect lang: %s.", e)
        lang_detect = 'en'
    if lang == 'auto' and lang_detect == 'ru':
        lang_res = 'en'
    if lang == 'auto' and lang_detect == 'en':
        lang_res = 'ru'
    if lang_res != lang_detect:
        try:
            translate_res = translator.translate(text=text, dest=lang_res).text
        except Exception as e:
            logger.error("Error translate: %s.", e)
    return translate_res, lang_detect


def main():
    res_len = 0
    while True:
        last_update = bot.get_updates()
        if last_update:  # формируем цикл на случай если updates вернул список из нескольких событий
            type_upd = bot.get_update_type(last_update)
            txt = bot.get_text(last_update)
            try:
                text = re.sub(r'[^\w\s,.?!/:~`@#$%^&*()_+={}№;"><]', '', txt)
            except Exception as e:
                logger.error("Error text correct: %s.", e)
                text = txt
            chat_id = bot.get_chat_id(last_update)
            payload = bot.get_payload(last_update)
            callback_id = bot.get_callback_id(last_update)
            mid = bot.get_message_id(last_update)
            name = bot.get_name(last_update)
            admins = bot.get_chat_admins(chat_id)
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
                    lang_all.update({chat_id: 'ru'})
                    bot.send_message('Текст будет переводиться на Русский', chat_id)
                    text = None
                if text == '/lang en' or text == '@gotranslatebot /lang en':
                    lang_all.update({chat_id: 'en'})
                    bot.send_message('Text will be translated into English', chat_id)
                    text = None
                if text == '/lang auto' or text == '@gotranslatebot /lang auto':
                    lang_all.update({chat_id: 'auto'})
                    bot.send_message('Русский|English - автоматически|automatically', chat_id)
                    text = None
                if payload is not None:
                    lang_all.update({chat_id: payload})
                    lang = lang_all.get(chat_id)
                    text = None
                    if lang == 'ru':
                        bot.send_answer_callback(callback_id, 'Текст будет переводиться на Русский')
                        bot.delete_message(mid)
                    elif lang == 'auto':
                        bot.send_answer_callback(callback_id, 'Русский|English - автоматически|automatically')
                        bot.delete_message(mid)
                    else:
                        bot.send_answer_callback(callback_id, 'Text will be translated into English')
                        bot.delete_message(mid)

            if type_upd == 'bot_started':
                bot.send_message(
                    'Отправьте или перешлите боту текст. Язык переводимого текста определяется автоматически. '
                    'Перевод по умолчанию на русский. Для изменения направления перевода используйте команду /lang',
                    chat_id)
                lang_all.update({chat_id: 'ru'})
                text = None
            if chat_id in lang_all.keys():
                lang = lang_all.get(chat_id)
            elif '-' in str(chat_id):
                lang = 'ru'
            else:
                lang = 'auto'
            if type_upd == 'message_construction_request':
                text_const = bot.get_construct_text(last_update)
                sid = bot.get_session_id(last_update)
                if text_const:
                    translt, lang_detect = translate(text_const, 'en')
                    if translt:
                        bot.send_construct_message(sid, hint=None, text=translt)
                    else:
                        bot.send_construct_message(sid, 'Введите текст для перевода на Английский и отправки в чат | '
                                                        'Enter the text to be translated into English and sent to chat')
                else:
                    bot.send_construct_message(sid, 'Введите текст для перевода на Английский и отправки в чат | '
                                                    'Enter the text to be translated into English and send to chat')
            elif text:
                translt, lang_detect = translate(text, lang)
                if translt:
                    len_sym = len(translt)
                    if len_sym != 0:
                        res_len += len_sym
                        logger.info(
                            'chat_id: {}, lang: {}, len symbols: {}, result {}'.format(chat_id, lang_detect, len_sym,
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
        exit()
