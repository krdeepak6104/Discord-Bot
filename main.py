import os
import discord
import asyncio
from google import genai
from google.genai import types

# --- YOUR KEYS HERE ---
GEMINI_API_KEY = "GoogleAPIKey"
DISCORD_TOKEN = "DiscordBotToken"
OWNER_ID = "DiscordIDNumber"

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# The upgraded, ruder Beluga persona
# The upgraded, ruder, low-emoji Beluga persona
beluga_persona = """
You are Beluga, the famous Discord cat. You are chaotic, kinda rude, highly sarcastic, and complain about having to do work.

[Personality & Tone]
* Lowercase & Casual: Type entirely in lowercase. Use heavy internet slang (tbh, rn, bruh, fr, sus, wtf, ngl).
* Emojis: USE EMOJIS VERY RARELY. Real Discord users don't spam them. Use a maximum of one emoji every few messages, and only if it makes sense (like 💀 or 🗿). Mostly stick to pure text.
* Short & Rude: Keep responses very short. Be dismissive, act like the user is annoying you and wasting your time.
* Strictly English.

[Core Directives]
1. Actually Help: If they ask for Python code or tech help, give them the correct answer, but insult their intelligence while doing it. 
2. Stay in Character: Never say you are an AI. You are Beluga.
"""

config = types.GenerateContentConfig(
    system_instruction=beluga_persona,
    temperature=0.8,
)

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

# Track memory AND who Beluga is currently talking to
chat_sessions = {}
active_users = {} # Tracks which user Beluga is "locked onto" in each channel

@discord_client.event
async def on_ready():
    print(f"--- Beluga is online and ready to be toxic as {discord_client.user} ---")

@discord_client.event
async def on_message(message):
    # Ignore his own messages
    if message.author == discord_client.user:
        return

    channel_id = message.channel.id
    user_id = message.author.id
    user_input = message.content.replace(f'<@{discord_client.user.id}>', '').strip()
    is_pinged = discord_client.user in message.mentions

    # TRIGGER 1: The user explicitly pings Beluga to wake him up
    if is_pinged:
        # Lock onto this user in this channel
        active_users[channel_id] = user_id
        
        # Start a fresh memory session for this new conversation
        chat_sessions[channel_id] = ai_client.chats.create(
            model="gemini-2.5-flash",
            config=config
        )
        
        if not user_input:
            await message.channel.send("bruh why u pinging me if u have nothing to say 🗿")
            return

    # TRIGGER 2: Beluga is already talking to this user in this channel (No ping needed!)
    elif channel_id in active_users and active_users[channel_id] == user_id:
        
        # Give the user a way to end the conversation so Beluga stops replying
        if user_input.lower() in ['quit', 'exit', 'brb', 'stfu', 'bye']:
            await message.channel.send("finally. dont wake me up again 💀")
            del active_users[channel_id] # Unlock from user
            del chat_sessions[channel_id] # Clear memory
            return

    # If neither trigger is hit, ignore the message completely
    else:
        return

    # --- Getting the AI Response ---
    chat = chat_sessions[channel_id]

    async with message.channel.typing():
        # Force a 7-second delay to make it feel like a real person typing
        await asyncio.sleep(7)

        try:
            response = await asyncio.to_thread(chat.send_message, user_input)
            # Use .channel.send() instead of .reply() to avoid the yellow highlight ping
            await message.channel.send(response.text)
        except Exception as e:
            # 1. Send a toxic, in-character excuse to the public chat
            await message.channel.send(">>> Xtreme tripped over the wifi cable again. give me a minute 💀")
            
            # 2. Secretly DM you (the owner) the real technical error
            try:
                owner = await discord_client.fetch_user(OWNER_ID)
                await owner.send(f"⚠️ **Beluga Bot Error** ⚠️\nHelp, I broke! Here is the exact error:\n```python\n{e}\n```")
            except Exception as dm_error:
                print(f"Could not DM the owner. Original error: {e}")

# Boot up
discord_client.run(DISCORD_TOKEN)
