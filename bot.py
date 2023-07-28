import discord
from discord.ext import commands, tasks
from discord.ui import View, Select, Button
from datetime import datetime, timedelta
import asyncio, aiohttp, os, random, openai, json
from discord.interactions import Interaction

openai.api_key = 'sk-jEHPwAEyS80PmZTlHq6' + 'LT3BlbkFJvVEnsYaN8mSGTZ3ECm6z' # Free tier key, sharable

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
intents = discord.Intents.default()

TOKEN = os.environ.get("TOKEN")

@bot.event
async def on_ready():
    print("Bot is UP and Ready!")
    check_events.start()  # starts the task when the bot is ready
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)





welcome_enabled = True  # initially the welcome messages are enabled



@bot.tree.command(name='toggle_welcome')
@commands.has_permissions(administrator=True)  # only allow administrators to run this command
async def toggle_welcome(ctx):
    global welcome_enabled
    welcome_enabled = not welcome_enabled
    status = "enabled" if welcome_enabled else "disabled"
    await ctx.response.send_message(f"Welcome DMs have been {status}.")




@bot.event
async def on_member_join(member):
    global welcome_enabled
    if welcome_enabled:

        embed = discord.Embed(
            title="Welcome to Computing Councils of Canada",
            description=(
                "We are delighted to have you join us. "
                "This community is focused on bringing together "
                "all enthusiasts and professionals related to computing. "
                "Here, we discuss, share, and learn about various computing topics. "
                "Feel free to explore, engage in discussions, and most importantly, "
                "have fun! If you have any questions, don't hesitate to ask."
            ),
            color=0x1a384c,
        )
        embed.set_thumbnail(url="https://media.licdn.com/dms/image/C4E0BAQFZ83Q-ryJyYw/company-logo_200_200/0/1612553017924?e=2147483647&v=beta&t=gQtTxgENMUZilwaIRFW-UVbVkEdX0W7HdhFmDXj5Kng")
        await message.author.send(embed=embed)








class IgnoreButton(discord.ui.Button):
    def __init__(self, flagged_message):
        super().__init__(label="Ignore", style=discord.ButtonStyle.green, emoji="✅")
        self.flagged_message = flagged_message

    async def callback(self, interaction: discord.Interaction):
        # Edit the embed color to green and change the title
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "👍 Message Confirmed 👍"
        await interaction.message.edit(embed=embed)

class RemoveButton(discord.ui.Button):
    def __init__(self, flagged_message):
        super().__init__(label="Remove", style=discord.ButtonStyle.secondary, emoji="🗑️")
        self.flagged_message = flagged_message

    async def callback(self, interaction: discord.Interaction):
        # Delete the flagged message and change the embed color to orange
        await self.flagged_message.delete()
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.orange()
        embed.title = "🚫 Message Removed 🚫"
        await interaction.message.edit(embed=embed)

class RemoveAndMuteButton(discord.ui.Button):
    def __init__(self, flagged_message):
        super().__init__(label="Remove and Mute", style=discord.ButtonStyle.red, emoji="🔕")
        self.flagged_message = flagged_message

    async def callback(self, interaction: discord.Interaction):
        # Delete the flagged message, change the embed color to yellow, and mute the user for 1 day
        await self.flagged_message.delete()
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.yellow()
        embed.title = "⏰ Message Removed and User Muted ⏰"
        await interaction.message.edit(embed=embed)

        # Mute the user for 1 day
        user = interaction.user
        mute_role = discord.utils.get(user.guild.roles, name="Muted")
        if mute_role is not None:
            await user.add_roles(mute_role)
            await asyncio.sleep(24 * 60 * 60)  # Wait for 1 day
            await user.remove_roles(mute_role)
        else:
            print("Muted role does not exist. Please create one.")

class MessageView(discord.ui.View):
    def __init__(self, flagged_message):
        super().__init__()
        self.add_item(IgnoreButton(flagged_message))
        self.add_item(RemoveButton(flagged_message))
        self.add_item(RemoveAndMuteButton(flagged_message))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
        
    # Create a conversation with the model
    # The prompt makes the model very eager to flag messages - maybe turn down the intensity to avoid randomly flagging ppl? ¯\_(ツ)_/¯
    empty = "{" + "}"
    conversation = [
        {"role": "system", "content": "You are a content review model. Your task is to review incoming messages and determine if they should be flagged for review. If a message is flagged, explain what parts were flagged and why. Only derogatory messages with clear malice should be flagged, ones made in good faith can remain unflagged. Respond ONLY in the correct format, your only two options are empty brackets and flagged=true, sections and the reason in JSON format."},
        {"role": "user", "content": "Check message: hi"},
        {"role": "assistant", "content": empty},
        {"role": "user", "content": "Check message: what's your github? i'll add you there."},
        {"role": "assistant", "content": empty},
        {"role": "user", "content": "Check message: Sure you can check my js stuff there its https://github.com/stevejobs"},
        {"role": "assistant", "content": empty},
        {"role": "user", "content": "Check message: bro you're actually so stupid and dumb and a dummy poopy head and you should actually go back to grade 1 like why would you think javascript is a good language"},
        {"role": "assistant", "content": '{"flagged":true,"sections":["stupid and dumb","dummy poopy head","go back to grade 1"],"reason":"The user\'s statement includes highly offensive language, personal attacks, and derogatory remarks."}'},
        {"role": "user", "content": "Check message: ??? What?"},
        {"role": "assistant", "content": empty},
        {"role": "user", "content": "Check message: " + message.content}
    ]
    # Generate a response from the model
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=conversation
    )

    # Get the model's reply
    model_reply = response['choices'][0]['message']['content']
  
    resp = json.loads(model_reply)
    # If the model decides to flag the message
    if 'flagged' in resp:
        guild = discord.utils.get(bot.guilds, name='Computing Councils of Canada - Internal')
        channel = discord.utils.get(guild.channels, name='bot-test')

        embed = discord.Embed(title="🚩 Flagged Message Review 🚩", description="A message has been flagged for review.", color=0xff0000)
        embed.add_field(name="User", value=message.author.mention, inline=False)

        # Replace flagged part in the message with a bolded version
        flagged_part = resp['sections']
        bolded_msg = message.content
        for flagged_section in flagged_part:
            bolded_msg = bolded_msg.replace(flagged_section, f'**{flagged_section}**')

        embed.add_field(name="Message Content", value=bolded_msg, inline=False)
        embed.add_field(name="Reason for Flagging", value=resp['reason'], inline=False)
        embed.set_thumbnail(url=message.author.avatar)

        # Send the message
        await channel.send(embed=embed, view=MessageView(message))

    # process commands after handling the message
    await bot.process_commands(message)


class PollOptionButton(Button):
    def __init__(self, label):
        super().__init__(style=discord.ButtonStyle.secondary, label=label.split(":")[0], row=0)
        self.vote_count = 0

    async def callback(self, interaction: Interaction):
        self.vote_count += 1
        self.label = f'{self.label} 🗳️'
        self.disabled = True
        await interaction.message.edit(embed=self.view.generate_embed(), view=self.view)

class PollView(View):
    def __init__(self, question, options):
        super().__init__(timeout=None)
        self.options = {option: PollOptionButton(option) for option in options}
        self.question = question
        for button in self.options.values():
            self.add_item(button)

    def generate_embed(self):
        total_votes = sum(button.vote_count for button in self.options.values())
        description = "```\n"
        max_option_length = max(len(option) for option in self.options.keys()) + 1  # include ':' in the option's length
        for option, button in self.options.items():
            percentage = (button.vote_count / total_votes) * 100 if total_votes > 0 else 0
            filled = int(percentage // 8.33)  # 1 character is 8.33% in a 12 character long bar
            empty = 12 - filled
            # pad the space between the option and the ASCII bar so that all bars start at the same position
            padded_option = (option + ':').ljust(max_option_length)
            description += f'{padded_option} {"▓" * filled}{"░" * empty} ({percentage:.2f}%)\n\n'
        description += "```"
        return discord.Embed(title="📊 " + self.question, description=description, color=0x1a384c)


@bot.tree.command(name='poll')
async def poll(interaction: Interaction, question: str, options: str):
    options = options.split(",")
    if len(options) < 2:
        await interaction.response.send_message("A poll must have at least two options.", ephemeral=True)
    elif len(options) > 25:
        await interaction.response.send_message("A poll can have at most 25 options.", ephemeral=True)
    else:
        view = PollView(question,options)
        await interaction.response.send_message(embed=view.generate_embed(), view=view)

@bot.tree.command(name='8ball', description='Ask the magic 8-ball for answers')
async def eightball(interaction: discord.Interaction, *, question: str):
    # Create a conversation with the model
    conversation = [
        {"role": "system", "content": "You are a Magic 8-ball response creator for the Computing Councils of Canada discord server (CCubed for short). You come up with creative responses to 8-ball prompts. Use emojis in your responses. Keep your responses short, around 8 words max. Each response needs to be in the form of a classic 8-Ball response, like 'Signs point to...'. Give amusing answers, ALWAYS."},
        {"role": "user", "content": f"leafs or bruins?"},
        {"role": "assistant", "content": f"🍁 Signs point to the Leafs, but expect disappointment. 🏒"},
        {"role": "user", "content": f"{question}"}
    ]
    
    # Generate a response from the model
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=conversation
    )
    
    # Get the model's reply
    model_reply = response['choices'][0]['message']['content']
    

    # Embed
    embed = discord.Embed(
        title="🎱 The Magic 8-Ball",
        description=f"Question: {question}",
        color=0x1a384c  # Dark blue color, CCubed theme
    )
    embed.add_field(name="Answer", value=model_reply, inline=False)
    embed.set_thumbnail(url="https://media.licdn.com/dms/image/C4E0BAQFZ83Q-ryJyYw/company-logo_200_200/0/1612553017924?e=2147483647&v=beta&t=gQtTxgENMUZilwaIRFW-UVbVkEdX0W7HdhFmDXj5Kng")
    embed.set_footer(text=f"Asked by {interaction.user.name}")

    # Send embed
    await interaction.response.send_message(embed=embed)

class UniversityAndInterestView(View):
    def __init__(self):
        super().__init__()
        self.add_item(AlbertaUniversitiesSelect())
        self.add_item(BritishColumbiaUniversitiesSelect())
        self.add_item(ManitobaUniversitiesSelect())
        self.add_item(NewBrunswickUniversitiesSelect())
        self.add_item(NovaScotiaUniversitiesSelect())

class UniversityAndInterestViewRest(View):
    def __init__(self):
        super().__init__()
        self.add_item(OntarioUniversitiesSelect())
        self.add_item(PrinceEdwardIslandUniversitiesSelect())
        self.add_item(QuebecUniversitiesSelect())
        self.add_item(SaskatchewanUniversitiesSelect())



# Alberta universities
class AlbertaUniversitiesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="University of Calgary", value="University of Calgary"),
            discord.SelectOption(label="MacEwan University", value="MacEwan University"),
            discord.SelectOption(label="University of Alberta", value="University of Alberta"),
            discord.SelectOption(label="Ambrose University", value="Ambrose University"),
            discord.SelectOption(label="Burman University", value="Burman University"),
            discord.SelectOption(label="Concordia University of Edmonton", value="Concordia University of Edmonton"),
            discord.SelectOption(label="Mount Royal University", value="Mount Royal University"),
            discord.SelectOption(label="Northern Alberta Institute of Technology", value="Northern Alberta Institute of Technology"),
            discord.SelectOption(label="SAIT Polytechnic", value="SAIT Polytechnic"),
            discord.SelectOption(label="St. Mary’s University", value="St. Mary’s University"),
            discord.SelectOption(label="The King’s University", value="The King’s University"),
            discord.SelectOption(label="University of Lethbridge", value="University of Lethbridge")
        ]
        super().__init__(placeholder="Select your University in Alberta", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        if role is not None:
            await interaction.response.send_message(f"Your selected university is: {self.values[0]}")
            await interaction.user.add_roles(role)

# British Columbia universities
class BritishColumbiaUniversitiesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="University of British Columbia", value="University of British Columbia"),
            discord.SelectOption(label="Simon Fraser University", value="Simon Fraser University"),
            discord.SelectOption(label="Thompson Rivers University", value="Thompson Rivers University"),
            discord.SelectOption(label="University of Northern BC", value="University of Northern BC"),
            discord.SelectOption(label="University of Fraser Valley", value="University of Fraser Valley"),
            discord.SelectOption(label="University of Victoria", value="University of Victoria"),
            discord.SelectOption(label="BC Institute of Technology", value="BC Institute of Technology"),
            discord.SelectOption(label="Capilano University", value="Capilano University"),
            discord.SelectOption(label="Kwantlen Polytechnic University", value="Kwantlen Polytechnic University"),
            discord.SelectOption(label="Nicola Valley Institute of Technology", value="Nicola Valley Institute of Technology"),
            discord.SelectOption(label="Quest University Canada", value="Quest University Canada"),
            discord.SelectOption(label="Royal Roads University", value="Royal Roads University"),
            discord.SelectOption(label="Trinity Western University", value="Trinity Western University"),
            discord.SelectOption(label="University Canada West", value="University Canada West"),
            discord.SelectOption(label="Vancouver Island University", value="Vancouver Island University")
        ]
        super().__init__(placeholder="Select your University in British Columbia", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        if role is not None:
            await interaction.response.send_message(f"Your selected university is: {self.values[0]}")
            await interaction.user.add_roles(role)







# Manitoba universities
class ManitobaUniversitiesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="University of Manitoba", value="University of Manitoba"),
            discord.SelectOption(label="University of Winnipeg", value="University of Winnipeg"),
            discord.SelectOption(label="Crandall University", value="Crandall University"),
            discord.SelectOption(label="Kingswood University", value="Kingswood University"),
            discord.SelectOption(label="St. Stephen’s University", value="St. Stephen’s University"),
            discord.SelectOption(label="Brandon University", value="Brandon University"),
            discord.SelectOption(label="Canadian Mennonite University", value="Canadian Mennonite University"),
            discord.SelectOption(label="Universite de Saint-Boniface", value="Universite de Saint-Boniface")
        ]
        super().__init__(placeholder="Select your University in Manitoba", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        if role is not None:
            await interaction.response.send_message(f"Your selected university is: {self.values[0]}")
            await interaction.user.add_roles(role)

# New Brunswick universities
class NewBrunswickUniversitiesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="University of New Brunswick", value="University of New Brunswick"),
            discord.SelectOption(label="Mount Allison University", value="Mount Allison University"),
            discord.SelectOption(label="Universite de Moncton", value="Universite de Moncton"),
            discord.SelectOption(label="Yorkville University", value="Yorkville University"),
            discord.SelectOption(label="St. Thomas University", value="St. Thomas University")
        ]
        super().__init__(placeholder="Select your University in New Brunswick", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        if role is not None:
            await interaction.response.send_message(f"Your selected university is: {self.values[0]}")
            await interaction.user.add_roles(role)

# Nova Scotia universities
class NovaScotiaUniversitiesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="St. Mary’s University", value="St. Mary’s University"),
            discord.SelectOption(label="St. Francis Xavier University", value="St. Francis Xavier University"),
            discord.SelectOption(label="Dalhousie University", value="Dalhousie University"),
            discord.SelectOption(label="Acadia University", value="Acadia University"),
            discord.SelectOption(label="Mount Saint Vincent University", value="Mount Saint Vincent University"),
            discord.SelectOption(label="Cape Breton University", value="Cape Breton University"),
            discord.SelectOption(label="NSCAD University", value="NSCAD University"),
            discord.SelectOption(label="University of King’s College", value="University of King’s College"),
            discord.SelectOption(label="Universite Sainte-Anne", value="Universite Sainte-Anne")
        ]
        super().__init__(placeholder="Select your University in Nova Scotia", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        if role is not None:
            await interaction.response.send_message(f"Your selected university is: {self.values[0]}")
            await interaction.user.add_roles(role)



# Ontario universities
class OntarioUniversitiesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Wilfrid Laurier University", value="Wilfrid Laurier University"),
            discord.SelectOption(label="Queen's University", value="Queen's University"),
            discord.SelectOption(label="Ryerson University", value="Ryerson University"),
            discord.SelectOption(label="Carleton University", value="Carleton University"),
            discord.SelectOption(label="University of Guelph", value="University of Guelph"),
            discord.SelectOption(label="University of Waterloo", value="University of Waterloo"),
            discord.SelectOption(label="University of Windsor", value="University of Windsor"),
            discord.SelectOption(label="Western University", value="Western University"),
            discord.SelectOption(label="Trent University", value="Trent University"),
            discord.SelectOption(label="York University", value="York University"),
            discord.SelectOption(label="University of Ottawa", value="University of Ottawa"),
            discord.SelectOption(label="McMaster University", value="McMaster University"),
            discord.SelectOption(label="University of Toronto - St. George", value="University of Toronto - St. George"),
            discord.SelectOption(label="University of Toronto - Missassauga", value="University of Toronto - Missassauga"),
            discord.SelectOption(label="University of Toronto - Scarborough", value="University of Toronto - Scarborough"),
            discord.SelectOption(label="Lakehead University", value="Lakehead University"),
            discord.SelectOption(label="Nipissing University", value="Nipissing University"),
            discord.SelectOption(label="Ontario Tech University", value="Ontario Tech University"),
            discord.SelectOption(label="Laurentian University", value="Laurentian University"),
            discord.SelectOption(label="Redeemer College", value="Redeemer College")
        ]
        super().__init__(placeholder="Select your University in Ontario", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        if role is not None:
            await interaction.response.send_message(f"Your selected university is: {self.values[0]}")
            await interaction.user.add_roles(role)

# Prince Edward Island universities
class PrinceEdwardIslandUniversitiesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="University of PEI", value="University of PEI")
        ]
        super().__init__(placeholder="Select your University in Prince Edward Island", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        if role is not None:
            await interaction.response.send_message(f"Your selected university is: {self.values[0]}")
            await interaction.user.add_roles(role)

# Quebec universities
class QuebecUniversitiesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="McGill University", value="McGill University"),
            discord.SelectOption(label="Concordia University", value="Concordia University"),
            discord.SelectOption(label="Université Laval", value="Université Laval"),
            discord.SelectOption(label="l'Université du Québec à Montréal", value="l'Université du Québec à Montréal"),
            discord.SelectOption(label="Algoma University", value="Algoma University"),
            discord.SelectOption(label="l'Université du Québec à Chicoutimi", value="l'Université du Québec à Chicoutimi"),
            discord.SelectOption(label="l’Universite de Montreal", value="l’Universite de Montreal"),
            discord.SelectOption(label="l'Université de Sherbrooke", value="l'Université de Sherbrooke"),
            discord.SelectOption(label="l'Université du Québec à Trois-Rivières", value="l'Université du Québec à Trois-Rivières"),
            discord.SelectOption(label="l'Université du Québec à Rimouski", value="l'Université du Québec à Rimouski"),
            discord.SelectOption(label="l'Université du Québec à Outaouais", value="l'Université du Québec à Outaouais"),
            discord.SelectOption(label="l'Université du Québec en Abitibi-Témiscamingue", value="l'Université du Québec en Abitibi-Témiscamingue"),
            discord.SelectOption(label="Bishop's University", value="Bishop's University"),
            discord.SelectOption(label="École de Technologie Supéreure (ÉTS)", value="École de Technologie Supéreure (ÉTS)"),
            discord.SelectOption(label="HEC Montréal", value="HEC Montréal"),
            discord.SelectOption(label="Polytechnique Montréal", value="Polytechnique Montréal")
        ]
        super().__init__(placeholder="Select your University in Quebec", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        if role is not None:
            await interaction.response.send_message(f"Your selected university is: {self.values[0]}")
            await interaction.user.add_roles(role)

# Saskatchewan universities
class SaskatchewanUniversitiesSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="University of Regina", value="University of Regina"),
            discord.SelectOption(label="University of Saskatchewan", value="University of Saskatchewan"),
            discord.SelectOption(label="First Nations University of Canada", value="First Nations University of Canada"),
            discord.SelectOption(label="St. Thomas More College", value="St. Thomas More College")
        ]
        super().__init__(placeholder="Select your University in Saskatchewan", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        if role is not None:
            await interaction.response.send_message(f"Your selected university is: {self.values[0]}")
            await interaction.user.add_roles(role)








@bot.tree.command(name='select')
async def select(interaction: discord.Interaction):
    embed = discord.Embed(title="Select your University and Interests", description="Please choose your university and interests from the dropdown menus below.", color=0x00ff00)
    view = UniversityAndInterestView()
    viewRest = UniversityAndInterestViewRest()

    await interaction.channel.send(embed=embed, view=view)
    await interaction.channel.send(view=viewRest)






class Event:
    def __init__(self, time, roles, title, description):
        self.time = time
        self.roles = roles
        self.title = title
        self.description = description
        self.reminded = False

# List of events
events = []

async def send_embed(guild, channel_name, title, description, event, color):
    # Get the server and channel
    channel = discord.utils.get(guild.channels, name=channel_name) 

    # Create role mentions
    role_mentions = [f"<@&{role.id}>" for role in event.roles]

    # Create the embed
    embed = discord.Embed(title=title, description=description, color=color)
    embed.add_field(name=event.description, value=", ".join(role_mentions), inline=False)
    embed.set_thumbnail(url="https://media.licdn.com/dms/image/C4E0BAQFZ83Q-ryJyYw/company-logo_200_200/0/1612553017924?e=2147483647&v=beta&t=gQtTxgENMUZilwaIRFW-UVbVkEdX0W7HdhFmDXj5Kng")

    # Send the message
    await channel.send(embed=embed)

@tasks.loop(seconds=60)  # run this every 60 seconds
async def check_events():
    guild = discord.utils.get(bot.guilds, name='Computing Councils of Canada - Internal')

    for event in events:
        if event.time - timedelta(hours=1) <= datetime.now() <= event.time and not event.reminded:
            await send_embed(guild, 'bot-test', "⏰ Event Reminder ⏰", f"The event {event.title} is starting in 1 hour!", event, 0x1a384c)
            event.reminded = True

        elif datetime.now() >= event.time:
            await send_embed(guild, 'bot-test', "⏰ Event Reminder ⏰", f"The event {event.title} is starting NOW!", event, 0x1a384c)
            # Remove the event from the list
            events.remove(event)


# For notifying about club meetings, coding competitions,
# hackathons, guest lectures, workshops, etc.
@bot.tree.command(name='queue_event',description="queue an event")
async def queue_event(interaction: discord.Interaction, event_time: str, roles: str, title: str, description: str):
    guild = discord.utils.get(bot.guilds, name='Computing Councils of Canada - Internal')

    # Parse the event time
    event_time = datetime.strptime(event_time, "%Y-%m-%d %H:%M")  # format: "YYYY-MM-DD HH:MM"

    # Get roles from string
    role_ids = [role.strip().replace("<@&","").replace(">","") for role in roles.split(" ")]
    guild_roles = interaction.guild.roles
    roles = [role for role in guild_roles if str(role.id) in role_ids]

    # Create a new event
    event = Event(event_time, roles, title, description)

    # Add the event to the list
    events.append(event)

    # Send the embed
    await send_embed(guild, 'bot-test', "⏰ Event Created ⏰", f"The event {event.title} has been scheduled for " + event.time.strftime("%A, %b. %d at %I:%M%p") + ".", event, 0x1a384c)

@bot.tree.command(name='clear')
@commands.has_permissions(administrator=True)  # only allow administrators to run this command
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.send_message(f"Cleared {amount} messages from this channel.")
    await interaction.channel.purge(limit=amount+1,check=lambda m: m.author != bot.user)

@bot.tree.command(name='mute')
@commands.has_permissions(administrator=True)  # only allow administrators to run this command
async def mute(ctx: discord.Interaction, member: discord.Member):
    mute_role = discord.utils.get(ctx.guild.roles, name='Muted')  # assuming 'Muted' role exists
    await member.add_roles(mute_role)
    await ctx.response.send_message(f"{member.mention} has been muted.")

@bot.tree.command(name='ban')
@commands.has_permissions(administrator=True)  # only allow administrators to run this command
async def ban(ctx: discord.Interaction, member: discord.Member, reason: str = None):
    await member.ban(reason=reason)
    await ctx.response.send_message(f"{member.mention} was banned.")

@bot.tree.command(name='kick')
@commands.has_permissions(administrator=True)  # only allow administrators to run this command
async def kick(ctx: discord.Interaction, member: discord.Member, reason: str = None):
    await member.kick(reason=reason)
    await ctx.response.send_message(f"{member.mention} was kicked.")

@bot.tree.command(name='userinfo')
async def userinfo(ctx: discord.Interaction, member: discord.Member):
    roles = [role for role in member.roles]
    embed = discord.Embed(color=member.color, timestamp=datetime.utcnow())
    embed.set_author(name=f"User Info - {member}")
    embed.set_thumbnail(url=member.avatar)
    embed.add_field(name="ID:", value=member.id)
    embed.add_field(name="Guild name:", value=member.display_name)
    embed.add_field(name="Created at:", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))
    embed.add_field(name="Joined at:", value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))
    embed.add_field(name=f"Roles ({len(roles)})", value=" ".join([role.mention for role in member.roles if role.name != "@everyone"]))
    embed.add_field(name="Top role:", value=member.top_role.mention)
    embed.add_field(name="Bot?", value=member.bot)
    await ctx.response.send_message(embed=embed)


@bot.tree.command(name='roll', description='Roll a dice')
async def roll(interaction: discord.Interaction, *, dice: str):
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await interaction.response.send_message('Format has to be in NdN!', ephemeral=True)
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))

    embed = discord.Embed(
        title="🎲 Dice Roll 🎲",
        description=f"You rolled: {result}",
        color=0x1a384c
    )
    embed.set_thumbnail(url="https://media.licdn.com/dms/image/C4E0BAQFZ83Q-ryJyYw/company-logo_200_200/0/1612553017924?e=2147483647&v=beta&t=gQtTxgENMUZilwaIRFW-UVbVkEdX0W7HdhFmDXj5Kng")
    embed.set_footer(text=f"Roll made by {interaction.user.name}")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='ping', description='latency check command')
async def ping(interaction: discord.Interaction):
    bot_latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'Latency: {bot_latency}ms')



@bot.tree.command(name='say', description='say command')
async def say(interaction: discord.Interaction, *, message: str):
    await interaction.response.send_message(message)

# admin only command to create channels


@bot.tree.command(name='create', description='create channel command')
@commands.has_permissions(administrator=True)
async def create(interaction: discord.Interaction, *, name: str):
    await interaction.response.send_message(f'Creating channel: {name}')
    await interaction.guild.create_text_channel(name)

# admin only command to delete channels


@bot.tree.command(name='delete', description='delete channel command')
@commands.has_permissions(administrator=True)
async def delete(interaction: discord.Interaction, *, name: str):
    await interaction.response.send_message(f'Deleting channel: {name}')
    channel = discord.utils.get(interaction.guild.channels, name=name)
    await channel.delete()
 
# admin only command to create roles


@bot.tree.command(name='createrole', description='create role command')
@commands.has_permissions(administrator=True)
async def createrole(interaction: discord.Interaction, *, name: str):
    await interaction.response.send_message(f'Creating role: {name}')
    await interaction.guild.create_role(name=name)

# admin only command to delete roles


@bot.tree.command(name='deleterole', description='delete role command')
@commands.has_permissions(administrator=True)
async def deleterole(interaction: discord.Interaction, *, name: str):
    await interaction.response.send_message(f'Deleting role: {name}')
    role = discord.utils.get(interaction.guild.roles, name=name)
    await role.delete()

@bot.tree.command(name='addrole')
@commands.has_permissions(manage_roles=True)  # only allow users with role management permissions to run this command
async def add_role(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"Role {role.name} added to {member.display_name}.")

@bot.tree.command(name='removerole')
@commands.has_permissions(manage_roles=True)  # only allow users with role management permissions to run this command
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f"Role {role.name} removed from {member.display_name}.")



bot.run(TOKEN)
