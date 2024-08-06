import asyncio
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from collections import defaultdict

# Define your API ID, hash, bot token, and session here
API_ID = 21735369
API_HASH = '5956217627dfa4110078c0441ded3dfd'
BOT_TOKEN = '7445818425:AAEHxcqPeVUJnigEPShUaH7E-BWHxQykFco'
SESSION = '1BVtsOGcBuwiu3OO4aeyjMfgCeIBc6vJ-8q7A9tUm3OJzCzJOwin3VlLT46zQy1Xk7PulDpC5HMjTCespq25vuhpinCzGxuZr5kjUVxnz-fOA2DLXilOV6kdQGUxT-BusMW9eQQFG29fLztI6bxa26lCmcOasTcpQpSy_Fp2q1lvfdz8ge9nKdZqzMbaVEk5KxeooUE7N4G7PnzwkpBa17Em1k1qTlaXhyxXrI3YordgUS4_qsYtpXScFIVNeWCfCyP6RvsKcAhxPHqfhfe24QSWQq1mvSvqwpinX4UEZbhycUEZO4gR76kbFt4EWiqPbHy8WcXy37sY4JKDKEOGifMQMrcivH-U='
GROUP_ID = -1002170963386
TOURNAMENT_CHANNEL_ID = -1002239768493  # Replace with your actual tournament channel ID

# Initialize Telegram clients
app = TelegramClient('bt', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
ass = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# Initialize data structures
verified_traders = set()
user_invite_links = {}
ongoing_conversations = defaultdict(lambda: None)

@app.on(events.NewMessage(pattern='/start'))
async def start(event):
    user = await event.get_sender()
    full_name = user.first_name
    if user.last_name:
        full_name += f" {user.last_name}"
    welcome_message = (
        f"Welcome {full_name} to Positive Trader Auto-Verify Bot! "
        "Please enter your trader ID here (only numbers). After successful verification, "
        "we will add you to our VIP group!"
    )
    await event.reply(welcome_message)

@app.on(events.NewMessage)
async def handle_message(event):
    if event.is_private and not event.message.message.startswith('/'):
        trader_id = event.message.message
        if not trader_id.isdigit():
            await event.reply("Not a valid ID. Please enter numbers only.")
            return
        if len(trader_id) != 8:
            await event.reply("Trader ID must consist of 8 numbers.")
            return
        if trader_id in verified_traders:
            await event.reply("This trader ID has already been verified by another user. Each trader ID can only be verified once.")
            return

        try:
            # Check if there's an ongoing conversation for the user
            if ongoing_conversations[event.sender_id]:
                conv = ongoing_conversations[event.sender_id]
            else:
                async with ass.conversation("QuotexPartnerBot") as conv:
                    ongoing_conversations[event.sender_id] = conv
                    await conv.send_message(trader_id)
                    response = await conv.get_response()

            # Close the conversation after processing
            if ongoing_conversations[event.sender_id]:
                ongoing_conversations[event.sender_id].cancel()  # Close the conversation
                ongoing_conversations[event.sender_id] = None

            # Debugging: Print response text
            print("Response from QuotexPartnerBot:", response.text)

            if "Trader with ID" in response.text and "was not found" in response.text:
                await event.reply(
                    "Dear Member,\n\n"
                    "It appears that your account is not registered using my referral link.\n\n"
                    "Please create your account using the appropriate link below:\n\n"
                    "- For worldwide members: https://broker-qx.pro/sign-up/?lid=292132\n"
                    "- For Bangladesh members: https://market-qx.pro/sign-up/?lid=292132\n\n"
                    "After creating your account, please deposit a minimum of $50 and type your trader ID.\n\n"
                    "Thank you."
                )
            elif "Trader #" in response.text:
                deposits_sum_line = [line for line in response.text.split('\n') if line.startswith("Deposits Sum:")]
                if deposits_sum_line:
                    deposits_sum_line = deposits_sum_line[0]
                    if "$" in deposits_sum_line:
                        deposits_sum_str = deposits_sum_line.split("$")[1].strip()
                        deposits_sum_str = ''.join(c for c in deposits_sum_str if c.isdigit() or c == '.')
                        try:
                            deposits_sum = float(deposits_sum_str)
                        except ValueError:
                            await event.reply("Error parsing deposits sum. Please try again later.")
                            return
                        if deposits_sum > 50:
                            verified_traders.add(trader_id)

                            # Invite to VIP group
                            invite_link_vip = await app(functions.messages.ExportChatInviteRequest(
                                peer=GROUP_ID,
                                title="VIP Invitation"
                            ))
                            if isinstance(invite_link_vip, types.ChatInviteExported):
                                user_invite_links[invite_link_vip.link] = event.sender_id
                                link_message = await event.reply(
                                    "Your ID has been successfully verified.\n\n"
                                    "Thank you for joining the Positive Trader VIP Group. You are now an official member.\n\n"
                                    f"Please join us on Telegram: {invite_link_vip.link}\n\n"
                                    "We look forward to your participation. Happy trading!"
                                )
                                await asyncio.sleep(300)
                                await link_message.delete()
                            else:
                                await event.reply("Failed to generate VIP invite link. Please try again later.")

                        if deposits_sum > 100:
                            # Invite to Tournament channel
                            invite_link_tournament = await app(functions.messages.ExportChatInviteRequest(
                                peer=TOURNAMENT_CHANNEL_ID,
                                title="Tournament Invitation"
                            ))
                            if isinstance(invite_link_tournament, types.ChatInviteExported):
                                user_invite_links[invite_link_tournament.link] = event.sender_id
                                link_message = await event.reply(
                                    "Congratulations! Since your deposits sum is over $100, you are also invited to our Tournament Channel.\n\n"
                                    f"Please join us here: {invite_link_tournament.link}\n\n"
                                    "Enjoy the tournament and happy trading!"
                                )
                                await asyncio.sleep(300)
                                await link_message.delete()
                            else:
                                await event.reply("Failed to generate Tournament invite link. Please try again later.")
                    else:
                        await event.reply("Deposits sum information is not in the expected format.")
                else:
                    await event.reply("No deposits sum information found in the response.")
        except Exception as e:
            print("Error:", e)
            await event.reply("An error occurred while processing your request. Please try again later.")

@app.on(events.ChatAction)
async def handle_chat_action(event):
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
    print("Assistant bot is running...")
    app.run_until_disconnected()
