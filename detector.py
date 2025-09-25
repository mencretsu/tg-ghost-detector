from telethon import TelegramClient, events, Button
from telethon.tl.types import User, Channel
from telethon.errors import ChatAdminRequiredError
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import pytz

# Setup logging
logging.basicConfig( 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

API_ID = os.getenv('API_ID_SPECTER')
API_HASH = os.getenv('API_HASH_SPECTER')
BOT_TOKEN = os.getenv('BOT_TOKEN_SPECTER')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))  # Admin Telegram ID
BOT_SESSION_DIR = os.getenv('BOT_SESSION_DIR', 'botsessions')
BOT_SESSION_NAME = os.getenv('BOT_SESSION_NAME', 'specterhunter')

# Initialize bot
bot = TelegramClient(
    os.path.join(BOT_SESSION_DIR, BOT_SESSION_NAME),
    API_ID,
    API_HASH
).start(bot_token=BOT_TOKEN)

def get_current_time():
    """Get current UTC time"""
    return datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")

async def send_new_user_alert(sender):
    """Send alert when new user starts the bot"""
    if ADMIN_ID:
        try:
            alert_message = (
                f"🎉 New User Alert!\n\n"
                f"Name: {sender.first_name}\n"
                f"Username: @{sender.username or 'No username'}\n"
                f"ID: {sender.id}\n"
                f"Time: {get_current_time()} UTC"
            )
            await bot.send_message(ADMIN_ID, alert_message)
        except Exception as e:
            logger.error(f"Failed to send new user alert: {str(e)}")

async def scan_frozen(event):
    """Scan for deleted accounts in a group"""
    try:
        chat = await event.get_chat()
        if not isinstance(chat, (Channel)):
            await event.respond("❌ This command only works in groups/channels!")
            return

        group_name = chat.title or "this group"
        msg = await event.respond("☠️ Scanning for ghost accounts...")

        # Check bot permissions
        bot_member = await bot.get_permissions(chat, 'me')
        if not bot_member.is_admin:
            await msg.edit("❌ I need to be an admin to scan for ghosts!")
            return

        frozen = active = 0

        async for member in bot.iter_participants(chat):
            if isinstance(member, User):
                if member.deleted:
                    frozen += 1
                else:
                    active += 1

        total = frozen + active
        ratio = (frozen / total * 100) if total > 0 else 0

        buttons = [Button.inline("🔥 Remove Ghosts", b"remove_ghosts")] if frozen > 0 else None
        
        scan_results = (
            f"📊 **Scan Result** for **{group_name}**\n\n"
            f"📦 Total members: {total}\n"
            f"👻 Ghosts: {frozen}\n"
            f"🧍‍♂️ Active users: {active}\n"
            f"💀 Ghost Ratio: {ratio:.1f}%\n\n"
        )

        if frozen > 0:
            scan_results += "🔥 Click below to remove ghost accounts from this group?"
        else:
            scan_results += "👏 Looks clean. No ghost to banish. 🧹"

        await msg.edit(scan_results, buttons=buttons)

    except Exception as e:
        logger.error(f"Error in scan_frozen: {str(e)}")
        await event.respond("⚠️ Error while scanning. Make sure I have proper admin rights.")

@bot.on(events.NewMessage(pattern='^/start$'))
async def start_command(event):
    """Handle /start command"""
    if event.is_private:
        # Send alert for new user
        await send_new_user_alert(await event.get_sender())
        
        bot_me = await bot.get_me()
        await event.respond(
            "🧟‍♂️ **Specter Hunter Bot**\n\n"
            "This bot sniffs out dead accounts (aka ghost users) haunting your Telegram groups "
            "and helps you purge 'em like a digital exorcist. 🔥\n\n"
            "I can't haunt ghosts in your DMs. Add me to a group and make me admin, then run `/scanmembers`.\n",
            buttons=[
                Button.url("➕ Add me to your group", f"https://t.me/{bot_me.username}?startgroup=true")
            ]
        )

@bot.on(events.NewMessage(pattern=r'^/scanmembers(?:@\w+)?$'))
async def scan_command(event):
    """Handle /scanmembers command"""
    try:
        await send_new_user_alert(await event.get_sender())
        if event.is_private:
            bot_me = await bot.get_me()
            return await event.respond(
                "🚫 This command only works in groups, not in DMs.",
                buttons=[
                    Button.url("➕ Add me to your group", f"https://t.me/{bot_me.username}?startgroup=true")
                ]
            )

        # Check if bot is admin
        chat = await event.get_chat()
        bot_member = await bot.get_permissions(chat, 'me')
        if not bot_member.is_admin:
            return await event.respond("❌ I need to be an admin to work properly!")

        # Check if sender is admin
        sender = await event.get_sender()
        try:
            participant = await bot.get_permissions(chat, sender.id)
            if not participant.is_admin:
                return await event.respond("🛑 Only group admins can use this command.")
        except ChatAdminRequiredError:
            return await event.respond("❌ I need to be an admin to check permissions!")

        await scan_frozen(event)

    except Exception as e:
        logger.error(f"Error in scan_command: {str(e)}")
        await event.respond("⚠️ An error occurred. Make sure I'm an admin in this group.")

@bot.on(events.CallbackQuery(data=b'remove_ghosts'))
async def confirm_remove_ghosts(event):
    """Handle ghost removal confirmation"""
    await event.edit(
        "⚔️ One last step. Send ghost accounts straight to hell?",
        buttons=[
            [Button.inline("✅ Yes, do it", b"confirm_remove")],
            [Button.inline("❌ Nah, chill", b"cancel_remove")]
        ]
    )

@bot.on(events.CallbackQuery(data=b'confirm_remove'))
async def do_remove_ghosts(event):
    """Execute ghost removal"""
    try:
        await event.edit("⏳__Cleaning up... Hang tight, this might take a sec.__")
        chat = await event.get_chat()
        deleted = 0

        async for member in bot.iter_participants(chat):
            if isinstance(member, User) and member.deleted:
                try:
                    await bot.kick_participant(chat, member.id)
                    deleted += 1
                except Exception as e:
                    logger.error(f"Failed to remove member {member.id}: {str(e)}")

        await event.edit(
            f"🔥 Mission complete. **{deleted}** ghost(s) were banished to the afterlife.\n"
            "Use /scanmembers anytime to scan again."
        )
    except Exception as e:
        logger.error(f"Error in do_remove_ghosts: {str(e)}")
        await event.edit("❌ Failed to remove ghosts. Make sure I have proper admin rights.")

@bot.on(events.CallbackQuery(data=b'cancel_remove'))
async def cancel_remove_ghosts(event):
    """Handle cancellation of ghost removal"""
    await event.edit(
        "👍 Got it. Ghosts live to haunt another day.\n"
        "Use /scanmembers if you change your mind."
    )

def main():
    """Main function to run the bot"""
    try:
        logger.info("Bot started...")
        bot.run_until_disconnected()
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")

if __name__ == '__main__':
    main()
