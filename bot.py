import requests
import asyncio  
import discord
import json
import time

client = discord.Client()
channel, task, delay, lo, hi, talk = None, None, None, None, None, True

@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------------")

@client.event
async def on_message(message):
    global task, channel, client, delay, lo, hi, talk
    content = message.content
    args = content.split(" ")
    print(content)

    if content.startswith("!price"):
        r = requests.get("https://bitgrail.com/api/v1/BTC-XRB/ticker") 
        j = json.loads(r.text)
        price = float(j["response"]["ask"])
        await client.send_message(message.channel, "price is "+str(price))
    
    elif content.startswith("!delay"): 
        delay = int(args[1])

    elif content.startswith("!lo"): 
        lo = float(args[1])

    elif content.startswith("!hi"): 
        hi = float(args[1])

    elif content.startswith("!talk"): 
        talk = not talk

    elif content.startswith("!monitor"): 
        if not task: 
            print("Creating task")
            delay, lo, hi = int(args[1]), float(args[2]), float(args[3])
            talk = len(args) > 4 and args[4] == "talk"

            task = client.loop.create_task(background_loop())
    
    elif content.startswith("!stop"): 
        if task:
            print("Stopping task")
            await client.send_message(channel, "Stopping monitor")
            task.cancel()
            task = None

    elif message.content.startswith("!sleep"):
        await asyncio.sleep(5)
        await client.send_message(message.channel, "Done sleeping")

async def background_loop():
    global channel, client, delay, lo, hi, talk
    peak = None
    peakTime = None

    while not channel: 
        await client.wait_until_ready()
        channel = client.get_channel("CHANNEL_ID")
        await asyncio.sleep(20)

    await client.send_message(channel, "Starting monitor")

    while not client.is_closed:

        print("Querying", end=" ")
        r = requests.get("https://bitgrail.com/api/v1/BTC-XRB/ticker") 
        j = json.loads(r.text) 
        price = float(j["response"]["ask"]) 
        print("price={}".format(price), end=" ")

        if not peak: peak = price
        if not peakTime: peakTime = time.time()
        delta = peak - price
        if delta > 0.00002000: 
            currentTime = time.time()
            await client.send_message(channel, "dropped by {} satoshis".format(int(delta * 100000000)), tts = talk) 
            await client.send_message(channel, "from {0:.8f}[{1}s ago] -> {2:.8f}".format(peak, 12, price)) 
            peak = price
            peakTime = currentTime
        elif delta < 0:
            peak = price
            peakTime = time.time()
        print("peak={}".format(peak))
            
        if price < lo: 
            await client.send_message(channel, "price {0:.8f} has DROPPED below lower threshold".format(price), tts = talk)
        elif price > hi:
            await client.send_message(channel, "price {0:.8f} has EXCEEDED upper threshold".format(price), tts = talk)

        await asyncio.sleep(delay)
        
client.run("BOT_KEY")
