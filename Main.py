import asyncio
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from datetime import datetime, timedelta

API_ID = 27034173
API_HASH = 'db451b0d92014f80c6ab13289d88fb27'
BOT_TOKEN = '7213690750:AAFOiAns7LJG3kHHApyl-lbpBIosgueXmCg'
SESSION = '1BVtsOGcBu5dC9JXtA5MZFqG2d6VURod1_wJLPgTJb5FabGVMSGxgHf_L04XW0XCy14h5A0aO4dPmVRj9v6VJBciAgPR4cai1Y73VHBUOAMnFHD_hZ722ynWmbM_17QzveIckVwbDqnvr5WPOx8uaWPyBXyH5W5In7cWW6CiHn-HBplHbRL_kTDG0FC1G-umAEDytmFbkI7IJmLpzs1liDnmzNTPtGK-CJib6X5-eKgDxjHdJfvTe2R_4S_bbk1Dj0Bx1DAaEAMsCElM_ZPSpWvja2I1ls5ykrsbBFqsMv94DITCAx1ljF94YvEgQ7dZvZXNlCcewxI5OO65zLUGLpdFBr8r8G10=‘
GROUP_ID = -1002132674838

app = TelegramClient('bt', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
ass = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
verified_traders = set()
user_invite_links = {}

@app.on(events.NewMessage(pattern='/start'))
async def start(event):
    user = await event.get_sender()
    full_name = user.first_name
    if user.last_name:
        full_name += f" {user.last_name}"
    welcome_message = (
        f"Welcome {full_name} to FTT Auto-Verify Trader ID Bot! "
        "Please enter your trader ID here (only numbers). After successful verification, "
        "we will add you to our VIP group!"
    )
    await event.reply(welcome_message)

@app.on(events.NewMessage)
async def handle_message(event):
    if event.is_private and not event.message.message.startswith('/'):
        trader_id = event.message.message
        if not trader_id.isdigit():
            await event.reply("Not a Valid ID, Please enter numbers only")
            return
        if len(trader_id) != 8:
            await event.reply("Trader ID only consists of 8 numbers!! ✅")
            return
        if trader_id in verified_traders:
            await event.reply("This trader ID has already been verified by another user, one trader ID only one time verification.")
            return
        try:
            async with ass.conversation("QuotexPartnerBot") as conv:
                await conv.send_message(trader_id)
                response = await conv.get_response()

                if "Trader with ID" in response.text and "was not found" in response.text:
                    await event.reply(
                        "Dear Member,\n\n"
                        "It appears that your account is not registered using my referral link.❌\n\n"
                        "Please create your account using the appropriate link below:👇\n\n"
                        "- **For worldwide members:** https://broker-qx.pro/sign-up/?lid=292132\n"
                        "- **For Bangladesh members:** https://market-qx.pro/sign-up/?lid=292132\n\n"
                        "After creating your account, please deposit minimum 50$ and type your trader ID. 🏆💰\n\n"
                        "Thank you."
                    )
                elif "Trader #" in response.text:
                    balance_line = next(line for line in response.text.split('\n') if "Balance:" in line)
                    balance_str = balance_line.split("$")[1].strip().replace('**', '').strip()
                    balance = float(balance_str)

                    if balance >= 50:
                        verified_traders.add(trader_id)

                        # Create a unique invite link for the user
                        invite_link = await app(functions.messages.ExportChatInviteRequest(
                            peer=GROUP_ID,
                            title="VIP Invitation"
                        ))
                        if isinstance(invite_link, types.ChatInviteExported):
                            user_invite_links[invite_link.link] = event.sender_id
                            link_message = await event.reply(
                                "Your ID has been successfully verified.✅\n\n"
                                "Thank you for choosing the FTT VIP Group. You are now an official member.\n\n"
                                f"Please join us on Telegram: {invite_link.link}\n\n"
                                "We look forward to your participation. Happy trading 🤩💰"
                            )
                            await asyncio.sleep(300)
                            await link_message.delete()
                        else:
                            await event.reply("Failed to generate invite link. Please try again later.")
                    else:
                        await event.reply(
                            "Your balance is less than 50$, please deposit at least 50$ or more to join our VIP."
                        )
                else:
                    await event.reply("Not a valid ID ?")

        except Exception as e:
            print("Error:", e)
            await event.reply("An error occurred while processing your request. Please try again later.")

@app.on(events.ChatAction)
async def handler(event):
    if event.user_joined or event.user_added:
        user_id = event.user_id
        for invite_link, stored_user_id in user_invite_links.items():
            if stored_user_id == user_id:
                try:
                    await app(functions.messages.EditExportedChatInviteRequest(
                        peer=GROUP_ID,
                        link=invite_link,
                        revoked=True
                    ))
                    del user_invite_links[invite_link]
                    break
                except Exception as e:
                    print(f"Error revoking invite link: {e}")

if __name__ == '__main__':
    ass.start()
    print("Bot is running...")
    app.run_until_disconnected()
