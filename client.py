import socket
import os
from threading import Thread


def listen_for_messages(server_socket):

    while True:
        message = server_socket.recv(1024).decode("utf-8")
        if message == "The game has started. Press Enter to hit the bell.":
            os.system('cls' if os.name == 'nt' else 'clear')

        print(message)

def create_client(host, port):

    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.connect((host, port))

    message_listener = Thread(target=listen_for_messages, args=(my_socket,))
    message_listener.daemon = True 
    message_listener.start()

    while True:
        user_input = input()

        if user_input == "q":
            my_socket.close()
            break

        elif user_input == "":
            a = "ready"
            my_socket.send(a.encode("utf-8"))

if __name__ == "__main__":
    host = "192.168.50.101" 
    port = 11111 

    create_client(host, port)
