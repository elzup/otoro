import json
import time
from datetime import datetime
from websocket import create_connection
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import threading

from services.cryptowatcli import cryptowat_request

clients = []
cache = False


class SimpleEcho(WebSocket):
    def handleMessage(self):
        for client in clients:
            if client != self:
                client.sendMessage(self.data)

    def handleConnected(self):
        global cache
        # print(self.address, 'connected')
        clients.append(self)
        if cache:
            print(f'new client {str(len(clients))}')
            for client in clients:
                client.sendMessage(cache)

    def handleClose(self):
        clients.remove(self)
        # print(self.address, 'closed')
        # for client in clients:
        #     client.sendMessage(self.address[0] + u' - disconnected')


class ClientThread(threading.Thread):
    def __init__(self):
        super(ClientThread, self).__init__()

    def run(self):
        global cache
        time.sleep(4)
        print('start')
        while True:
            t = datetime.now().timestamp()
            after = int(t - (300 * 39 * 12))
            m5data = cryptowat_request(300, after)
            after = int(t - (3600 * 60))
            h1data = cryptowat_request(3600, after)

            ws = create_connection("ws://localhost:8000/all")
            cache = json.dumps({"m5": m5data, "h1": h1data})
            ws.send(cache)

            ws.close()
            time.sleep(60 * 5)


if __name__ == "__main__":
    ws = SimpleWebSocketServer('', 8000, SimpleEcho)
    client = ClientThread()
    client.start()
    ws.serveforever()
