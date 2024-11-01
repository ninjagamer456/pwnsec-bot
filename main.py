import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
import asyncio
import requests
import random
import time
from datetime import datetime
from datetime import timedelta

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.members = True
intents.bans = True
intents.message_content = True
intents.guild_scheduled_events = True       

bot = commands.Bot(command_prefix='-', intents=intents)

@bot.command(name='trollhook')
@commands.has_permissions(manage_webhooks=True)
async def trollhook(ctx, member: discord.Member, *, message: str):
    await ctx.message.delete()

    if ctx.guild is None:
        await ctx.send(":x: You can't use this command in DMs.")
        return

    print(f"Trollhook triggered by {ctx.author} for {member} with message: {message}")

    try:
        webhook = await ctx.channel.create_webhook(name=member.display_name)
        print(f"Webhook created with URL: {webhook.url}")
    except Exception as e:
        print(f"Error creating webhook: {e}")
        await ctx.send(":x: Failed to create webhook.")
        return

    try:
        await webhook.send(content=message, avatar_url=member.avatar.url, allowed_mentions=discord.AllowedMentions.none())
        print(f"Message sent via webhook as {member.display_name}")
    except Exception as e:
        print(f"Error sending message via webhook: {e}")
        await ctx.send(":x: Failed to send message via webhook.")

    await asyncio.sleep(1)

    try:
        await webhook.delete()
        print("Webhook deleted successfully.")
    except Exception as e:
        print(f"Error deleting webhook: {e}")
        await ctx.send(":x: Failed to delete webhook.")

@trollhook.error
async def trollhook_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(":warning: Please mention a user and specify a message!")
        print("Error: Missing required argument.")

@trollhook.error
async def trollhook_permission_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(":x: You don't have Manage Webhooks permissions!")
        print("Error: Missing permissions.")

@bot.command(name='joke')
async def joke(ctx):

    response = requests.get("https://v2.jokeapi.dev/joke/Any?type=single")

    if response.status_code == 200:
        data = response.json()  
        joke = data.get('joke', 'Could not retrieve a joke.')  
        await ctx.send(joke)
    else:
        await ctx.send(":x: Could not retrieve a joke at this time.")

@bot.command(name='r34')
@commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
async def r34(ctx, *args):
    if not ctx.channel.is_nsfw():
        await ctx.send(":x: This command can only be used in NSFW channels.")
        return

    if args[-1].isdigit():
        num_images = int(args[-1])
        if num_images > 5:
            await ctx.send(":x: You can't request more than 5 images. The limit is 5.")
            return
        tags = args[:-1]
    else:
        num_images = 1
        tags = args

    query = '+'.join(tags)
    api_url = f"https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&tags={query}"

    response = requests.get(api_url)

    if response.status_code == 200:
        try:
            data = response.json()

            if not data:
                await ctx.send(":x: No results found.")
                return

            posts = random.sample(data, min(len(data), num_images))

            for post in posts:
                image_url = post['file_url']
                await ctx.send(image_url)

        except ValueError:
            await ctx.send(":x: Error retrieving data.")
    else:
        await ctx.send(":x: Failed to reach r34 API.")


@r34.error
async def r34_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f":hourglass_flowing_sand: Slow down! Wait {round(error.retry_after, 1)} seconds before trying again.")

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)  
@commands.bot_has_permissions(ban_members=True)  
async def ban(ctx, member: discord.Member = None, *, reason: str = "No reason provided"):

    if ctx.guild is None:
        return

    if member is None:
        await ctx.send("Please mention someone to ban.")
        return

    if member == ctx.me:
        await ctx.send("I can't ban myself.")
        return

    if member == ctx.guild.owner:
        await ctx.send("You can't ban the server owner.")
        return

    if member.top_role >= ctx.author.top_role:
        await ctx.send("You can't ban someone with a higher or equal role than you.")
        return

    try:
        await member.ban(reason=reason)

        embed = discord.Embed(
            title="User Banned!",
            description=f"<@{member.id}> has been banned.\nReason: {reason}\nModerator: <@{ctx.author.id}>\nTime Banned: <t:{int(time.time())}:T>",
            color=discord.Color.random()
        )
        embed.set_author(name="Ban System", icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text="Ban issued successfully")

        await ctx.send(embed=embed)

    except discord.Forbidden:
        await ctx.send("I don't have permission to ban this user.")
    except discord.HTTPException:
        await ctx.send("Failed to ban the user. Please try again.")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You are missing the required ban permission.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I am missing the required ban permission.")
    else:
        await ctx.send("An error occurred while trying to ban the user.")

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)  
@commands.bot_has_permissions(ban_members=True)  
async def unban(ctx, user_id: str):

    if ctx.guild is None:
        return

    if not user_id.isdigit():
        await ctx.send("Please provide a valid User ID to unban.")
        return

    user_id = int(user_id)
    try:
        user = await bot.fetch_user(user_id)  
        await ctx.guild.unban(user)

        embed = discord.Embed(
            title="User Unbanned!",
            description=f"<@{user.id}> has been unbanned!\nTime Unbanned: <t:{int(time.time())}:T>",
            color=discord.Color.random()
        )
        embed.set_author(name="Ban System", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    except discord.NotFound:
        await ctx.send("User not banned or does not exist.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to unban this user.")
    except discord.HTTPException:
        await ctx.send("Failed to unban the user. Please try again.")

@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You are missing the required ban permission.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I am missing the required ban permission.")
    else:
        await ctx.send("An error occurred while trying to unban the user.")

@bot.command(name='lock')
@commands.has_permissions(manage_channels=True)  
async def lock(ctx, channel: discord.TextChannel = None):

    channel = channel or ctx.channel

    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    embed = discord.Embed(
        description=f"🔒 <@{ctx.author.id}>: <#{channel.id}> locked. Use `!unlock #{channel.name}` to lift the lockdown.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command(name='unlock')
@commands.has_permissions(manage_channels=True)  
async def unlock(ctx, channel: discord.TextChannel = None):

    channel = channel or ctx.channel

    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    embed = discord.Embed(
        description=f"🔓 <@{ctx.author.id}>: <#{channel.id}> unlocked - lockdown lifted.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@lock.error
@unlock.error
async def permission_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Nonperms")  

@bot.command(name='nick')
@commands.has_permissions(manage_nicknames=True)
async def nick(ctx, member: discord.Member = None, *, nickname: str = None):

    if member is None:
        await ctx.send("❌️ Please mention the user whose nickname you want to change.\nUsage: `!nick @user [nickname]`")
        return

    if not ctx.author.guild_permissions.manage_nicknames:
        await ctx.send("You are missing the Manage Nicknames permission!")
        return

    if member.guild_permissions.administrator:
        await ctx.send("You can't change Admin nicknames!")
        return

    color = ctx.author.top_role.color

    if nickname and nickname.lower() == "reset":
        await member.edit(nick=None)
        embed = discord.Embed(
            description=f"Reset {member.mention}'s nickname back to `{member.name}`.",
            color=color
        )
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)
    else:

        await member.edit(nick=nickname)
        embed = discord.Embed(
            description=f"Changed {member.mention}'s nickname to `{nickname}`.",
            color=color
        )
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)

@nick.error
async def nick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You are missing the Manage Nicknames permission!")

@bot.command(name='purge')
@commands.has_permissions(manage_messages=True)  
async def purge(ctx, number_of_messages: int):

    if number_of_messages <= 0:
        await ctx.send("❌ Please specify a positive number of messages to delete.")
        return

    deleted = await ctx.channel.purge(limit=number_of_messages + 1)  

    confirmation = await ctx.send(f"✅ Deleted {number_of_messages} messages.")

    await confirmation.delete(delay=3)

@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You are missing the Manage Messages permission!")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Please specify a valid number of messages to delete.")

@bot.command(name='user')
async def user_info(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("❌️ Please ping a user to see their info.\nUsage: `-user @user`")
        return

    embed = discord.Embed(title="**USER INFO**", color=0x00FF21)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Requested by - {ctx.author.name}")

    embed.add_field(name="👤 **Name:**", value=f"`{member.name}`", inline=False)
    embed.add_field(name="🪪 **ID:**", value=f"`{member.id}`", inline=False)
    embed.add_field(name="🤖 **Bot:**", value=f"`{member.bot}`", inline=False)
    embed.add_field(name="🏷 **Tag:**", value=f"`#{member.discriminator}`", inline=False)
    embed.add_field(name="🛠 **Admin:**", value=f"`{member.guild_permissions.administrator}`", inline=False)
    embed.add_field(name="📅 **Creation:**", value=f"`{member.created_at.strftime('%Y-%m-%d')}`", inline=False)
    embed.add_field(name="🗓 **Join date:**", value=f"`{member.joined_at.strftime('%Y-%m-%d')}`", inline=False)
    embed.add_field(name="📬 **DM Enabled:**", value=f"`{'Yes' if member.dm_channel else 'No'}`", inline=False)

    hype_squad = None
    for badge in member.public_flags.all():
        if badge == discord.PublicUserFlags.hypesquad_brilliance:
            hype_squad = "Brilliance"
            embed.color = 0xF57B66
        elif badge == discord.PublicUserFlags.hypesquad_bravery:
            hype_squad = "Bravery"
            embed.color = 0x9B84EE
        elif badge == discord.PublicUserFlags.hypesquad_balance:
            hype_squad = "Balance"
            embed.color = 0x44DDC1

    hype_squad_text = f"`{hype_squad}`" if hype_squad else "`This user doesn't belong to any HypeSquad.`"
    embed.add_field(name="🔗 **HypeSquad:**", value=hype_squad_text, inline=False)

    embed.timestamp = datetime.utcnow()
    await ctx.send(embed=embed)

@bot.command(name='avatar')
async def avatar(ctx, member: discord.Member = None):

    if member is None:
        member = ctx.author

    embed = discord.Embed(title=f"{member.name}'s avatar", url=member.display_avatar.url)
    embed.set_image(url=member.display_avatar.with_size(4096).url)
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)

user_data = {}  

def init_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "Gems": 100,
            "bjrunning": False,
            "dealerbj": 0,
            "playerbj": 0,
            "betamnt": 0,
            "bankgems": 0,
            "lottery": 0,
            "memorymatchdata": 0
        }

class Blackjack:
    @staticmethod
    def draw_card():
        return random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11])

@bot.command(name="bj")
async def bj(ctx, bet_amount: int = None):
    init_user(ctx.author.id)
    user = user_data[ctx.author.id]

    if user["bjrunning"]:
        await ctx.send("Another blackjack game is running, please finish it first.")
        return

    if bet_amount is None:
        await ctx.send("Please enter a betting amount.")
        return

    if not isinstance(bet_amount, int) or bet_amount <= 0:
        await ctx.send("Your betting amount needs to be a positive number.")
        return

    if user["Gems"] < bet_amount:
        await ctx.send("Your betting amount can't be higher than your gems amount.")
        return

    user["dealerbj"] = Blackjack.draw_card()
    user["playerbj"] = random.randint(4, 21)
    user["bjrunning"] = True
    user["betamnt"] = bet_amount
    user["Gems"] -= bet_amount

    embed = discord.Embed(title="Blackjack", color=0x152238)
    embed.add_field(name="Your hand:", value=f"{user['playerbj']}🔹", inline=False)
    embed.add_field(name="Dealer hand:", value=f"{user['dealerbj']}🔹", inline=False)
    embed.set_footer(text="Use !s to save or !h to hit")
    await ctx.send(embed=embed)

@bot.command(name="s")
async def save(ctx):
    init_user(ctx.author.id)
    user = user_data[ctx.author.id]

    if not user["bjrunning"]:
        await ctx.send("No blackjack game is currently running.")
        return

    while user["dealerbj"] <= 16:
        user["dealerbj"] += Blackjack.draw_card()

    user["bjrunning"] = False
    result_embed = discord.Embed(title="Blackjack")

    if user["playerbj"] > 21:
        result_embed.description = f"Your hand: {user['playerbj']}🔹\nDealer hand: {user['dealerbj']}🔹"
        result_embed.color = 0xFF0000
        result_embed.set_footer(text=f"Lost {user['betamnt']} gems")

    elif user["dealerbj"] > 21 or user["playerbj"] > user["dealerbj"]:
        winnings = user["betamnt"] * 2
        user["Gems"] += winnings
        result_embed.description = f"Your hand: {user['playerbj']}🔹\nDealer hand: {user['dealerbj']}🔹"
        result_embed.color = 0x00FF00
        result_embed.set_footer(text=f"Won {user['betamnt']} gems")

    elif user["playerbj"] < user["dealerbj"]:
        result_embed.description = f"Your hand: {user['playerbj']}🔹\nDealer hand: {user['dealerbj']}🔹"
        result_embed.color = 0xFF0000
        result_embed.set_footer(text=f"Lost {user['betamnt']} gems")

    else:
        user["Gems"] += user["betamnt"]
        result_embed.description = f"Your hand: {user['playerbj']}🔹\nDealer hand: {user['dealerbj']}🔹"
        result_embed.color = 0x00FF00
        result_embed.set_footer(text=f"Push {user['betamnt']} gems")

    await ctx.send(embed=result_embed)

@bot.command(name="h")
async def hit(ctx):
    init_user(ctx.author.id)
    user = user_data[ctx.author.id]

    if not user["bjrunning"]:
        await ctx.send("No blackjack game is currently running.")
        return

    user["playerbj"] += Blackjack.draw_card()

    embed = discord.Embed(title="Blackjack", color=0x152238)
    embed.add_field(name="Your hand:", value=f"{user['playerbj']}🔹", inline=False)
    embed.add_field(name="Dealer hand:", value=f"{user['dealerbj']}🔹", inline=False)

    if user["playerbj"] > 21:
        user["bjrunning"] = False
        embed.color = 0xFF0000
        embed.set_footer(text=f"Lost {user['betamnt']} gems")
    else:
        embed.set_footer(text="Use !s to save or !h to hit")

    await ctx.send(embed=embed)

@bot.command(name="bal")
async def balance(ctx, member: discord.Member = None):

    member = member or ctx.author
    init_user(member.id)  

    if member.bot:
        await ctx.send("**Discord bots don't have a bank account**")
        return

    user = user_data[member.id]
    hand = user["Gems"]
    bank = user["bankgems"]
    lottery = user["lottery"]
    total = hand + bank

    embed = discord.Embed(title=f"{member.display_name}'s Balance", color=random.randint(55555, 99999))
    embed.add_field(name="Hand", value=hand)
    embed.add_field(name="Bank", value=bank)
    embed.add_field(name="Total", value=total)
    embed.add_field(name="Lottery", value=lottery)
    embed.set_footer(text="Bank Statistics")
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.timestamp = discord.utils.utcnow()

    await ctx.send(embed=embed)

@bot.command(name="givegems")
async def give_gems(ctx, member: discord.Member = None, amount: int = None):

    if not member:
        await ctx.send("**⚠️ Please mention somebody to give gems**")
        return
    if member == ctx.author:
        await ctx.send("**⚠️ You can't give gems to yourself**")
        return
    if member.bot:
        await ctx.send("**Discord bots don't have a bank account**")
        return
    if amount is None or amount <= 0:
        await ctx.send("**⚠️ Provide a valid amount to send**")
        return

    init_user(ctx.author.id)
    init_user(member.id)

    if user_data[ctx.author.id]["Gems"] < amount:
        await ctx.send("**⚠️ You don't have that many gems in your hand**")
        return

    user_data[ctx.author.id]["Gems"] -= amount
    user_data[member.id]["Gems"] += amount

    embed = discord.Embed(description=f"**{ctx.author.mention} sent {amount} Gems to {member.mention}**", color=0x5865F2)
    await ctx.send(embed=embed)

@bot.command(name="work")
@commands.cooldown(1, 4, commands.BucketType.user)  
async def work(ctx):
    embed = discord.Embed(title="Work", description="Choose a job to earn Gems:", color=0x2F3136)

    view = discord.ui.View()
    jobs = {
        "fishing": "Fishing",
        "uber": "Uber Driver",
        "pizza": "Pizza Delivery",
        "barber": "Barber",
        "postman": "Postman",
        "cook": "Chef",
        "developer": "Developer",
        "lawyer": "Lawyer",
        "boxer": "Boxer",
        "journalist": "Journalist"
    }

    for job_id, job_name in jobs.items():
        view.add_item(discord.ui.Button(label=job_name, style=discord.ButtonStyle.primary, custom_id=job_id))

    await ctx.send(embed=embed, view=view)

@work.error
async def work_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Calm down, you are using this command too quickly. Try again in {error.retry_after:.1f} seconds.")

@bot.event
async def on_interaction(interaction: discord.Interaction):

    if interaction.data["component_type"] != 2:  
        return

    job_earnings = {
        "fishing": (100, 500, "You caught a pretty big fish and sold it for {amount} Gems."),
        "uber": (100, 500, "You helped someone get to their destination and earned {amount} Gems."),
        "pizza": (100, 500, "You delivered a pizza and earned {amount} Gems."),
        "barber": (200, 500, "The customer liked the haircut and gave you {amount} Gems."),
        "postman": (300, 700, "The manager was happy with your work and gave you {amount} Gems."),
        "cook": (1000, 2000, "You won a chef competition and earned {amount} Gems."),
        "developer": (3000, 5000, "You helped a company make a security system and earned {amount} Gems."),
        "lawyer": (5000, 6000, "You defended an innocent person, won the case, and earned {amount} Gems."),
        "boxer": (10000, 15000, "You fought well and won the grand prize of {amount} Gems."),
        "journalist": (500, 1000, "The magazine liked your article and gave you {amount} Gems.")
    }

    job_id = interaction.data["custom_id"]
    if job_id in job_earnings:
        min_earn, max_earn, message = job_earnings[job_id]
        earnings = random.randint(min_earn, max_earn)

        init_user(interaction.user.id)

        user_data[interaction.user.id]["bankgems"] += earnings

        embed = discord.Embed(
            description=f"**{interaction.user.mention}** " + message.format(amount=earnings),
            color=random.randint(0x11111, 0x99999)
        )
        await interaction.response.edit_message(embed=embed, view=None)  

@bot.command(name="deposit")
async def deposit(ctx, amount: int):

    if amount <= 0:
        await ctx.send("**⚠️Invalid amount. Please provide a positive number.**")
        return

    init_user(ctx.author.id)

    if user_data[ctx.author.id]["Gems"] < amount:
        await ctx.send("**⚠️You don't have that many gems in your hand.**")
        return

    user_data[ctx.author.id]["Gems"] -= amount
    user_data[ctx.author.id]["bankgems"] += amount

    embed = discord.Embed(
        description=f"**✅ Successfully deposited {amount:,} Gems into your bank.**",
        color=random.randint(0x55555, 0x99999)
    )
    embed.set_thumbnail(url=ctx.bot.user.avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="withdraw")
async def withdraw(ctx, amount: int):

    if amount <= 0:
        await ctx.send("**⚠️Invalid amount. Please provide a positive number.**")
        return

    init_user(ctx.author.id)

    if user_data[ctx.author.id]["bankgems"] < amount:
        await ctx.send("**⚠️You don't have that many gems in your bank.**")
        return

    user_data[ctx.author.id]["Gems"] += amount
    user_data[ctx.author.id]["bankgems"] -= amount

    embed = discord.Embed(
        description=f"**✅ Successfully withdrew {amount:,} Gems from your bank.**",
        color=random.randint(0x55555, 0x99999)
    )
    embed.set_thumbnail(url=ctx.bot.user.avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="rob")
@cooldown(1, 10800, BucketType.user)  
async def rob(ctx, member: discord.Member):

    if member == ctx.author:
        await ctx.send("**⚠️You can't rob yourself.**")
        return
    if member.bot:
        await ctx.send("**Discord bots don't have a bank account.**")
        return

    init_user(ctx.author.id)
    init_user(member.id)

    if user_data[ctx.author.id]["bankgems"] < 10000:
        await ctx.send("**⚠️You must have at least 10,000 Gems in your bank to rob.**")
        return
    if user_data[member.id]["bankgems"] < 10000:
        await ctx.send("**⚠️The user must have at least 10,000 Gems in their bank.**")
        return

    luck = random.randint(1, 7)
    if luck in [1, 2]:  
        stolen_amount = random.randint(1000, 7000)
        user_data[ctx.author.id]["bankgems"] += stolen_amount
        user_data[member.id]["bankgems"] -= stolen_amount
        await ctx.send(f"**✅ You successfully robbed {stolen_amount:,} Gems from {member.display_name}.**")
    else:  
        fine_amount = random.randint(2000, 8000)
        user_data[ctx.author.id]["bankgems"] -= fine_amount
        user_data[member.id]["bankgems"] += fine_amount
        await ctx.send(f"**❌ Your robbery attempt failed, and you were fined {fine_amount:,} Gems.**")

@bot.command(name="gamble")
async def gamble(ctx, amount: int):

    if amount <= 0:
        await ctx.send("**⚠️Invalid amount. Please provide a positive number.**")
        return

    init_user(ctx.author.id)

    if user_data[ctx.author.id]["Gems"] < amount:
        await ctx.send("**⚠️You don't have that many Gems on hand.**")
        return

    luck = random.randint(1, 7)
    if luck in [1, 2]:  
        winnings = amount * random.randint(1, 5)
        user_data[ctx.author.id]["Gems"] += winnings
        await ctx.send(f"**✅ You won the gamble and gained {winnings:,} Gems!**")
    else:  
        user_data[ctx.author.id]["Gems"] -= amount
        await ctx.send("**❌ You lost the gamble and the Gems you bet.**")

@bot.command(name="resetbal")
async def resetbal(ctx):

    user_data[ctx.author.id] = {"Gems": 100, "bankgems": 0}
    await ctx.send("**Your Gems in hand and bank Gems have been reset.**")

@bot.command(name="income")
@cooldown(1, 86400, BucketType.user)  
async def income(ctx):

    init_user(ctx.author.id)

    daily_income = random.randint(3000, 5000)
    user_data[ctx.author.id]["Gems"] += daily_income

    embed = discord.Embed(
        title="Your Daily Income",
        description=f"**You earned {daily_income:,} Gems!**",
        color=random.randint(0x11111, 0x99999)
    )
    embed.set_thumbnail(url=ctx.bot.user.avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="buylotteryticket")
async def buylotteryticket(ctx, amount: int = 1):
    user_id = str(ctx.author.id)
    init_user(user_id)  

    ticket_cost = 20000 * amount

    if user_data[user_id]["Gems"] < ticket_cost:
        await ctx.send("**You need at least 20000 Gems per ticket.**")
        return

    user_data[user_id]["Gems"] -= ticket_cost
    user_data[user_id]["lottery"] += amount

    await ctx.send(f"**You have bought {amount} lottery ticket(s).**")

@bot.command(name="scratch")
async def scratch(ctx):
    user_id = str(ctx.author.id)
    init_user(user_id)  

    if user_data[user_id]["lottery"] <= 0:
        await ctx.send("**You don't have any lottery tickets.**")
        return

    user_data[user_id]["lottery"] -= 1

    chance = random.randint(1, 16)
    if chance <= 7:
        await ctx.send("**You lost the lottery and gained nothing.**")
    elif 8 <= chance <= 12:
        prize = random.randint(25000, 50000)
        user_data[user_id]["Gems"] += prize
        await ctx.send(f"**✅ You won the lottery! You gained {prize} Gems.**")
    else:
        prize = random.randint(60000, 100000)
        user_data[user_id]["Gems"] += prize
        await ctx.send(f"**✅ Big win! You gained {prize} Gems.**")

@bot.command(name="coinflip")
async def coinflip(ctx, amount: int, guess: str):
    user_id = str(ctx.author.id)
    init_user(user_id)  

    if user_data[user_id]["Gems"] < amount:
        await ctx.send("**You don't have that many Gems to bet.**")
        return

    if guess not in ["Head", "Tails"]:
        await ctx.send("**Please choose 'Head' or 'Tails'.**")
        return

    flip_result = random.choice(["Head", "Tails"])

    if flip_result == guess:
        winnings = amount * random.randint(1, 5)
        user_data[user_id]["Gems"] += winnings
        await ctx.send(f"**It's {flip_result}! You won {winnings} Gems!**")
    else:
        user_data[user_id]["Gems"] -= amount
        await ctx.send(f"**It's {flip_result}. You lost your bet of {amount} Gems.**")

@bot.command(name="define")
async def define(ctx, word: str = None):
    if not word:
        await ctx.send("**Type a word to define.**")
        return

    word = word.lower()
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

    try:
        response = requests.get(url)
        data = response.json()

        if isinstance(data, dict) and data.get("title") == "No Definitions Found":
            await ctx.send(f"**The word '{word}' does not exist in the API database.**")
        else:
            definition = data[0]["meanings"][0]["definitions"][0]["definition"]
            embed = discord.Embed(title=word, description=definition, color=0x2b2d31)
            await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send("**An error occurred while fetching the definition.**")
        print(e) 

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)  
@commands.bot_has_permissions(kick_members=True)  
async def kick(ctx, member: discord.Member = None, *, reason: str = None):

    if ctx.guild is None:
        await ctx.send("**Can't use this command in DMs!**")
        return

    if member is None:
        await ctx.send("**Mention someone to kick!**")
        return

    if member == ctx.author:
        await ctx.send("**You can't kick yourself!**")
        return

    if member == ctx.guild.owner:
        await ctx.send("**You can't kick the server owner!**")
        return

    if reason is None:
        await ctx.send("**Please provide a reason!**")
        return

    try:

        await member.kick(reason=reason)

        embed = discord.Embed(
            title=f"{member.name}#{member.discriminator} has been kicked!",
            description=f"**ID:** {member.id}\n**Reason:** {reason}\n**Who kicked:** {ctx.author.display_name}",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text="Kicked")
        embed.timestamp = ctx.message.created_at
        await ctx.send(embed=embed)

    except discord.Forbidden:
        await ctx.send("**I don't have permission to kick this member!**")
    except Exception as e:
        await ctx.send("**An error occurred while trying to kick the member.**")
        print(e)

bot.command(name="mute")
@commands.has_permissions(moderate_members=True)  
@commands.bot_has_permissions(moderate_members=True)  
async def mute(ctx, member: discord.Member = None, time: str = None):

    if ctx.guild is None:
        await ctx.send("**Can't use this command in DMs!**")
        return

    if member is None:
        await ctx.send("**Mention someone to mute!**")
        return

    if member == ctx.author:
        await ctx.send("**You can't mute yourself!**")
        return

    if member == ctx.guild.owner:
        await ctx.send("**You can't mute the server owner!**")
        return

    if time is None:
        await ctx.send("**Please provide a time duration!**")
        return

    try:
        time_multiplier = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        duration = int(time[:-1]) * time_multiplier[time[-1]]
        mute_duration = timedelta(seconds=duration)
    except (ValueError, KeyError):
        await ctx.send("**Invalid time format! Use `s`, `m`, `h`, or `d` for seconds, minutes, hours, or days.**")
        return

    try:

        await member.timeout(mute_duration)

        embed = discord.Embed(
            title=f"{member.name}#{member.discriminator} has been muted!",
            description=f"**ID:** {member.id}\n**Time:** {time}\n**Muted by:** {ctx.author.display_name}",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text="Muted")
        embed.timestamp = ctx.message.created_at
        await ctx.send(embed=embed)

    except discord.Forbidden:
        await ctx.send("**I don't have permission to mute this member!**")
    except Exception as e:
        await ctx.send("**An error occurred while trying to mute the member.**")
        print(e)

@bot.command(name="serverinfo")
async def serverinfo(ctx):
    guild = ctx.guild  
    owner = guild.owner 
    created_at = guild.created_at.strftime("%B %d, %Y")  
    member_count = guild.member_count 
    channel_count = len(guild.channels) 
    role_count = len(guild.roles)  
    icon_url = guild.icon.url if guild.icon else None 

    embed = discord.Embed(title=f"📊 Serverinfo for {guild.name}", color=0x3498db)
    embed.set_thumbnail(url=icon_url)  
    embed.add_field(name="👑 Owner", value=f"{owner.mention}", inline=True)
    embed.add_field(name="📅 Created On", value=created_at, inline=True)
    embed.add_field(name="👥 Members", value=member_count, inline=True)
    embed.add_field(name="💬 Channels", value=channel_count, inline=True)
    embed.add_field(name="📜 Roles", value=role_count, inline=True)

    embed.set_footer(text=f"Server ID: {guild.id}")

    await ctx.send(embed=embed)

bot.command(name="search")
async def search(ctx, platform: str = None, *, query: str = None):
    if not platform or not query:
        await ctx.send("❌️ Please specify a platform and query.\n**Usage:** `-search google/instagram/youtube/spotify/steam/github/twitch/soundcloud/tiktok/wikipedia (query)`")
        return

    platforms = {
        "steam": {
            "url": f"https://store.steampowered.com/search/?term={query.replace(' ', '+')}",
            "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Breezeicons-apps-48-steam.svg/1024px-Breezeicons-apps-48-steam.svg.png",
            "title": "Steam Search"
        },
        "google": {
            "url": f"https://www.google.com/search?q={query.replace(' ', '%20')}",
            "icon": "https://news-cdn.softpedia.com/images/news2/the-new-google-logo-is-a-lesson-in-modern-design-490648-3.jpg",
            "title": "Google Search"
        },
        "spotify": {
            "url": f"https://open.spotify.com/search/{query.replace(' ', '%20')}",
            "icon": "https://www.abagarecords.com/files/social-icons/spotify.png",
            "title": "Spotify Search"
        },
        "twitch": {
            "url": f"https://www.twitch.tv/search?term={query.replace(' ', '%20')}",
            "icon": "https://www.shareicon.net/data/2015/10/04/111738_twitch_512x512.png",
            "title": "Twitch Search"
        },
        "soundcloud": {
            "url": f"https://soundcloud.com/search?q={query.replace(' ', '%20')}",
            "icon": "https://cdn0.iconfinder.com/data/icons/free-social-media-set/24/soundcloud-512.png",
            "title": "SoundCloud Search"
        },
        "github": {
            "url": f"https://github.com/search?q={query.replace(' ', '+')}",
            "icon": "https://cdn4.iconfinder.com/data/icons/iconsimple-logotypes/512/github-512.png",
            "title": "GitHub Search"
        },
        "youtube": {
            "url": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
            "icon": "https://cdn4.iconfinder.com/data/icons/iconsimple-logotypes/512/youtube-512.png",
            "title": "YouTube Search"
        },
        "instagram": {
            "url": f"https://www.instagram.com/{query.strip()}",
            "icon": "https://www.freepnglogos.com/uploads/logo-ig-png/logo-ig-instagram-new-logo-vector-download-13.png",
            "title": "Instagram Search"
        },
        "wikipedia": {
            "url": f"https://en.wikipedia.org/w/index.php?search={query.replace(' ', '+')}",
            "icon": "https://upload.wikimedia.org/wikipedia/commons/6/63/Wikipedia-logo.png",
            "title": "Wikipedia Search"
        },
        "tiktok": {
            "url": f"https://www.tiktok.com/@{query.strip()}",
            "icon": "https://pngimg.com/uploads/tiktok/tiktok_PNG21.png",
            "title": "TikTok Account Search"
        }
    }

    platform = platform.lower()
    if platform not in platforms:
        await ctx.send("```\nUsage: -search google weather forecast\nAvailable Platforms: steam, google, spotify, twitch, soundcloud, github, youtube, instagram, tiktok, wikipedia\n```")
        return

    platform_data = platforms[platform]
    embed = discord.Embed(
        title=f"{platform_data['title']} - {query}",
        description=f"[Click here for search results]({platform_data['url']})",
        color=0x9B30FF
    )
    embed.set_author(name=f"{ctx.author.display_name} searched for: {query}", icon_url=platform_data["icon"])
    embed.set_thumbnail(url=platform_data["icon"])

    await ctx.send(embed=embed)

log_channels = {}

@bot.command(name="setlog")
@commands.has_permissions(manage_guild=True)
async def set_log_channel(ctx):
    log_channels[ctx.guild.id] = ctx.channel.id
    await ctx.send(f"Logging channel set to {ctx.channel.mention}")

async def get_log_channel(guild):
    channel_id = log_channels.get(guild.id)
    return guild.get_channel(channel_id)

@bot.event
async def on_guild_channel_create(channel):
    log_channel = await get_log_channel(channel.guild)
    if log_channel:
        embed = discord.Embed(title="Channel Created", color=discord.Color.green())
        embed.add_field(name="Channel", value=channel.mention)
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_channel_delete(channel):
    log_channel = await get_log_channel(channel.guild)
    if log_channel:
        embed = discord.Embed(title="Channel Deleted", color=discord.Color.red())
        embed.add_field(name="Channel Name", value=channel.name)
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_channel_update(before, after):
    log_channel = await get_log_channel(before.guild)
    if log_channel and before.overwrites != after.overwrites:
        embed = discord.Embed(title="Channel Permissions Updated", color=discord.Color.blue())
        embed.add_field(name="Channel", value=after.mention)
        embed.add_field(name="Changes", value="Updated Permissions")
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_update(before, after):
    log_channel = await get_log_channel(before.guild)
    if log_channel:
        embed = discord.Embed(title="Role Updated", color=discord.Color.purple())
        embed.add_field(name="Role", value=after.mention)
        embed.add_field(name="Changes", value="Updated Role Permissions")
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_create(role):
    log_channel = await get_log_channel(role.guild)
    if log_channel:
        embed = discord.Embed(title="Role Created", color=discord.Color.green())
        embed.add_field(name="Role", value=role.mention)
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_delete(role):
    log_channel = await get_log_channel(role.guild)
    if log_channel:
        embed = discord.Embed(title="Role Deleted", color=discord.Color.red())
        embed.add_field(name="Role Name", value=role.name)
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    async for entry in member.guild.audit_logs(limit=1, action=AuditLogAction.kick):
        if entry.target.id == member.id:
            log_channel = await get_log_channel(member.guild)
            if log_channel:
                embed = discord.Embed(title="Member Kicked", color=discord.Color.red())
                embed.add_field(name="Member", value=member.mention)
                embed.add_field(name="Reason", value=entry.reason or "No reason provided")
                embed.timestamp = datetime.datetime.utcnow()
                await log_channel.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    log_channel = await get_log_channel(guild)
    if log_channel:
        embed = discord.Embed(title="Member Banned", color=discord.Color.red())
        embed.add_field(name="User", value=user.mention)
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)

@bot.event
async def on_webhooks_update(channel):
    log_channel = await get_log_channel(channel.guild)
    if log_channel:
        embed = discord.Embed(title="Webhook Updated", color=discord.Color.orange())
        embed.add_field(name="Channel", value=channel.mention)
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    log_channel = await get_log_channel(before.guild)
    if log_channel and before.timed_out_until != after.timed_out_until:
        timeout_status = "Timeout Set" if after.timed_out_until else "Timeout Removed"
        embed = discord.Embed(title=f"Member {timeout_status}", color=discord.Color.yellow())
        embed.add_field(name="Member", value=after.mention)
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_update(before, after):
    log_channel = await get_log_channel(before)
    if log_channel:
        embed = discord.Embed(title="Server Updated", color=discord.Color.gold())
        embed.add_field(name="Changes", value="Updated Server Settings")
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

bot.run('MTMwMDgyODEyMTczMzUzMzcwNg.GnV1Wg.cyMW4HpTKIwy4td_5RmtgRZ0EWcAHlSqpDPfa4')