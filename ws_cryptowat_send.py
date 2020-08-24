import json
import time
from datetime import datetime
from websocket import create_connection
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import threading

from services.cryptowatcli import cryptowat_request

periods = 300
size = 39 * 12


clients = []


class SimpleEcho(WebSocket):
    def handleMessage(self):
        for client in clients:
            if client != self:
                client.sendMessage(self.data)

    def handleConnected(self):
        # print(self.address, 'connected')
        # for client in clients:
        #     client.sendMessage(self.address[0] + u' - connected')
        clients.append(self)

    def handleClose(self):
        clients.remove(self)
        # print(self.address, 'closed')
        # for client in clients:
        #     client.sendMessage(self.address[0] + u' - disconnected')


class ClientThread(threading.Thread):
    def __init__(self):
        super(ClientThread, self).__init__()

    def run(self):
        time.sleep(4)
        while True:
            after = int(datetime.now().timestamp() - (periods * size))
            data = cryptowat_request(periods, after)
            # data = datetime.now().isoformat()

            print(len(data))
            ws = create_connection("ws://localhost:8000/all")
            ws.send(json.dumps(data))
            ws.close()

            time.sleep(1)
            ws = create_connection("ws://localhost:8000/recent")
            ws.send(json.dumps(data[-1]))
            ws.close()
            time.sleep(60 * 10)


if __name__ == "__main__":
    ws = SimpleWebSocketServer('', 8000, SimpleEcho)
    client = ClientThread()
    client.start()
    ws.serveforever()
