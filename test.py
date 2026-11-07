import socket
import json

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 5555))

def send_msg(data):
    client.send((json.dumps(data) + "\n").encode("utf-8"))
    response = client.recv(4096).decode("utf-8")
    print("SERVER REPLIED:", response)

# 1. Test logging in over the network
send_msg({"action": "signin", "username": "noam", "password": "1234"})

# 2. Test creating a table over the network
send_msg({"action": "create_table", "table_name": "High Stakes"})

client.close()





