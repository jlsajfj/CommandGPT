import discord
from discord import app_commands
import os
from dotenv import load_dotenv
from litellm import completion

# Set up the intents
intents = discord.Intents.default()
intents.message_content = True  # For reading messages
intents.guild_messages = True  # For writing messages


# Create a client instance
class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


client = MyClient()


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")


@client.tree.command(name="hello", description="Says hello to you")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.name}!")


@client.tree.command(name="ping", description="Checks the bot's latency")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(f"Pong! Latency: {latency}ms")


@client.tree.command(
    name="summarize",
    description="Fetches and summarizes a specified number of messages from the current channel",
)
@app_commands.describe(
    count="Number of messages to summarize",
    ephemeral="Whether the response should be visible only to you",
)
async def summarize(
    interaction: discord.Interaction,
    count: app_commands.Range[int, 1, 100],
    ephemeral: bool = True,
):
    await interaction.response.defer(ephemeral=ephemeral)

    messages = [message async for message in interaction.channel.history(limit=count)]
    conversation = "\n".join(
        [f"{msg.author.name}: {msg.content}" for msg in messages[::-1]]
    )
    response = completion(
        model="claude-3-haiku-20240307",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes conversations between Discord users. You get all the key points but you are concise and to the point. Make sure to keep usernames accurate in your summary.",
            },
            {
                "role": "user",
                "content": f"Please summarize the following conversation:\n\n{conversation}",
            },
        ],
    )
    summary = response["choices"][0]["message"]["content"]
    await interaction.followup.send(summary, ephemeral=ephemeral)


@client.tree.command(
    name="search", description="Performs a search for the provided topic"
)
@app_commands.describe(
    topic="Topic to search",
    ephemeral="Whether the response should be visible only to you",
)
async def search(interaction: discord.Interaction, topic: str, ephemeral: bool = True):
    await interaction.response.defer(ephemeral=ephemeral)

    # Use ChatGPT to research the query
    response = completion(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that performs research on given topics. Please use the internet for the latest results. You provide important details but you are concise and to the point.",
            },
            {
                "role": "user",
                "content": f"Please provide a brief summary of information about: {topic}",
            },
        ],
    )

    research_result = response["choices"][0]["message"]["content"]

    # Send the research result back to the user
    await interaction.followup.send(
        f"Research results for `{topic}`:\n\n{research_result}", ephemeral=ephemeral
    )


# Load environment variables from .env file
load_dotenv()

# Get the bot token from the environment variable
client.run(os.getenv("BOT_TOKEN"))
