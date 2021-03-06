import time
from Config import Config
from pyrogram import Client as app
import sql_helpers.forceSubscribe_sql as sql
from pyrogram import Filters, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, UsernameNotOccupied, ChatAdminRequired, PeerIdInvalid


@app.on_callback_query(Filters.regex("^onButtonPress$"))
def onButtonPress(client, cb):
  user_id = cb.from_user.id
  chat_id = cb.message.chat.id
  cws = sql.fs_settings(chat_id)
  if cws:
    channel = cws.channel
    if client.get_chat_member(chat_id, user_id).restricted_by.id == (client.get_me()).id:
      try:
        client.get_chat_member(channel, user_id)
        client.unban_chat_member(chat_id, user_id)
      except UserNotParticipant:
        client.answer_callback_query(cb.id, text="Join the channel and press the button again.")
    else:
      client.answer_callback_query(cb.id, text="You are muted by admins for other reasons.", show_alert=True)


@app.on_message(Filters.text & ~Filters.private & ~Filters.edited, group=1)
def SendMsg(client, message):
  cws = sql.fs_settings(message.chat.id)
  if cws:
    user_id = message.from_user.id
    if not client.get_chat_member(message.chat.id, user_id).status in ("administrator", "creator") and not user_id in Config.SUDO_USERS:
      first_name = message.from_user.first_name
      channel = cws.channel
      try:
        client.get_chat_member(channel, user_id)
      except UserNotParticipant:
        try:
          sent_message = message.reply_text(
              "[{}](tg://user?id={}), you are **not subscribed** to my [channel](https://t.me/{}) yet. Please [join](https://t.me/{}) and **press the button below** to unmute yourself.".format(first_name, user_id, channel, channel),
              disable_web_page_preview=True,
              reply_markup=InlineKeyboardMarkup(
                  [[InlineKeyboardButton("UnMute Me", callback_data="onButtonPress")]]
              )
          )
          client.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=False))
        except ChatAdminRequired:
          sent_message.edit("❗ **I am not an admin in here.**\n__Make me admin with ban user permission or turn off ForceSubscribe.__")
      except ChatAdminRequired:
        client.send_message(message.chat.id, text=f"❗ **I am not an admin in @{channel}**\n__Make me admin in the channel or turn of ForceSubscribe.__")


@app.on_message(Filters.command(["forcesubscribe", "fsub"]) & ~Filters.private)
def config(client, message):
  user = client.get_chat_member(message.chat.id, message.from_user.id)
  if user.status is "creator" or user.user.id in Config.SUDO_USERS:
    chat_id = message.chat.id
    if len(message.command) > 1:
      input_str = message.command[1]
      input_str = input_str.replace("@", "")
      if input_str.lower() in ("off", "no", "disable"):
        sql.disapprove(chat_id)
        message.reply_text("❌ **Force Subscribe is Disabled Successfully.**")
      elif input_str.lower() in ('clear'):
        sent_message = message.reply_text('**Unmuting all members who is muted by me...**')
        try:
          for chat_member in client.get_chat_members(message.chat.id, filter="restricted"):
            if chat_member.restricted_by.id == (client.get_me()).id:
                client.unban_chat_member(chat_id, chat_member.user.id)
                time.sleep(1)
          sent_message.edit('✅ **UnMuted all members which are muted by me.**')
        except ChatAdminRequired:
          sent_message.edit('❗ **I am not an admin in this chat.**\n__I can\'t unmute members because i am not an admin in this chat make me.__')
      else:
        try:
          client.get_chat_member(input_str, "me")
          sql.add_channel(chat_id, input_str)
          message.reply_text(f"✅ **Force Subscribe is Enabled**\n__Force Subscribe is enabled, all the group members have to subscribe this [channel](https://t.me/{input_str}) in order to send messages in this group.__", disable_web_page_preview=True)
        except UserNotParticipant:
          message.reply_text(f"❗ **Not an Admin in the Channel**\n__I am not an admin in the [channel](https://t.me/{input_str}). Add me as a admin in order to enable ForceSubscribe.__", disable_web_page_preview=True)
        except (UsernameNotOccupied, PeerIdInvalid):
          message.reply_text(f"❗ **Invalid Channel Username.**")
        except Exception as err:
          message.reply_text(f"❗ **ERROR:** ```{err}```")
    else:
      if sql.fs_settings(chat_id):
        message.reply_text(f"✅ **Force Subscribe is enabled in this chat.**\n__For this [Channel](https://t.me/{sql.fs_settings(chat_id).channel})__", disable_web_page_preview=True)
      else:
        message.reply_text("❌ **Force Subscribe is disabled in this chat.**")
  else:
      message.reply_text("❗ **Group Creator Required**\n__You have to be the group creator to do that.__")