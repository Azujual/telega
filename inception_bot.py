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


def srv_status(hostname):
    try:
        s = pxssh.pxssh()
        username = 'root'
        s.login (hostname, username, port=1322)
        s.sendline ('uptime')   # run a command
        s.prompt()             # match the prompt
        print s.before          # print everything before the prompt.
        s.sendline ('ps auxww | grep -i 3proxy | grep -v grep | grep -v srati |wc -l')
        s.prompt()
        print s.before
        s.logout()
    except pxssh.ExceptionPxssh, e:
        print "pxssh failed on login."
        print str(e)

def getMicb():
    selector = '<div id="currancy-rates">'
    response = urllib.urlopen('http://www.micb.md/')
    html = response.read()

    html = html.replace('\r','')
    html = html.replace('\n', '')
    html = html.replace(' ', '')
    html = re.sub(r'^.*currancy-rates', 'currancy-rates', html)
    html = re.sub(r'</div>.*$', 'currancy-ratesEND', html)
    html = html.replace('\t', '')
    html = re.sub(r'</table>.*$', '</table>', html)
    html = html.replace('</span></td></tr>', '\n')
    html = re.sub(r'^.*USD', 'USD', html)
    html = html.replace('</td><td>&mdash;</td><td>&mdash;</td><tdclass="dec"><span>', ' = ')
    html = html.replace('</td><td>&mdash;</td><td>&mdash;</td><td><span>', ' = ')
    html = html.replace('<tr><tdclass="currancy">', '')
    html = html.replace('</tbody></table>', '')
    return html

db = DBHelper()

# Open a file with token
fo = open("token.pw", "r")
i = fo.readlines();

# Close opend file
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
"""
def send_message(text, chat_id):
    text = urllib.pathname2url(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)
"""
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

"""
def echo_all(updates):
    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        send_message(text, chat)
"""
"""
def handle_updates(updates):
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            items = db.get_items()
            if text in items:
                db.delete_item(text)
                items = db.get_items()
            else:
                db.add_item(text)
                items = db.get_items()
            message = "\n".join(items)
            send_message(message, chat)
        except KeyError:
            pass
"""
"""
def handle_updates(updates):
    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        items = db.get_items()
        if text == "/done":
            keyboard = build_keyboard(items)
            send_message("Select an item to delete", chat, keyboard)
        elif text in items:
            db.delete_item(text)
            items = db.get_items()
            keyboard = build_keyboard(items)
            send_message("Select an item to delete", chat, keyboard)
        else:
            db.add_item(text)
            items = db.get_items()
            message = "\n".join(items)
            send_message(message, chat)
"""
def handle_updates(updates):
    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        items = db.get_items(chat)  ##
        pattern = re.compile("^[0-9]{1-3}\.[0-9]{1-3}\.[0-9]{1-3}")
        if text == "/done":
            keyboard = build_keyboard(items)
            send_message("Select an item to delete", chat, keyboard)
        elif text == '191.96.4.215':
            send_message("Wait a sec...", chat)
            response = srv_status(text)
            send_message(response, chat)
        elif text == "micb":
            send_message(getMicb(), chat)
        elif text == "/start":
            send_message(
                "Welcome to your personal To Do list. Send any text to me and I'll store it as an item. Send /done to remove items",
                chat)
        elif text.startswith("/"):
            continue
        elif text in items:
            db.delete_item(text, chat)  ##
            items = db.get_items(chat)  ##
            keyboard = build_keyboard(items)
            send_message("Select an item to delete", chat, keyboard)
        else:
            db.add_item(text, chat)  ##
            items = db.get_items(chat)  ##
            message = "\n".join(items)
            send_message(message, chat)

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
