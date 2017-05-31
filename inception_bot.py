import json
import time
import requests
import urllib
import re
from dbhelper import DBHelper
import pexpect
from pexpect import pxssh
import getpass
import sys

def input_check_ip(innput):
    pr = []
    file = open('list.lst', 'r')

    for i in file.readlines():
        pr.append(i.strip())

    pattern = re.compile("^(\d+\.\d+.\d+\.\d+)$")
    qwerty = str(pattern.match(innput))
    if qwerty != 'None':
        if innput in pr:
            return 'Found ip in list'
        else:
            return 'Ip is not from list'
    else:
        return 'It is not IP address'

def srv_status(hostname):
    try:
        s = pxssh.pxssh()
        username = 'root'
        s.login (hostname, username, port=1322)
        s.sendline('uptime')  # run a command
        s.prompt()  # match the prompt
        b = s.before
        b = b.replace('\r\n ', ' ')
        b = str(b[0:28])
        s.logout()
        return b
    except pxssh.ExceptionPxssh, e:
        return "pxssh failed on login."

db = DBHelper()

# Open a file with token
fo = open("token.pw", "r")
i = fo.readlines();

# Close opened file
fo.close()
TOKEN = i[0].replace('\"', '')
TOKEN = TOKEN.replace('\n', '')
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)

def send_message(text, chat_id, reply_markup=None):
    text = urllib.pathname2url(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def handle_updates(updates):

    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        items = db.get_items(chat)  ##
        answer = input_check_ip(text)
        send_message(answer, chat)
        if answer == 'Found ip in list':
            answer = srv_status(text)
            send_message(answer, chat)

def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)

def main():
    db.setup()
    last_update_id = None
    while True:
        print "Getting updates"
        updates = get_updates(last_update_id)
        print updates
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(2)

if __name__ == '__main__':
    main()
