import socket
from time import sleep
from enum import Enum
from threading import Lock, Thread
from halligalli_game import HalliGalli_Game

class ServerStatus(Enum):
    LOBBY_NOT_READY = 0
    LOBBY_READY = 1  
    STARTING_GAME = 2  
    IN_GAME = 3  
    PROCESSING_HIT = 4  
    GAME_OVER = 5


class HalliGalli_Player:
    def __init__(self, socket: socket.socket, address):
        self.socket = socket
        self.address = address
        self.player_number = 0
        self.isready = False

    def ready(self):
        self.isready = True
    
    def not_ready(self):
        self.isready = False

class HalliGalli_Server:
    def __init__(self, host, port):
        self.lock = Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.clients = []
        self.game_object = None 
        self.host_player = None
        self.hit_player = None
        self.players_by_number = {}

    def handle_client(self, player: HalliGalli_Player):

        print(f"Accepted connection from {player.address}")

        player.socket.send("Type q+Enter to quit the game.\n".encode())

        player.socket.send(
            f"Welcome to Halli Galli!\nYou are Player {player.player_number}.\n".encode())

        if self.host_player == None:
            self.host_player = player
            player.socket.send(
                "You are the host of this game room.".encode("utf-8"))
        else:
            player.socket.send(
                "Please press Enter to ready up for the game.".encode("utf-8"))

        while True:
            try:
                if not player in self.clients:
                    player.socket.close()
                else:
                    message = player.socket.recv(1024).decode("utf-8")

                    if self.status == "LOBBY_NOT_READY":
                        if message == "ready":
                            if player != self.host_player:
                                player.ready()
                                player.socket.send(
                                    "You have readied up. Please wait for the host to start the game...".encode("utf-8"))
                                host_message = f"Player {player.player_number} has readied up."
                                self.host_player.socket.send(host_message.encode("utf-8"))
                                if all(p.isready for p in self.clients if p != self.host_player):
                                    self.status = "LOBBY_READY"
                                    self.host_player.socket.send(
                                        "All players have readied up. Press Enter to start the game.".encode("utf-8"))

                    if self.status == "LOBBY_READY":
                        if message == "ready":
                            if player == self.host_player:
                                self.send_game_info("Starting the game now...")
                                self.status = "STARTING_GAME"
                                start_thread = Thread(
                                    target=self.start_game)
                                start_thread.daemon = True
                                start_thread.start()
                                message = ""
                        
                    if self.status == "IN_GAME":
                        if message == "ready":
                            self.hit_player = player
                            self.status = "PROCESSING_HIT"
                        
            except ConnectionResetError:
                print(f"Connection from {player.address} closed.")
                if self.status in ["LOBBY_NOT_READY", "LOBBY_READY"]:
                    if player in self.clients:
                        self.clients.remove(player)
                        message = f"Player {player.player_number} has left the game..."
                        self.send_game_info(message)

                        if player == self.host_player:
                            if self.clients:
                                self.host_player = self.clients[0]
                                message = "You are the new host of the game."
                                self.host_player.socket.send(message.encode("utf-8"))
                            else:
                                self.host_player = None

                        for person in self.clients:
                            if person.player_number > player.player_number:
                                person.player_number = person.player_number - 1
                                message = f"You are now Player {person.player_number}!"
                                person.socket.send(message.encode("utf-8"))
                                if person.isready == False:
                                    person.socket.send("Please press Enter to ready up for the game.".encode("utf-8"))
                                self.host_player.socket.send(f"Player {person.player_number+1} is now Player {person.player_number}.".encode("utf-8"))

                            else:
                                if person != self.host_player:
                                    if person.isready == False:
                                        person.socket.send("Please press Enter to ready up for the game.".encode("utf-8"))
                                else:
                                    if all(people.isready for people in self.clients if people != self.host_player):
                                        if len(self.clients) > 1:
                                            self.status = "LOBBY_READY"
                                            self.host_player.socket.send(
                                                "All players have readied up. Press Enter to start the game.".encode("utf-8"))
                                        else:
                                            self.status = "LOBBY_NOT_READY"

                else:
                    if player in self.clients:
                        del self.clients[player.player_number-1]
                        self.clients.insert(player.player_number-1, None)
                        self.game_object.black_list.append(player.player_number-1)
                        message = f"Player {player.player_number} has left the game..."
                        self.send_game_info(message)

    def start_server(self):
        self.status = "LOBBY_NOT_READY"
        with self.lock:
            self.socket.bind((self.host, self.port))
            self.socket.listen()
            print(f"Server is listening on {self.host}:{self.port}")

            while True:
                if self.status == "LOBBY_NOT_READY" or self.status == "LOBBY_READY":
                    client_socket, client_address = self.socket.accept()
                    if client_socket:
                        if not self.clients:
                            self.status = "LOBBY_NOT_READY"
                            new_player = HalliGalli_Player(
                                client_socket, client_address)
                            new_player.not_ready()
                            self.clients.append(new_player)
                            new_player.player_number = len(self.clients)
                            player_thread = Thread(
                                target=self.handle_client, args=(new_player,))
                            player_thread.daemon = True
                            player_thread.start()
                        else:
                            self.status = "LOBBY_NOT_READY"
                            new_player = HalliGalli_Player(
                                client_socket, client_address)
                            new_player.not_ready()
                            self.clients.append(new_player)
                            new_player.player_number = len(self.clients)
                            for existing_player in self.clients:
                                if existing_player != new_player:
                                    existing_player.socket.send(
                                        f"Player {new_player.player_number} has joined.".encode("utf-8"))
                            player_thread = Thread(
                                target=self.handle_client, args=(new_player,))
                            player_thread.daemon = True
                            player_thread.start()

    def start_game(self):
        self.status = "IN_GAME"

        self.game_object = HalliGalli_Game(len(self.clients))

        while True:
            if self.status == "PROCESSING_HIT":

                sleep(3)
                result = self.game_object.check_sum_equals_5()
                self.status = "IN_GAME"

                if result == True:
                    cnt = 0
                    self.send_game_info(
                        f"Player {self.hit_player.player_number} got it right!")
                    for pile in self.game_object.piles:
                        if not cnt in self.game_object.black_list:
                            self.game_object.decks[self.hit_player.player_number-1].add(
                                pile, False)
                        cnt = cnt+1
                else:
                    self.send_game_info(
                        f"Player {self.hit_player.player_number} got it wrong...")

                    penalty_card = self.game_object.decks[self.hit_player.player_number-1].play()

                    self.game_object.piles[self.hit_player.player_number-1].add(penalty_card, True)

                for i in self.game_object.black_list:
                    if not self.clients[i] == None:
                        del self.clients[i]
                        self.clients.insert(i, None)
            else:
                self.status = "IN_GAME"
                self.send_game_info(
                    "The game has started. Press Enter to hit the bell.")
                
                text = ''
                for i in range(len(self.clients)):
                    text += ' P'+str(i+1) + ' '
                text = text+'\n'
                self.send_game_info(text)

                text = ''
                for deck in self.game_object.decks:
                    if deck:
                        deck_amount = len(deck.deck)
                        if deck_amount > 9:
                            text += ' ' + str(deck_amount) + ' '
                        else:
                            text += ' ' + str(deck_amount) + '  '
                text = text + '\n'
                self.send_game_info(text)

                text = ''
                cnt = 0
                for pile in self.game_object.piles:
                    if pile.deck:
                        upper_card = pile.deck[0]
                        first = ' ' + str(upper_card.num)
                        second = str(upper_card.fruit)[0].upper() + ' '
                        formatted = first + second
                        text += formatted
                        cnt += 1
                    else:
                        if self.game_object.decks[cnt%len(self.game_object.decks)]:
                            text += ' XX '
                        cnt += 1
                    
                text = text + '\n'
                self.send_game_info(text)

                for i in self.game_object.black_list:
                    if not self.clients[i] == None:
                        del self.clients[i]
                        self.clients.insert(i, None)

                self.game_object.play_turn()
            sleep(2)
            finish = self.close()
            if finish:
                break

    def send_game_info(self, letter: str):

        for player in self.clients:
            if not player == None:
               player.socket.send(letter.encode("utf-8"))

    def format(word):

        formatted_word = '' + word + ''

        return formatted_word
 
    def close(self):
        finish = self.game_object.check_game_over()
        if finish == True:
            message = f"Player {self.clients[self.game_object.game_over_index].player_number} won the game!"
            self.send_game_info(message)
            sleep(3)
            return True

if __name__ == "__main__":
    host = "192.168.50.101"
    port = 11111
    implement = HalliGalli_Server(host, port)
    implement.start_server()