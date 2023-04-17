from client import Client
import threading

def client_thread(client):
    client.send_request()

# create multiple client instances
clients = [Client("Client1"), Client("Client2"), Client("Client3")]

# create multiple client threads
threads = []
for client in clients:
    t = threading.Thread(target=client_thread, args=(client,))
    threads.append(t)
    t.start()

# wait for all threads to finish
for t in threads:
    t.join()