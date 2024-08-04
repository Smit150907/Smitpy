import pymongo
import schedule
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread

mongo = pymongo.MongoClient("mongodb+srv://dbuserds:akashti@cluster0.zhmedkn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo["BDBOT"]
users = db["users"]

api_id = '29238075'
api_hash = '467eafb86e39b78878937cabfdef6e5d'
bot_token = '6639550663:AAHzLhrLm8O0YGqk3ZNKjzVY34p9D_8biB8'

app = Client("bdbot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.command("start") & filters.private)
def start(client: Client, message: Message):
    user_id = message.from_user.id
    if not users.find_one({"user_id": user_id}):
        users.insert_one({"user_id": user_id})

def send_messages():
    users_list = users.find()
    for user in users_list:
        try:
            inline_keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Recover your looses 🚀", url="https://t.me/FTT21")]]
            )
            app.send_photo(
                user["user_id"],
                photo="https://graph.org/file/27b32c851fa3e88b7313b.jpg",
                caption=("Don’t worry!! 😉\n"
                         "I can recover all of your lifetime losses in just one session only!! 😳📈🚀\n\n"
                         "It may sound suspicious right? But i am serious look we just did three step-compounding 👀🫡\n\n"
                         "Our all VIP members made huge profits from it, they all recovered their losses 🚀📈\n\n"
                         "Do you also want to recover your loss? 🫡\n"
                         "Join now:\n"
                         "https://t.me/FTT21\n"
                         "https://t.me/FTT21\n"
                         "https://t.me/FTT21\n"
                         "https://t.me/FTT21"),
                reply_markup=inline_keyboard
            )
        except Exception as e:
            print(f"Failed to send message to {user['user_id']}: {e}")

def run_scheduler():
    schedule.every(2).hours.do(send_messages)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    Thread(target=run_scheduler).start()
    print("bot is running")
    app.run()
