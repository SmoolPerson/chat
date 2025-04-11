from websockets import serve, ConnectionClosedOK, ConnectionClosedError, broadcast
import asyncio
import json
import sqlite3
import time
clientSet = set()

# self explanatory name
def update_message_db(username, message):
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messageList (timestamp, username, message) VALUES (?, ?, ?)", (time.time(), username, message))
    cursor.execute("SELECT * FROM messageList ORDER BY timestamp ASC")
    allitems = cursor.fetchall()
    if len(allitems) > 50: # the db only stores 50 messages, delete the oldest one when > 50 msgs are sent
        valuetoremove = allitems[0][0]
        cursor.execute("DELETE FROM messageList WHERE timestamp = ?", (valuetoremove,))
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
    if fetched == []:
        return None
    return fetched[0][1]

# converts the tuple format returned by cursor.fetchall() to json string format
def convert_to_json(list_of_tuples):
    output_list = []
    for item in list_of_tuples:
        output_list.append({"username": item[1], "message":  item[2]})
    output_string = json.dumps(output_list)
    return output_string

# loads the current messageList when the client connects to the websocket
async def load_msg(websocket):
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messageList ORDER BY timestamp ASC")
    fetchedmessages = "init " + convert_to_json(cursor.fetchall())
    # send the fetched messages to websocket
    await websocket.send(fetchedmessages)
    # update the people online
    broadcast(clientSet, "peopleonline " + str(len(clientSet)))
    conn.commit()
    conn.close()

async def handler(websocket):
    try:
        while True:
            conn = sqlite3.connect('maindb.db')
            cursor = conn.cursor()
            # add websocket to set of clients
            clientSet.add(websocket)
            receivedmessage = await websocket.recv()
            if receivedmessage == "loadmsg":
                # client requesting for initial message load
                await load_msg(websocket)
            else:
                dictionary = json.loads(receivedmessage)
                message = dictionary.get("message")
                authToken = dictionary.get("authToken")
                # authorize authToken to get username
                username = authorize(authToken)

                if (username == None): # if the username doesnt exist, throw an error
                    await websocket.send("invalidCookieError")
                else:
                    # update the message database with the new message sent
                    update_message_db(username, message)
                    broadcastobj = {"username": username, "message": message}
                    # broadcast message to all clients
                    broadcast(clientSet, json.dumps(broadcastobj))

    except ConnectionClosedOK or ConnectionClosedError:
        # if the connection ends for whatever reason, remove it from the set and rebroadcast ppl online
        clientSet.remove(websocket)
        broadcast(clientSet, "peopleonline " + str(len(clientSet)))


async def main():
    server = await serve(handler, "localhost", 5001)
    print("WebSocket server started on ws://localhost:5001")
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
