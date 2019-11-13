import discord
from discord.ext import commands

TOKEN = str(open("token.txt", 'r').read())

client = commands.Bot(command_prefix='?')
CONFIG = "config.txt"
MESSAGE_IDS = "message_ids.txt"
OWNER = 251402333731291139

#to be used when accessing the config file
#so it is more clear which settings are being used
CONFIG_SETTINGS = {
    "limit": 0,
    "mod_role": 1,
    "starboard_id": 2
}


def set_config(line, value):
    """
        set the configuration file to the specified value

        Arguments:
        line - the line to be changed
        value - the new value to set
    """
    org_lines = origin_lines(CONFIG)
    file = open(CONFIG, "w")
    org_lines[line] = str(value) + "\n"
    string=""
    for i in org_lines:
        string += i
    file.write(string)
    file.close()


def get_config(line):
    """return the setting at the specified line"""
    org_lines = origin_lines(CONFIG)
    return org_lines[line]


def get_starboard_id(message_id):
    """return the id of the message in starboard from the id of the original message"""
    lines = open(MESSAGE_IDS, 'r').readlines()
    for line in lines:
        ids = line.split(",")
        if message_id == int(ids[1].strip()):
            return int(ids[0])
    return -1


def get_starboard_line(message_id):
    """return the line containing the ids for the starboard message and the original message"""
    lines = open(MESSAGE_IDS, 'r').readlines()
    count = -1
    for line in lines:
        count += 1
        ids = line.split(",")
        if message_id == int(ids[1].strip()):
            return count
    return -1


def check(emoji):
    """return the limit before a message is starred if the emoji is a star
        otherwise return -1"""
    if(str(emoji) != "⭐"):
        return -1
    try:
        return int(get_config(CONFIG_SETTINGS["limit"]))
    except Exception:
        return -1
    return -1


def origin_lines(filename):
    """return the lines of a file"""
    origin = open(filename, 'r')
    org_lines = origin.readlines()
    origin.close()
    return org_lines


def is_mod(roles):
    """returns true if the person has the configured mods role"""
    mod_role = str(get_config(CONFIG_SETTINGS["mod_role"]))
    role_names = [role.name for role in roles]
    if((mod_role.lower() in role_names)):
        print("No permission")
        return True
    return False


def is_admin(roles):
    """returns true if the person has admin permissions on the server"""
    for role in roles:
        if(role.permissions.administrator):
            return True
    return False


@client.event
async def on_reaction_remove(reaction, user):
    """when a reaction is removed check to see if the starboard message should be deleted"""
    channel = reaction.message.channel
    LIMIT = check(reaction.emoji)
    if(LIMIT == -1): #this should never run
        await channel.send("{} pls help something has gone wrong")

    if(reaction.count < LIMIT):
        star_msg = get_starboard_id(int(reaction.message.id))
        if(star_msg == -1):
            print("message not found")
            return

        star_id = int(get_config(CONFIG_SETTINGS["starboard_id"]))
        star = client.get_channel(star_id)
        msg = await star.fetch_message(star_msg)
        await msg.delete()

        org_lines = origin_lines(MESSAGE_IDS)
        i = get_starboard_line(reaction.message.id)
        file = open(MESSAGE_IDS, 'w')
        string = ""
        for x in range(len(org_lines)):
            if x == i:
                continue  # we remove the deleted message from the file
            else:
                string += org_lines[x]
        file.write(string)
        file.close()


def create_embed(reaction, user):
    """returns an embed to be sent to the starboard channel"""
    channel = reaction.message.channel
    quote = discord.Embed(
        title="**Content**",
        description=reaction.message.content,
        url=reaction.message.jump_url,
        colour=0xFFAC33,
        timestamp=reaction.message.created_at)

    quote.add_field(name="**Author**", value=user.mention, inline=True)
    quote.add_field(name="**Channel**", value=channel.mention, inline=True)
    return quote


@client.event
async def on_reaction_add(reaction, user):
    """checks to see if a message needs to be sent to starboard"""
    channel = reaction.message.channel
    LIMIT = check(reaction.emoji)
    if(LIMIT == -1):
        await channel.send("{} pls help something has gone wrong".format(client.get_user(OWNER).mention))

    if(reaction.count >= LIMIT):
        # put in starboard channel
        quote = create_embed(reaction, user)

        stars_id = int(get_config(CONFIG_SETTINGS["starboard_id"]))
        stars = client.get_channel(stars_id)
        await stars.send(embed=quote)

        if(get_starboard_id(reaction.message.id) != -1):
            print("message already quoted")
            return

        file = open(MESSAGE_IDS, 'a')
        embed_id = stars.last_message_id
        string = "{},{}\n".format(embed_id, reaction.message.id)
        file.write(string)
        file.close()


@client.command()
async def set_limit(ctx, x: int):
    """sets the limit before a message will be sent to starboard
        can only be done by a mod or admin"""
    try:
        x = int(x)
    except Exception:
        await ctx.send("Parameter must be an integer")
        return

    if(x < 1):
        await ctx.send("Cannot set limit below 1")
        return

    roles = ctx.message.author.roles
    if(not (is_mod(roles) or is_admin(roles))):
        await ctx.send("You do not have permission please contact a mod or an admin")
        return

    set_config(CONFIG_SETTINGS["limit"], x)
    await ctx.send("New limit is {0}".format(x))


@client.command()
async def set_mod_role(ctx, role: str):
    """sets the name of the role for mods can only be done by an admin"""
    if(not is_admin(ctx.message.author.roles)):
        await ctx.send("You do not have permission please contact an admin")
        return

    set_config(CONFIG_SETTINGS["mod_role"], role.lower())
    await ctx.send("{} now has permission to edit config".format(role))


@client.command()
async def set_starboard(ctx, id: int):
    """sets the id of the starboard channel that highlighted messages should be sent to"""
    roles = ctx.message.author.roles
    if(not (is_mod(roles) or is_admin(roles))):
        await ctx.send("You do not have permission contact a mod or an admin")
    set_config(CONFIG_SETTINGS["starboard_id"], id)
    await ctx.send("starboard id set to {}".format(id))


@client.command()
async def greet(ctx):
    """A simple test command to ensure the bot is working"""
    await ctx.send("Hi am working thanks :smile:")


@client.event
async def on_ready():
    """prints when the bot has successfully logged in"""
    print("Logged in as:")
    print(client.user.name)
    print(client.user.id)
    print("-----")

client.run(TOKEN)
