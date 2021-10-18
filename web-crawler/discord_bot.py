import os, re, time, json, discord
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from datetime import datetime

if os.name == 'posix':
    os.environ['TZ'] = 'Asia/Taipei'
    time.tzset()

def readenv():
    if not os.path.isfile('.env'):
        return {}

    result = {}
    file_object = open('.env', 'r', encoding="utf-8")
    while True:
        line = file_object.readline()
        if not line:
            break

        center_point = line.find('=')
        name = line[0:center_point]
        value = line[(center_point + 1):]
        
        result[name] = value

    file_object.close()
    return result

def storeLog(content):
    global time
    now_time = time.time()
    format_date = datetime.fromtimestamp(now_time).strftime('%Y-%m-%d')
    format_time = datetime.fromtimestamp(now_time).strftime('%H:%M:%S')
    file_object = open('./logs/discord_bot_%s.log'%(format_date), 'a', encoding="utf-8")
    file_object.write('[%s] %s\n'%(format_time, content))
    file_object.close()

envs = readenv()

# 背景執行瀏覽器
options = uc.ChromeOptions()
options.add_argument('--disable-gpu') # for headless
options.add_argument('--disable-dev-shm-usage') # uses /tmp for memory sharing
options.add_argument('--no-sandbox')
options.add_argument('--headless')
options.add_argument('--disable-setuid-sandbox')
driver = uc.Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), options=options)

# client 是我們與Discord連結的橋樑
client = discord.Client()

#調用event函式庫
@client.event
#當機器人完成啟動時
async def on_ready():
    print('目前登入身份：', client.user)
    activity = discord.Activity(name="!Server Riallaro 查詢伺服器狀態", type=discord.ActivityType.listening)
    await client.change_presence(status=discord.Status.online, activity=activity)

@client.event
# 當有訊息時
async def on_message(message):
    catch_time = time.time()
    # 排除自己的訊息，避免陷入無限循環
    if message.author == client.user:
        return

    # match 指令 !server
    match_objs = re.match('^!(S|s)erver (.*)$', message.content)
    if match_objs:
        game_server_name = match_objs[2]
        discord_message = await message.channel.send('查詢 ' + game_server_name + ' 的伺服器狀態中...')

        if isinstance(message.channel, discord.TextChannel):
            commander = '伺服器: %s, 群組: %s, 頻道: %s, 查詢者: %s, 內容: %s'%(message.channel.guild, message.channel.category, message.channel, message.author.name, message.content)
            print(commander)
            storeLog(commander)
        else:
            commander = '查詢者: %s, 內容: %s'%(message.author.name, message.content)
            print(commander)
            storeLog(commander)

        driver.get('https://newworldstatus.com/')

        # 用 javascript 解析目標資料
        script = 'function findNodeByXPath(e,n){var t=new XPathEvaluator,o=e+"[contains(translate(., \'ABCDEFGHIJKLMNOPQRSTUVWXYZ\', \'abcdefghijklmnopqrstuvwxyz\'),\'"+n+"\')]";return t.evaluate(o,document.documentElement,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null)}var content,world_name="' + game_server_name + '",result=findNodeByXPath("//strong",world_name.toLowerCase());result.singleNodeValue?(server_infos=result.singleNodeValue.parentNode.parentNode.innerText.split("\t"),server_location=server_infos[3],timezone=findNodeByXPath("//strong",server_location.toLowerCase()),now_time=timezone.singleNodeValue.parentNode.lastElementChild.innerText.split(", ")[1],server_infos.push(now_time),content=server_infos.join(",")):content="empty";return content;'

        # 這邊每一秒鐘看一下網頁長好了沒，直到逾時
        count = 0
        while True:
            result = driver.execute_script(script)
            if result != 'empty':
                break
            if (time.time() - catch_time) >= 15:
                msg = '本次查詢超過 %.1f 秒，找不到指定世界 %s 的資料'%((time.time() - catch_time), game_server_name)
                print(msg)
                storeLog(msg)
                await discord_message.edit(content=msg)
                return
            count += 1
            time.sleep(1)
        
        arr = result.split(',')

        if len(arr) != 8:
            msg = '解析陣列長度的結果與預期長度不符，可能是查詢來源有異動，請通知作者'%(count, game_server_name)
            print(msg)
            storeLog(msg)
            await discord_message.edit(content=msg)
            return

        world_status, world_name, world_set, location, now_players, in_queue, average_wait, current_time = arr

        # 處理嵌入內容
        embed = discord.Embed()

        embed.set_author(name='New World Server Status & Population', url='https://newworldstatus.com/', icon_url='http://i.imgur.com/lDF4O4s.jpg') # https://imgur.com/a/paxI6xX
        embed.title = '%s 的伺服器狀態'%(world_name)
        embed.url = 'https://newworldstatus.com/' #This URL will be hooked up to the title of the embed
        # embed.description = ''

        embed.add_field(name='狀態', value=world_status, inline=True)
        embed.add_field(name='%s 時間'%(location[0:location.find('(') - 1]), value=current_time, inline=True)
        embed.add_field(name='世界集', value=world_set, inline=True)

        embed.add_field(name='線上人數', value=str(now_players), inline=True)
        embed.add_field(name='排隊人數', value=str(in_queue), inline=True)
        embed.add_field(name='預估等待時間', value=average_wait, inline=True)

        embed.timestamp = datetime.utcnow()
        embed.set_footer(text='查詢耗時 %.1f 秒 • 解析耗時 %d 秒'%((time.time() - catch_time), count))
        embed.color = 15548997 # red
        if int(now_players) >= 1990:
            embed.color = 16705372 # yellow
        if world_status == 'LIVE':
            embed.color = 5763719 # green
        if world_status == 'UNKNOWN':
            embed.color = 9807270 # grey

        content = "查詢耗時: %.1f 秒\n解析耗時: %d\n%s 狀態 [**%s**]\n世界時間: %s - %s\n遊玩人數: %s\n排隊人數: %s\n預估時間: %s"%((time.time() - catch_time), count, world_name, world_status, current_time, location, str(now_players), str(in_queue), average_wait)
        print(content)
        storeLog(content)
        await discord_message.delete()
        await message.channel.send(embed=embed)

client.run(envs['DISCORD_BOT_TOKEN']) # from env