import websockets
import asyncio
import json
import sqlite3
import time

async def handler(websocket):
    while True:
        conn = sqlite3.connect('maindb.db')
        cursor = conn.cursor()
        message = await websocket.recv()
        dictionary = json.loads(message)
        print(dictionary)


async def main():
    server = await websockets.serve(handler, "localhost", 5001)
    print("WebSocket server started on ws://localhost:5001")
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
