import telebot
import time
import requests
import json

bot = telebot.TeleBot('7030847910:AAG76nvYEyIgpvbzXtysXubyuVaRYA8puhU')

nodes = ['http://192.168.1.37:5001', 'http://192.168.1.37:5002', 'http://192.168.1.37:5003']

weather_codes = {
    0.0: "Чисте небо",
    **dict.fromkeys([1.0, 2.0, 3.0], "Переважно ясно, мінлива хмарність, похмуро"),
    **dict.fromkeys([45.0, 48.0], "Туман. Утворення туману"),
    **dict.fromkeys([51.0, 53.0, 55.0], "Мряка: слабка, помірна та густа"),
    **dict.fromkeys([56.0, 57.0], "Крижаний дощ: легкий і щільний"),
    **dict.fromkeys([80.0, 81.0, 82.0], "Дощ: з помірним вітром")
}

# Переместил Ваши кнопки и клавиатуры отдельно от кода.
connect1 = telebot.types.InlineKeyboardButton(text='1', callback_data='connect1')
connect2 = telebot.types.InlineKeyboardButton(text='2', callback_data='connect2')
connect3 = telebot.types.InlineKeyboardButton(text='3', callback_data='connect3')

weather = telebot.types.InlineKeyboardButton(text='Погода', callback_data='weather')
get_chain = telebot.types.InlineKeyboardButton(text='Ланцюг', callback_data='get_chain')
change_node = telebot.types.InlineKeyboardButton(text='Змінити Ноду', callback_data='change_node')
exit_btn = telebot.types.InlineKeyboardButton(text='Вийти', callback_data='exit')

markup = telebot.types.InlineKeyboardMarkup([[ connect1, connect2, connect3 ]])

markup1 = telebot.types.InlineKeyboardMarkup([[ weather, get_chain, change_node ], [exit_btn]])

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "☁️*Вітаємо в боті надання погодних даних*☁️\n\n"
                                      "Щоб розпочати роботу з програмою, підключіться до однієї з нижче наданих нод:\n\n"
                                      f"*1)* - {nodes[0]}🟢\n"
                                      f"*2)* - {nodes[1]}🟢\n"
                                      f"*3)* - {nodes[2]}🟢", reply_markup=markup, parse_mode="Markdown")

url = ''
@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    global url
    if call.data == 'connect1':
        msg = bot.send_message(call.message.chat.id, "Гарний вибір!\n"
                                                     "Під'єднуюсь до ноди №5001...")
        url += nodes[0]
        time.sleep(2)
        bot.delete_message(call.message.chat.id, message_id=msg.message_id)

        bot.send_message(call.message.chat.id, "Успішно під'єднались до Ноди №5001🥳\n\n"
                                               "Тепер ви можете дізнатись актуальну погоду", reply_markup=markup1)
    elif call.data == 'connect2':
        msg = bot.send_message(call.message.chat.id, "Гарний вибір!\n"
                                                     "Під'єднуюсь до ноди №5002...")
        url = nodes[0]
        time.sleep(2)
        bot.delete_message(call.message.chat.id, message_id=msg.message_id)

        bot.send_message(call.message.chat.id, "Успішно під'єднались до Ноди №5002🥳\n\n"
                                               "Тепер ви можете дізнатись актуальну погоду", reply_markup=markup1)
    elif call.data == 'connect3':
        msg = bot.send_message(call.message.chat.id, "Гарний вибір!\n"
                                                     "Під'єднуюсь до ноди №5003...")
        url = nodes[0]
        time.sleep(2)
        bot.delete_message(call.message.chat.id, message_id=msg.message_id)

        bot.send_message(call.message.chat.id, "Успішно під'єднались до Ноди №5003🥳\n\n"
                                               "Тепер ви можете дізнатись актуальну погоду", reply_markup=markup1)
    elif call.data == 'weather':
        print(url)
        response = requests.get(f"{url}/mining_block").text
        data_received = json.loads(response)

        code = data_received["data"][0]["block_data"]["weather_code"]
        coordinates = data_received["data"][0]["block_data"]["coordinates"]
        timestamp = data_received["timestamp"]
        message = ("Погода в Києві на сьогодні\n"
                   f"({coordinates[0]}, {coordinates[1]})\n"
                   f"{weather_codes[code]}\n"
                   f"{timestamp[:-7]}")

        bot.send_message(call.message.chat.id, message, reply_markup=markup1)
    elif call.data == 'get_chain':
        requests.get(f"{url}/replace_chain")
        response = requests.get(f"{url}/get_chain").text
        data_received = json.loads(response)['chain']
        if len(data_received) == 1:
            bot.send_message(call.message.chat.id, "*Ви ще не маєте збереженої інформації в Ланцюгу*", parse_mode="Markdown")

        message = '*Погода в Києві*\n\n'
        counter = 1
        for block in data_received:
            if block['data'] == []:
                continue
            code = block["data"][0]["block_data"]["weather_code"]
            coordinates = block["data"][0]["block_data"]["coordinates"]
            timestamp = block["timestamp"]
            message += (f"*{counter})* {coordinates[0], coordinates[1]}\n"
                        f"{weather_codes[code]}\n"
                        f"{timestamp}\n\n")
            counter += 1
        bot.send_message(call.message.chat.id, message, reply_markup=markup1, parse_mode="Markdown")

    elif call.data == 'change_node':
        bot.send_message(call.message.chat.id, "⚡*Зміна Ноди*⚡\n\n"
                                                "Список актуальних наразі нод:\n\n"
                                                f"*1)* - {nodes[0]}🟢\n"
                                                f"*2)* - {nodes[1]}🟢\n"
                                                f"*3)* - {nodes[2]}🟢", reply_markup=markup, parse_mode="Markdown")

    elif call.data == 'exit':
        bot.send_message(call.message.chat.id, "🔴*Вихід пройшов успішно*🔴", parse_mode="Markdown")
        exit()




if __name__ == '__main__':
    # schedule.every().day.at('22:11').do(send_message)
    # Thread(target=schedule_checker).start()
    bot.polling(none_stop=True)
