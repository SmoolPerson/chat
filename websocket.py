import websockets
import asyncio
import json
import sqlite3
import time
clientSet = set()

def update_message_db(username, message):
    conn = sqlite3.connect('maindb.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messageList (timestamp, username, message) VALUES (?, ?, ?)", (time.time(), username, message))
    cursor.execute("SELECT * FROM messageList ORDER BY time ASC")
    allitems = cursor.fetchall()
    if len(allitems) > 50:
        valuetoremove = allitems[0][1]
        cursor.execute("DELETE FROM messageList WHERE username = ?", (valuetoremove,))

async def handler(websocket):
    while True:
        conn = sqlite3.connect('maindb.db')
        cursor = conn.cursor()
        clientSet.add(websocket)
        receivedmessage = await websocket.recv()
        if receivedmessage == "loadmsg":
            print("client requesting for initial message load")
            cursor.execute("SELECT * FROM messageList ORDER BY timestamp ASC")
            fetchedmessages = cursor.fetchall()
            sendobj = [dict(item[1], item[2]) for item in fetchedmessages]
            print(json.dumps(sendobj))
        else:            
            dictionary = json.loads(receivedmessage)
            message = dictionary.get("message")
            authToken = dictionary.get("authToken")

            cursor.execute("SELECT * FROM authTokenList WHERE authToken = ?", (authToken,))
            fetched = cursor.fetchall()
            conn.commit()
            conn.close()

            if (fetched == [] or authToken == None):
                await websocket.send("Invalid cookie. Try logging in again")
            else:
                conn = sqlite3.connect('maindb.db')
                cursor = conn.cursor()
                username = fetched[0][1]

                cursor.execute("INSERT INTO messageList (timestamp, username, message) VALUES (?, ?, ?)", (time.time(), username, message))
                cursor.execute("SELECT * FROM messageList ORDER BY timestamp ASC")
                allitems = cursor.fetchall()

                if len(allitems) > 50:
                    valuetoremove = allitems[0][0]
                    cursor.execute("DELETE FROM messageList WHERE timestamp = ?", (valuetoremove,))

                broadcastobj = {"username": username, "message": message}
                websockets.broadcast(clientSet, json.dumps(broadcastobj))
                cursor.execute("SELECT * FROM messageList")

                conn.commit()
                conn.close()


async def main():
    server = await websockets.serve(handler, "localhost", 5001)
    print("WebSocket server started on ws://localhost:5001")
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
