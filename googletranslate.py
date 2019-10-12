from botapitamtam import BotHandler
import urllib
import json
import logging
from googletrans import Translator

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

config = 'config.json'
#base_url = 'https://translate.yandex.net/api/v1.5/tr.json/'
lang_all = {}
with open(config, 'r', encoding='utf-8') as c:
    conf = json.load(c)
    token = conf['access_token']
    #key = conf['key']

bot = BotHandler(token)
translator = Translator()


def url_encode(txt):
    return urllib.parse.quote(txt)


def main():
    res_len = 0
    marker = None
    while True:
        update = bot.get_updates(marker)
        if update is None:  # проверка на пустое событие, если пусто - возврат к началу цикла
            continue
        marker = bot.get_marker(update)
        updates = update['updates']
        for last_update in list(updates):  # формируем цикл на случай если updates вернул список из нескольких событий
            type_upd = bot.get_update_type(last_update)
            text = bot.get_text(last_update)
            chat_id = bot.get_chat_id(last_update)
            payload = bot.get_payload(last_update)
            if text == '/lang':
                buttons = [[{"type": 'callback',
                             "text": 'Русский',
                             "payload": 'ru'},
                            {"type": 'callback',
                             "text": 'English',
                             "payload": 'en'}]]
                bot.send_buttons('Направление перевода', buttons, chat_id)  # вызываем две кнопки с одним описанием
                text = None
            if text == '/lang ru':
                lang_all.update({chat_id: 'ru'})
                bot.send_message('Текст будет переводиться на Русский', chat_id)
                text = None
            if text == '/lang en':
                lang_all.update({chat_id: 'en'})
                bot.send_message('Текст будет переводиться на English', chat_id)
                text = None
            if payload is not None:
                lang_all.update({chat_id: payload})
                lang = lang_all.get(chat_id)
                text = None
                if lang == 'ru':
                    bot.send_message('______\nТекст будет переводиться на Русский', chat_id)
                else:
                    bot.send_message('______\nТекст будет переводиться на English', chat_id)
            if type_upd == 'bot_started':
                bot.send_message(
                    'Отправте или перешлите боту текст. Язык переводимого текста определяется автоматически. '
                    'Перевод по умолчанию на русский. Для изменения направления перевода используйте команду /lang',
                    chat_id)
                lang_all.update({chat_id: 'ru'})
                text = None
            if chat_id in lang_all.keys():
                lang = lang_all.get(chat_id)
            else:
                lang = 'ru'
            if text is not None:
                try:
                    lang_detect = translator.detect(text).lang
                except Exception as e:
                    logger.error("Error: %s.", e)
                    lang_detect = 'en'
                if lang_detect == 'ru':
                    lang = 'en'
                if lang_detect == 'en':
                    lang = 'ru'
                try:
                    translate = translator.translate(text=text, dest=lang).text
                except Exception as e:
                    logger.error("Error: %s.", e)
                    translate = None
                len_sym = len(translate)
                if len_sym != 0:
                    res_len += len_sym
                    logger.info('chat_id: {}, lang: {}, len symbols: {}, result {}'.format(chat_id, lang_detect, len_sym, res_len))
                    bot.send_message(translate, chat_id)
                else:
                    bot.send_message('Перевод не возможен\nTranslation not available', chat_id)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
