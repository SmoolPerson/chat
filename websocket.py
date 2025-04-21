from websockets import serve, ConnectionClosedOK, ConnectionClosedError, broadcast
import asyncio
import json
import sqlite3
import time
clientUsernameDict = {}

# self explanatory name
def update_message_db(username, message, recipient):
    # insert all info into db
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messageList (timestamp, username, recipient, message) VALUES (?, ?, ?, ?)", (time.time(), username, recipient, message))
    conn.commit()
    conn.close()

# same as function in app.py
def authorize(authToken):
    if authToken == None:
        return None
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM authTokenList WHERE authToken = ?", (authToken,))
    fetched = cursor.fetchall()
    conn.commit()
    conn.close()
    if fetched == []:
        return None
    return fetched[0][1]

# converts the tuple format returned by cursor.fetchall() to json string format
def convert_to_json(list_of_tuples):
    output_list = []
    for item in list_of_tuples:
        output_list.append({"username": item[1], "message":  item[3], "recipient": item[2]})
    output_string = json.dumps(output_list)
    return output_string

# loads the current messageList when the client switches to a chat
async def load_msg(websocket, recipient, username):
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    if recipient == "everyone":
        cursor.execute("SELECT * FROM messageList WHERE (recipient = 'everyone') ORDER BY timestamp ASC")
    else:
        # check if message is exchanged between client and recipient
        cursor.execute("SELECT * FROM messageList WHERE ((username = ? AND recipient = ?) OR (recipient = ? AND username = ?)) ORDER BY timestamp ASC", (username,recipient,username,recipient))
    fetched = cursor.fetchall()
    conn.commit()
    conn.close()
    fetchedmessages = "init " + convert_to_json(fetched)
    # send the fetched messages to websocket
    await websocket.send(fetchedmessages)
    # update the people online
    broadcast(clientUsernameDict.values(), "peopleonline " + str(len(clientUsernameDict.values())))

async def init_dm(websocket, username):
    print('test')
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    # select the recipient based on when they were last messaged
    cursor.execute("SELECT recipient, MAX(timestamp) AS time FROM messageList WHERE username = ? GROUP by recipient ORDER BY time DESC", (username,))
    fetched = cursor.fetchall()
    cursor.execute("SELECT username, MAX(timestamp) AS time FROM messageList WHERE recipient = ? GROUP by recipient ORDER BY time DESC", (username,))
    fetched += cursor.fetchall()
    print(fetched)
    recipient_set = []
    for item in fetched:
        # select just the first item (recipient) from the SQL query
        recipient_set.append(item[0])
    recipient_set = list(dict.fromkeys(recipient_set))
    print(recipient_set)
    json_obj = "initdm" + json.dumps(list(recipient_set))
    await websocket.send(json_obj)

async def send_msg(username, message, recipient):
    # update the message database with the new message sent
    update_message_db(username, message, recipient)
    broadcastobj = {"username": username, "message": message, "intendedreceiver": recipient}
    # broadcast message to all clients if recipient is everyone
    if recipient == 'everyone':
        broadcast(clientUsernameDict.values(), json.dumps(broadcastobj))
    else:
        # if recipinet is online, send message, send it back to client always
        broadcast([clientUsernameDict[username]], json.dumps(broadcastobj))
        if recipient in clientUsernameDict.keys():
            broadcast([clientUsernameDict[recipient]], json.dumps(broadcastobj))

async def handler(websocket):
    try:
        while True:
            receivedmessage = await websocket.recv()
            purpose = "send"
            if receivedmessage[0:7] == "loadmsg":
                # client requesting for initial message load
                receivedmessage = receivedmessage[7:]
                purpose = "load"
            if receivedmessage[0:6] == "initdm":
                # client requesting for initial dm load
                receivedmessage = receivedmessage[6:]
                print(receivedmessage)
                purpose = "initdm"
            dictionary = json.loads(receivedmessage)
            message = dictionary.get("message")
            authToken = dictionary.get("authToken")
            recipient = dictionary.get("recipient")
            # authorize authToken to get username
            username = authorize(authToken)

            if (username == None): # if the username doesnt exist, throw an error
                await websocket.send("invalidCookieError")
                continue

            # add username to dict pairing clients to websockets
            if username not in clientUsernameDict.keys():
                clientUsernameDict[username] =  websocket
                
            if purpose == "send":
                print("sending message")
                await send_msg(username, message, recipient)
                        
            elif purpose == "load":
                print("loading message")
                # if init is true, then initialize client with initial messages
                await load_msg(websocket, recipient, username)

            elif purpose == "initdm":
                print("loading dms")
                await init_dm(websocket, username)

        
    except ConnectionClosedOK or ConnectionClosedError:
        # if the connection ends for whatever reason, remove it from the dict and rebroadcast ppl online
        for item in clientUsernameDict.copy().items():
            # if the value matches up, remove the key
            if item[1] == websocket:
                del clientUsernameDict[item[0]]
        broadcast(clientUsernameDict.values(), "peopleonline " + str(len(clientUsernameDict.values())))


async def main():
    server = await serve(handler, "localhost", 5001)
    print("WebSocket server started on ws://localhost:5001")
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
