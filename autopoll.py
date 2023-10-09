import discord
from discord import app_commands, ui
import os
import json
import time
from enum import IntEnum
import re
import pickle
from setproctitle import setproctitle

setproctitle("autopoll")

TOKEN_FILE = "TOKEN"
CANDIDATES_FILE = "candidates.pkl"
emoji_list = [
  '🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯', '🇰', '🇱', '🇲', '🇳', '🇴', '🇵', '🇶', '🇷', '🇸', '🇹', '🇺', '🇻', '🇼', '🇽', '🇾', '🇿'
]

def getChannelCandidates(guild_id: str, channel_id : str):
  # Get candidates for server
  if not guild_id in candidates:
    candidates[guild_id] = {}
  guild_candidates = candidates[guild_id]

  # Get candidates for channel
  if not channel_id in guild_candidates:
    guild_candidates[channel_id] = {}
  return guild_candidates[channel_id]

def updateCandidates(guild_id : str, channel_id : str, name : str, weight : str, description : str):
  channel_candidates = getChannelCandidates(guild_id, channel_id)
  if name in channel_candidates:
    return False

  game_info = {"weight": weight, "description": description}
  channel_candidates[name]=game_info
  saveCandidates()
  return True

def saveCandidates():
  with open(CANDIDATES_FILE, 'wb') as f:
    pickle.dump(candidates, f)

class AddCandidateModal(ui.Modal, title='候補の登録'):
  name = ui.TextInput(label='ゲーム名')
  weight = ui.TextInput(label='ゲームの重さ(軽量級:L, 中量級:M, 重量級:H)', max_length=1, min_length=1)
  # weight = ui.select(cls=discord.ui.Select, options=weight_options)
  description = ui.TextInput(label='簡単なゲーム説明(投票時に一緒に表示されます。)')

  weight_transform_dict = {'L':'(軽)', 'M':"(中)", 'H':"(重)"}
  async def on_submit(self, interaction: discord.Interaction):
    # Check format of weight.
    pattern = r'[LMH]'
    if re.fullmatch(pattern, self.weight.value) == None:
      await interaction.response.send_message('ゲームの重さが不適です。', ephemeral=True)
      return

    guild_id = str(interaction.guild_id) 
    channel_id = str(interaction.channel.id) 
    result = updateCandidates(guild_id, channel_id, self.name.value, self.weight_transform_dict[self.weight.value], self.description.value)
    if result:
      mes = self.name.value + "が候補に登録されました。"
      ephemeral = False
    else:
      mes = self.name.value + "は既に登録済みです。"
      ephemeral = True
    await interaction.response.send_message(mes, ephemeral=ephemeral)

# Load token.
with open(TOKEN_FILE) as f:
  TOKEN = f.read()

# Create instance.
intents = discord.Intents(message_content=True)
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Load candidates.
if os.path.isfile(CANDIDATES_FILE):
  with open (CANDIDATES_FILE, mode="rb") as f:
    candidates = pickle.load(f)
else:
  candidates = {}

@client.event
async def on_ready():
  print('ログインしました')
  for guild in client.guilds:
    print(guild.name, ":", guild.id)
  await tree.sync()

@tree.command(name="add_candidate", description="候補の登録")
async def add_candidate(interaction: discord.Interaction):
  modal = AddCandidateModal()
  await interaction.response.send_modal(modal)

def createPollEmb(title:str, guild_id: str, channel_id):
  # guild_candidates = candidates[guild_id]
  channel_candidates = getChannelCandidates(guild_id, channel_id)
  desc = ""
  for i, game in enumerate(channel_candidates):
    info = ""
    info += emoji_list[i] + " `" + str(i) + " : "
    info += channel_candidates[game]["weight"] + " "
    info += game + " : "
    info += channel_candidates[game]["description"] + '`\n'
    desc += info
  return discord.Embed(title= title, description=desc)

@tree.command(name="create_poll", description="投票フォームの作成")
async def create_poll(interaction: discord.Interaction, poll_title: str):
  # guild_candidates = candidates[str(interaction.guild_id)]
  guild_id = str(interaction.guild_id)
  channel_id = str(interaction.channel.id)
  channel_candidates = getChannelCandidates(guild_id, channel_id)

  if len(channel_candidates) == 0:
    await interaction.response.send_message("候補が登録されていません。", ephemeral=True)
    return
  await interaction.response.send_message(embed=createPollEmb(poll_title, guild_id, channel_id))
  async for message in interaction.channel.history(limit=1):
    for i in range(len(channel_candidates)):
      await message.add_reaction(emoji_list[i])

@tree.command(name="show_candidates", description="候補の表示")
async def show_candidates(interaction: discord.Interaction):
  # guild_candidates = candidates[guild_id]
  guild_id = str(interaction.guild_id)
  channel_id = str(interaction.channel.id)
  channel_candidates = getChannelCandidates(guild_id, channel_id)
  if len(channel_candidates) == 0:
    await interaction.response.send_message("候補が登録されていません。", ephemeral=True)
    return
  await interaction.response.send_message(embed=createPollEmb("次回のゲーム候補一覧", guild_id, channel_id), ephemeral=True)
  
@tree.command(name="remove_candidate", description="候補の削除")
async def remove_candidate(interaction: discord.Interaction, id:int):
  # guild_candidates = candidates[str(interaction.guild_id)]
  guild_id = str(interaction.guild_id)
  channel_id = str(interaction.channel.id)
  channel_candidates = getChannelCandidates(guild_id, channel_id)

  if id < 0 or id >= len(channel_candidates):
    await interaction.response.send_message("idが不適です。", ephemeral=True)
    return
  for i, key in enumerate(channel_candidates):
    if i != id:
      continue
    channel_candidates.pop(key)
    await interaction.response.send_message(key + "を削除しました。")
    saveCandidates()
    return

@tree.command(name="clear_all_candidates", description="clear_all_candidates")
async def clear_all_candidates(interaction: discord.Interaction):
  guild_id = str(interaction.guild_id)
  channel_id = str(interaction.channel.id)
  channel_candidates = getChannelCandidates(guild_id, channel_id)
  channel_candidates.clear()
  saveCandidates()
  await interaction.response.send_message("全ての候補を削除しました。")

client.run(TOKEN)
