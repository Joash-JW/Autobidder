from telepot.loop import MessageLoop
import telepot
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from threading import Thread
from ActivateSelenium import bid
from key import token

activeUsers = {}
timeslots = {}
input_format = "%d/%m/%Y %H:%M"
precise_format = "%d/%m/%Y %H:%M:%S.0"
MAX_USERS = 2

class User:
    def __init__(self):
        self.state = 1
        self.username = None
        self.password = None
        self.time = None
        self.plan = "1"

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == 'text':
        if msg['text'] == '/about':
            bot.sendMessage(chat_id, "This bot only stores your account details till it bids for you and they will be deleted afterwards. " \
            "Your details will not be made known to anyone, including the person who made me (he is quite ethical). " \
            "Only 2 people are able to use this bot to bid for modules at any timeslot. " \
            "Please ensure that you have already planned out your modules on STARS Planner. " \
            "Note that this bot does not guarantee a 100% success rate. " \
            "To start, type '/bid'")
        elif msg['text'] == '/bid' and (chat_id not in activeUsers):
            activeUsers[chat_id] = User()
            bot.sendMessage(chat_id, "Please key in your timeslot in this format DD/MM/YYYY HH:MM")
        elif chat_id in activeUsers:
            if msg['text'] == '/cancel':
                bot.sendMessage(chat_id, "Cancelled. Please restart the process with '/bid'")
                cleanUp(chat_id)
            elif msg['text'] == '/edit' and activeUsers[chat_id].state > 1:
                cleanUp(chat_id)
                activeUsers[chat_id] = User()
                bot.sendMessage(chat_id, "Please key in your timeslot in this format DD/MM/YYYY HH:MM")
            elif activeUsers[chat_id].state == 1:
                getTimeslot(chat_id, msg['text'])
            elif activeUsers[chat_id].state == 2 or activeUsers[chat_id].state == 2.1 or activeUsers[chat_id].state == 2.2:
                getAccountDetails(chat_id, msg['text'])
            elif msg['text'] == '/edit' and activeUsers[chat_id].state == 3:
                bot.sendMessage(chat_id, "Please give me your username")
                activeUsers[chat_id].state = 2
        else:
            bot.sendMessage(chat_id, "Use '/bid' to start")

def getTimeslot(chat_id, text):
    if checkText(text): # if valid
        precise_dt = datetime.strptime(text, input_format).strftime(precise_format) #change M to MM and add Seconds and ms precision
        if precise_dt in timeslots:
            if len(timeslots[precise_dt]) == MAX_USERS:
                bot.sendMessage(chat_id, "Your selected timeslot is full. Please restart the process with '/bid'")
                del activeUsers[chat_id]
            else:
                timeslots[precise_dt].append(chat_id)
                activeUsers[chat_id].state = 2
                activeUsers[chat_id].time = precise_dt
                bot.sendMessage(chat_id, "Please give me your username")
        else: # if not in dict of timeslots
            timeslots[precise_dt] = [chat_id]
            activeUsers[chat_id].state = 2
            activeUsers[chat_id].time = precise_dt
            bot.sendMessage(chat_id, "Please give me your username")
    else: 
        bot.sendMessage(chat_id, "Please follow the input format DD/MM/YYYY HH:MM") #if invalid

def checkText(text):
    try:
        datetime.strptime(text, input_format)
        return True
    except ValueError:
        return False

def getAccountDetails(chat_id, text):
    if activeUsers[chat_id].state == 2:
        activeUsers[chat_id].username = text
        bot.sendMessage(chat_id, "Please give me your password")
        activeUsers[chat_id].state = 2.1
    elif activeUsers[chat_id].state == 2.1:
        activeUsers[chat_id].password = text
        bot.sendMessage(chat_id, "Which Plan should I bid for?")
        activeUsers[chat_id].state = 2.2
    elif activeUsers[chat_id].state == 2.2:
        if text.isnumeric() and (int(text)<= 3 and int(text)>=1):
            activeUsers[chat_id].plan = text
            bot.sendMessage(chat_id, "Got it. I will notify you when it is done")
            activeUsers[chat_id].state = 3
        else:
            bot.sendMessage(chat_id, "Please input a number from 1 to 3")

def cleanUp(chat_id):
    target_time = activeUsers[chat_id].time
    target_index = timeslots[target_time].index(chat_id)
    del timeslots[target_time][target_index]
    if len(timeslots[target_time]) == 0:
        del timeslots[target_time]
    del activeUsers[chat_id]

def getUsersAtTimeslot(time):
    chat_ids = timeslots[time]
    users = []
    for chat_id in chat_ids:
        users.append(activeUsers[chat_id])
    return chat_ids, users

def finishBid(chat_ids, messages, look_ahead, flags):
    for index in range(len(chat_ids)):
        if not flags[index]:
            bot.sendMessage(chat_ids[index], messages[index][messages[index].find("{")+1:-1])
        else:
            soup = BeautifulSoup(messages[index], 'html.parser').find("div", {"id": "ui_body_container"})
            
            # 1st message
            tr_list = soup.find_all('tr')[2:-1]
            td_list = []
            for el in tr_list:
                td_list.append(str(el.find_all('td')))
            for el in td_list:
                text = el.split('\n')
                new_text = []
                for i in text:
                    if i[0] != "<" and i[-1]!=">":
                        new_text.append(i)
                new_text[0] = "Index: "+new_text[0]+","
                new_text[1] = "Course: "+new_text[1]+","
                new_text[2] = "Title: "+new_text[2]+","
                new_text[3] = "AUs: "+new_text[3]+","
                new_text[4] = "Type: "+new_text[4]+","
                new_text[5] = "Choice: "+new_text[5]+","
                new_text.append(text[-2])
                new_text[6] = "Remark: "+new_text[6]
                bot.sendMessage(chat_ids[index], " ".join(new_text))

            # 2nd message
            last_row = soup.find_all('tr')[-1].text.split("\n")
            new_last_row = []
            for el in last_row:
                if el != '' and el != '\xa0':
                    new_last_row.append(el)
            del last_row
            new_last_row = new_last_row[1:]
            new_last_row[0] = new_last_row[0]+","
            new_last_row[-1] = "Total AUs: "+new_last_row[-1]
            bot.sendMessage(chat_ids[index], " ".join(new_last_row))
        del activeUsers[chat_ids[index]]
    del timeslots[look_ahead]

if __name__ == "__main__":
    bot = telepot.Bot(token)
    MessageLoop(bot, handle).run_as_thread()
    print("Listening ...")

    while 1:
        look_ahead = (datetime.now()+timedelta(seconds=25)).strftime(precise_format) # 25 seconds before target time
        if look_ahead in timeslots:
            chat_ids, users = getUsersAtTimeslot(look_ahead)
            threads = [None]*MAX_USERS
            messages = ["error"]*MAX_USERS
            flags = [None]*MAX_USERS
            for i in range(len(chat_ids)):
                threads[i] = Thread(target=bid(users[i], look_ahead, messages, flags, i))
                threads[i].start()
            finishBid(chat_ids, messages, look_ahead, flags)
            del threads, messages, flags
        time.sleep(0.1)