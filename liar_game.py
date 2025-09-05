import os
from random import shuffle
import ollama

class PlayerBot():

    def __init__(self, model='EEVE-Korean-10.8B', id):
        self.bot_id = id
        self.instruction = f"{id}"
        self.chat_history = [{"role": "system", "content": self.instruction}]
        self.model = model

    def generate_instruction():
        return

    def turn(self, message):
        message = "이제 너 차례야! 설명해봐."
        self.chat_history.append({'role':'user', 'content':message})
        response = ollama.chat(model=self.model, messages=self.chat_history)
        bot_message = {"role": "user", "content": f'{self.player_id}번 플레이어는 이렇게 말했어.' + response.message.content}
        self.chat_history.append({'role':'assistant', 'content':response.message.content})
        
        return bot_message, response.message.content
    
    def connect_bot(self, bot_message, bot_list):
        for i in range(len(bot_list)):
            bot_list[i].chat_history.append(bot_message)


class Player():
    def __init__(self, id):
        self.player_id = id
    
    def turn(self, message):
        message = input()
        bot_message = {"role": "user", "content": f'{self.player_id}번 플레이어는 이렇게 말했어.' + message}
        return bot_message, message
    
    def connect_bot(self, bot_message, bot_list):
        for i in range(len(bot_list)):
            bot_list[i].chat_history.append(bot_message)

def generate_players(player, n=2):
    player_list = [player(i+1) for i in range(n)] 

    return player_list

def set_sequence(num_humans, num_bots):
    player_bots = generate_players(PlayerBot, num_bots)
    players = generate_players(Player, num_humans)
    players.extend(player_bots)
    shuffle(players)

    return player_bots, players

def start_game():
    num_humans = int(input('참가자 수를 입력하세요: '))
    num_bots = int(input('생성할 봇 수를 입력하세요: '))
    bot_list, player_list = set_sequence(num_humans, num_bots)
    
    # 단어 두개 선정
    # 벌칙자 랜덤 뽑기

    turn = 0
    while True:
        if turn % len(player_list) == 0:
            turn = 0
        current_player = player_list[turn]
        print(f'{current_player.id}번 플레이어님, 설명할 차례입니다. : ')
        bot_message, message = current_player.turn()
        current_player.connect_bot(bot_message, bot_list)
        turn += 1

if __name__ == "__main__":
    # os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    start_game()

