from websockets import serve, ConnectionClosedOK, ConnectionClosedError, broadcast
import asyncio
import json
import sqlite3
import time
clientSet = set()

def update_message_db(username, message):
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messageList (timestamp, username, message) VALUES (?, ?, ?)", (time.time(), username, message))
    cursor.execute("SELECT * FROM messageList ORDER BY timestamp ASC")
    allitems = cursor.fetchall()
    if len(allitems) > 50:
        valuetoremove = allitems[0][0]
        cursor.execute("DELETE FROM messageList WHERE timestamp = ?", (valuetoremove,))
    conn.commit()
    conn.close()

def authorize(authToken):
    if authToken == None:
        return None
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM authTokenList WHERE authToken = ?", (authToken,))
    fetched = cursor.fetchall()
    if fetched == []:
        return None
    return fetched[0][1]

def convert_to_json(list_of_tuples):
    output_list = []
    for item in list_of_tuples:
        output_list.append({"username": item[1], "message":  item[2]})
    output_string = json.dumps(output_list)
    return output_string

async def load_msg(websocket):
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM messageList ORDER BY timestamp ASC")
    fetchedmessages = "init " + convert_to_json(cursor.fetchall())
    await websocket.send(fetchedmessages)
    broadcast(clientSet, "peopleonline " + str(len(clientSet)))
    conn.commit()
    conn.close()

async def handler(websocket):
    try:
        while True:
            conn = sqlite3.connect('maindb.db')
            cursor = conn.cursor()
            clientSet.add(websocket)
            broadcast(clientSet, "peopleonline " + str(len(clientSet)))
            receivedmessage = await websocket.recv()
            if receivedmessage == "loadmsg":
                print("client requesting for initial message load")
                await load_msg(websocket)
            else:            
                dictionary = json.loads(receivedmessage)
                message = dictionary.get("message")
                authToken = dictionary.get("authToken")

                username = authorize(authToken)

                if (username == [] or username == None):
                    await websocket.send("invalidCookieError")
                else:
                    update_message_db(username, message)
                    broadcastobj = {"username": username, "message": message}
                    broadcast(clientSet, json.dumps(broadcastobj))
    except ConnectionClosedOK or ConnectionClosedError:
        clientSet.remove(websocket)
        broadcast(clientSet, "peopleonline " + str(len(clientSet)))


async def main():
    server = await serve(handler, "localhost", 5001)
    print("WebSocket server started on ws://192.168.1.242:5001")
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
