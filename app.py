from flask import Flask, request, send_file, jsonify
from flask_pymongo import PyMongo
from bson import json_util
import json
import requests
import random
import string
import Constant

global room_map
room_map = dict()
global roles
roles = ['']*5
roles.append('Werewolf Doctor Seer Hunter Villager')
roles.append('Werewolf Doctor Seer Hunter Villager Villager')
roles.append('Werewolf Doctor Seer Hunter Villager Villager Villager')
roles.append('Werewolf Doctor Seer Hunter Villager Villager Villager Villager')
roles.append('Werewolf Doctor Seer Hunter Villager Villager Villager Villager Villager')
roles.append('Werewolf Doctor Seer Hunter Villager Villager Villager Villager Villager Villager')

global desc
desc = dict()
desc['Werewolf'] = 'ทีม [Warewolf] \uDBC0\uDC5E\n    มี Active Ability ในช่วงกลางคืน สามารถเลือกฆ่าใครก็ได้ 1 คน|\uDBC0\uDC77 Tip!\n    พยายามหลบหนีการสงสัย การถูกจับจากคนอื่นๆ (โกหก) ให้อยู่รอดจนเหลือ 2 คนสุดท้ายในวง (รวมหมาป่า) และคนที่เหลือไม่ใช่ Hunter จึงจะถือว่าชนะ!'
desc['Doctor'] = 'ทีม [Villager] \uDBC0\uDC90\n    มี Active Ability ในช่วงกลางคืน สามารถเลือกช่วยชีวิตใครก็ได้ 1 คน รวมทั้งตัวเองด้วย|\uDBC0\uDC77 Tip!\n    พยายามเลือกช่วยคนที่มีแนวโน้มจะโดนหมาป่าฆ่า เช่น "พูดมาก" เป็นต้น'
desc['Seer'] = 'ทีม [Villager] \uDBC0\uDC90\n    มี Active Ability ในช่วงกลางคืน สามารถชี้ถามใครก็ได้ 1 คน ว่าเป็นหมาป่าหรือไม่?|\uDBC0\uDC77 Tip!\n    พยายามเลือกชี้หมาป่าให้ได้เร็วที่สุด และ พยายามไม่พูดมากจนหมาป่ารู้ว่าเป็น Seer เพราะจะโดนฆ่า'
desc['Hunter'] = 'ทีม [Villager] \uDBC0\uDC90\n   มี Passive Ability คือถ้าสามารถอยู่รอดจนเหลือ 2 คนสุดท้ายในวง (รวมหมาป่า) ได้ จะสามารถสู้กับหมาป่าได้และทำให้ทีม [Villager] เป็นผู้ชนะ!|\uDBC0\uDC77 Tip!\n    พยายามทำตัวนิ่งๆ ให้รอจบเกมก็พอ อย่าให้โดนฆ่าระหว่างก่อนจบเกม หรือ พยายามบอกให้ หมอ ช่วย'
desc['Villager'] = 'ทีม [Villager] \uDBC0\uDC90\n   ทำอะไรไม่ได้นอกจากบัฟคนอื่นและช่วยหาหมาป่า \uDBC0\uDC95|\uDBC0\uDC77 Tip!\n    พยายามช่วยทีมละกันนะ สู้ๆ 5555'

global LINE_API_KEY
LINE_API_KEY = 'Bearer ' + Constant.Token

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'werewolf'
app.config['MONGO_URI'] = Constant.MONGO_URI

mongo = PyMongo(app)

@app.route('/')
def index():
    room_model = mongo.db.rooms
    rooms = room_model.find({'id': '1111'})
    data = [json.dumps(r, default=json_util.default) for r in rooms]
    return jsonify(data=data)

@app.route('/img')
def img():
    filename = 'img/'+request.args.get('role')+'.jpg'
    return send_file(filename, mimetype='image/jpeg')

@app.route('/bot', methods=['POST'])
def bot():
    #locked = getLockingStatus()
    room_model = mongo.db.rooms
    player_model = mongo.db.players
    replyStack = []
    msg_in_json = request.get_json()
    msg_in_string = json.dumps(msg_in_json)
    replyToken = msg_in_json["events"][0]['replyToken']

    userID =  msg_in_json["events"][0]['source']['userId']
    name = getProfiles(userID)['displayName']
    msgType =  msg_in_json["events"][0]['message']['type']
    
    if msgType != 'text':
        reply(replyToken, ['Only text is allowed.'])
        return 'OK',200
    
    text = msg_in_json["events"][0]['message']['text'].lower().strip()
    words = text.split()
    '''
    if text in ['!lock','!locked']:
        lock()
        pushSticker(userID,"1","408")
        reply(replyToken, ['See you! chatbot is locked.'])
        return 'OK',200

    if locked:
        if text == 'qwertyasd11':
            unlock()
            pushSticker(userID,"2","144")
            reply(replyToken, ['Yay! chatbot is ready.'])
            return 'OK',200
        pushSticker(userID,"2","39")
        replyStack.append('Chatbot is locked!')
        replyStack.append('Passcode needed.')
        reply(replyToken, replyStack)
        return 'OK',200
    '''
    if words[0] in ['create', 'สร้าง', 'สร้างห้อง']:
        new_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
        while room_model.find_one({'id': new_id}!=None):
            new_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
        newroom_id = room_model.insert({'id': new_id, 'creator': name, 'status': 'waiting'})
        room_map[userID] = new_id
        replyStack.append('Your room id is : ' + new_id)
        reply(replyToken, replyStack)
        return 'OK',200

    elif words[0] in ['join','play','เล่น','เล่นด้วย']:
        # Acknowledge all player that already in room.
        if words.length == 1:
            replyStack.append('Please specify a Room ID')
            reply(replyToken, replyStack)
            return 'OK',200
        if room_model.find_one({'id': words[1]}) == None:
            replyStack.append('This Room ID is invalid')
            reply(replyToken, replyStack)
            return 'OK',200
        room_map[userID] = words[1]
        number_of_player = countPlayer(words[1])+1
        players_in_room = player_model.find({'room': words[1]})
        for player in players_in_room:
            push(player['user_id'],[name +' has joined the room : ' + words[1] + '! ('+str(number_of_player)+')'])

        player_model.insert({'room': words[1], 'user_id': userID})
        replyStack.append('You have joined the room : ' + words[1] + '! ('+str(number_of_player)+')')
        reply(replyToken, replyStack)
        return 'OK',200

    elif words[0] in ['quit','เลิก','ออก','เลิกเล่น','ออกจากห้อง','พอ']:
        # Acknowledge all player that already in room.
        name = getProfiles(userID)['displayName']
        number_of_player = countPlayer()-1
        saved = list()
        with open('db/registered.txt','r') as data_file:
            for line in data_file:
                if line[:-1] == userID:
                    continue
                saved.append(line[:-1])
                push(line,[name +' has left the room! ('+str(number_of_player)+')'])
        open('db/registered.txt', 'w').close()

        # Acknowledge player that recently left the room.
        with open('db/registered.txt','a') as data_write:
            for player in saved:
                data_write.write(player+"\n")
        replyStack.append('You have left the room!')
        reply(replyToken, replyStack)
        return 'OK',200
        
    elif words[0] == '!reset':
        with open('db/registered.txt','r') as data_file:
            for line in data_file:
                pushSticker(userID,"2","23")
                push(line,['You have been kicked!'])
        open('db/registered.txt', 'w').close()
        return 'OK',200

    elif words[0] in ['ls','list','มีใครบ้าง','มีใครมั่ง']:
        lists = 'Users List\n'
        count = 0
        with open('db/registered.txt','r') as data_file:
            for line in data_file:
                if len(line) == 0:
                    continue
                count += 1
                try:
                    name = getProfiles(line[:-1])['displayName']
                    lists += "- " + name + "\n"
                except:
                    pass
        if lists == 'Users List\n':
            lists = 'Room is empty.'
        else:
            lists += str(count) + ' user(s) in room.'
        reply(replyToken, [lists])
        return 'OK',200
    elif words[0] in ['go','เริ่ม','เริ่มเล่น','เริ่มเกม','แจกไพ่','แจกเลย','แจก']:
        number_of_player = countPlayer()
        if number_of_player < 5:
            pushSticker(userID,"1","107")
            reply(replyToken, ['Sorry, minimum players is 5'])
            return 'OK',200
        role = roles[number_of_player].split()
        with open('db/registered.txt','r') as data_file:
            for line in data_file:
                draw = ''
                while len(draw) <= 0:
                    lucky = random.randrange(number_of_player)
                    draw = role[lucky]
                    role[lucky] = ''
                pushImage(line,draw)
                description = desc[draw].split('|')
                push(line,['\uDBC0\uDC35 '+draw+' \uDBC0\uDC35', description[0], description[1]])
        open('db/registered.txt', 'w').close()
        return '0K',200
    elif words[0] in ['เล่นยังไง','ทำยังไง','อะไรวะ','เล่นไง','ทำไง','help','?']:
        replyStack.append('\uDBC0\uDC77 How To Play?')
        replyStack.append('ผู้ที่ต้องการเล่นเกมให้พิมพ์คำว่า "เล่น" หรือ "join"')
        replyStack.append('ผู้ที่ต้องการออกจากเกมให้พิมพ์คำว่า "ออก" หรือ "quit"')
        replyStack.append('เมื่อคนเล่นครบ 5+ คนแล้วให้พิมพ์คำว่า "เริ่มเกม" หรือ "go"')
    else:
        replyStack.append('\uDBC0\uDC5E พิมพ์ ? เพื่อดูวิธีการใช้งาน')
    reply(replyToken, replyStack[:5])
    return 'OK',200

def countPlayer(roomId):
    count = player_model.find({'room': roomId}).count()
    return count
 
def getLockingStatus():
    with open('db/locked.txt','r') as data_file:
        for line in data_file:
            if line.strip() == 'unlocked':
                return False
    return True

def lock():
    open('db/locked.txt', 'w').close()
    return

def unlock():
    with open('db/locked.txt','a') as data_write:
            data_write.write('unlocked')
    return

def reply(replyToken, textList):
    LINE_API = 'https://api.line.me/v2/bot/message/reply'
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': LINE_API_KEY
    }
    msgs = []
    for text in textList:
        msgs.append({
            "type":"text",
            "text":text
        })
    data = json.dumps({
        "replyToken":replyToken,
        "messages":msgs
    })
    requests.post(LINE_API, headers=headers, data=data)
    return

def pushSticker(userID, packId, stickerId):
    LINE_API = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': LINE_API_KEY
    }
    msgs = [{
        "type": "sticker",
        "packageId": packId,
        "stickerId": stickerId
    }]
    data = json.dumps({
        "to": userID,
        "messages":msgs
    })
    requests.post(LINE_API, headers=headers, data=data)
    return
    
def pushImage(userID, role):
    LINE_API = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': LINE_API_KEY
    }
    msgs = [{
        "type": "image",
        "originalContentUrl": "https://werewolf-bot-server.herokuapp.com/img?role="+role,
        "previewImageUrl": "https://werewolf-bot-server.herokuapp.com/img?role="+role+"_p"
    }]
    data = json.dumps({
        "to": userID,
        "messages":msgs
    })
    requests.post(LINE_API, headers=headers, data=data)
    return
    

def push(userID, textList):
    LINE_API = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': LINE_API_KEY
    }
    msgs = []
    for text in textList:
        msgs.append({
            "type":"text",
            "text":text
        })
    data = json.dumps({
        "to": userID,
        "messages":msgs
    })
    requests.post(LINE_API, headers=headers, data=data)
    return

def getContent(id):
    LINE_API = 'https://api.line.me/v2/bot/message/'+str(id)+'/content'
    r = requests.get(LINE_API, headers={'Authorization': LINE_API_KEY})
    r = r.content
    return r

def getProfiles(id):
    LINE_API = 'https://api.line.me/v2/bot/profile/'+str(id)
    r = requests.get(LINE_API, headers={'Authorization': LINE_API_KEY})
    r = r.content
    return json.loads(r.decode('utf8'))

if __name__ == '__main__':
    app.run()