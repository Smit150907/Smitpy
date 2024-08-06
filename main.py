import asyncio
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from collections import defaultdict, deque
from datetime import datetime, timedelta

# Define your API ID, hash, bot token, and session here
API_ID = 21735369
API_HASH = '5956217627dfa4110078c0441ded3dfd'
BOT_TOKEN = '7445818425:AAEHxcqPeVUJnigEPShUaH7E-BWHxQykFco'
SESSION = '1BVtsOGcBuwiu3OO4aeyjMfgCeIBc6vJ-8q7A9tUm3OJzCzJOwin3VlLT46zQy1Xk7PulDpC5HMjTCespq25vuhpinCzGxuZr5kjUVxnz-fOA2DLXilOV6kdQGUxT-BusMW9eQQFG29fLztI6bxa26lCmcOasTcpQpSy_Fp2q1lvfdz8ge9nKdZqzMbaVEk5KxeooUE7N4G7PnzwkpBa17Em1k1qTlaXhyxXrI3YordgUS4_qsYtpXScFIVNeWCfCyP6RvsKcAhxPHqfhfe24QSWQq1mvSvqwpinX4UEZbhycUEZO4gR76kbFt4EWiqPbHy8WcXy37sY4JKDKEOGifMQMrcivH-U='
GROUP_ID = -1001910731622
TOURNAMENT_CHANNEL_ID = -1002178332188  # Replace with your actual tournament channel ID

# Initialize Telegram clients
app = TelegramClient('bt', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
ass = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# Initialize data structures
verified_traders = {}  # Dictionary to store trader ID and corresponding username
user_invite_links = {}
ongoing_conversations = defaultdict(lambda: None)
trader_check_queue = deque()

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
            if ongoing_conversations[event.sender_id]:
                conv = ongoing_conversations[event.sender_id]
            else:
                async with ass.conversation("QuotexPartnerBot") as conv:
                    ongoing_conversations[event.sender_id] = conv
                    await conv.send_message(trader_id)
                    response = await conv.get_response()

            if ongoing_conversations[event.sender_id]:
                ongoing_conversations[event.sender_id].cancel()  # Close the conversation
                ongoing_conversations[event.sender_id] = None

            response_lines = response.text.split('\n')

            if len(response_lines) > 5 and "ACCOUNT CLOSED" in response_lines[5]:
                await event.reply(
                    "Dear Member,\n\n"
                    "It appears that your account has been deleted. Please create a new account and deposit at least $30.\n\n"
                    "Thank you."
                )
                return
            if "Trader with ID" in response.text and "was not found" in response.text:
                await event.reply(
                    "Dear Member,\n\n"
                    "It appears that your account is not registered using my referral link.\n\n"
                    "Please create your account using the following link:\n\n"
                    "https://qxbroker.com/en/sign-up?lid=825619\n\n"
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
                        # Generate VIP and Tournament invite links
                        invite_link_vip = None
                        invite_link_tournament = None
                        if deposits_sum > 30:
                            invite_link_vip = await app(functions.messages.ExportChatInviteRequest(
                                peer=GROUP_ID,
                                title="VIP Invitation"
                            ))
                            if deposits_sum > 100:
                                invite_link_tournament = await app(functions.messages.ExportChatInviteRequest(
                                    peer=TOURNAMENT_CHANNEL_ID,
                                    title="Tournament Invitation"
                                ))
                        # Construct message
                        message = "Your ID has been successfully verified.\n\n"
                        if invite_link_vip and isinstance(invite_link_vip, types.ChatInviteExported):
                            user_invite_links[invite_link_vip.link] = event.sender_id
                            message += f"Thank you for joining the Positive Trader VIP Group. You are now an official member.\n\n" \
                                       f"Please join us on Telegram: {invite_link_vip.link}\n\n"
                        else:
                            message += "Failed to generate VIP invite link. Please try again later.\n\n"
                        if invite_link_tournament and isinstance(invite_link_tournament, types.ChatInviteExported):
                            user_invite_links[invite_link_tournament.link] = event.sender_id
                            message += f"Congratulations! Since your deposits sum is over $100, you are also invited to our Tournament Channel.\n\n" \
                                       f"Please join us here: {invite_link_tournament.link}\n\n" \
                                       "Enjoy the tournament and happy trading!"
                        elif deposits_sum > 100:
                            message += "Failed to generate Tournament invite link. Please try again later.\n\n"
                        link_message = await event.reply(message)
                        await asyncio.sleep(300)
                        await link_message.delete()
                        # Store trader ID and username
                        verified_traders[trader_id] = event.sender_id
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

async def check_trader_status():
    while True:
        now = datetime.now()
        # Check every 24 hours
        next_run = now + timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())

        for trader_id, user_id in list(verified_traders.items()):
            if user_id in ongoing_conversations:
                conv = ongoing_conversations[user_id]
            else:
                async with ass.conversation("QuotexPartnerBot") as conv:
                    ongoing_conversations[user_id] = conv
                    try:
                        await conv.send_message(trader_id)
                        response = await conv.get_response()

                        # Close the conversation after processing
                        ongoing_conversations[user_id].cancel()  # Close the conversation
                        del ongoing_conversations[user_id]

                        # Process the response
                        response_lines = response.text.split('\n')
                        if len(response_lines) > 5 and "ACCOUNT CLOSED" in response_lines[5]:
                            # Handle the case where the account is closed
                            await handle_account_closed(trader_id, user_id)
                        else:
                            # If no "ACCOUNT CLOSED" message, skip to next trader ID
                            print(f"Trader ID {trader_id} is not closed. Skipping...")
                            continue  # Skip to the next trader ID

                    except Exception as e:
                        print("Error:", e)
                        await app.send_message(user_id, "An error occurred while checking your trader ID status. Please try again later.")
                        if user_id in ongoing_conversations:
                            ongoing_conversations[user_id].cancel()  # Close the conversation if an error occurs
                            del ongoing_conversations[user_id]

async def handle_account_closed(trader_id, user_id):
    # Fetch user from Telegram
    user = await app.get_entity(user_id)
    username = user.username or "Unknown"

    vip_channel_member = False
    tournament_channel_member = False

    try:
        vip_channel_member = await app.get_participant(GROUP_ID, user_id)
    except Exception as e:
        print(f"VIP Channel Check Error: {e}")

    try:
        tournament_channel_member = await app.get_participant(TOURNAMENT_CHANNEL_ID, user_id)
    except Exception as e:
        print(f"Tournament Channel Check Error: {e}")

    # Track if user was kicked
    kicked_from_vip = False
    kicked_from_tournament = False

    if vip_channel_member:
        try:
            await app.kick_participant(GROUP_ID, user_id)
            kicked_from_vip = True
        except Exception as e:
            print(f"Error kicking user from VIP group: {e}")

    if tournament_channel_member:
        try:
            await app.kick_participant(TOURNAMENT_CHANNEL_ID, user_id)
            kicked_from_tournament = True
        except Exception as e:
            print(f"Error kicking user from Tournament channel: {e}")

    # Remove trader ID from verified_traders only if user was kicked from at least one channel
    if kicked_from_vip or kicked_from_tournament:
        if trader_id in verified_traders:
            del verified_traders[trader_id]

        # Inform user about account closure
        message = f"Dear {username},\n\nYour account with trader ID {trader_id} has been closed. Unfortunately, you are no longer eligible for VIP and Tournament access.\n\n"
        if kicked_from_vip:
            message += "You have been removed from the VIP group.\n"
        if kicked_from_tournament:
            message += "You have been removed from the Tournament Channel.\n"

        try:
            await app.send_message(user_id, message)
        except Exception as e:
            print(f"Error sending message to user {user_id}: {e}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(check_trader_status())
    ass.start()
    print("Assistant bot is running...")
