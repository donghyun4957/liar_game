import os
from collections import Counter
import random
import ollama

class LiarGame():
    def __init__(self):
        self.word_list = ['키위', '사과', '바나나']

    def select_word(self):
        main_word, sub_word = random.sample(self.word_list, 2)
        return main_word, sub_word


class PlayerBot():
    def __init__(self, id=0):
        self.player_id = id
        self.identity = 'bot'
        self.word = None
        self.instruction = None
        self.chat_history = []
        self.model = 'EEVE-Korean-10.8B'

    def input_instruction(self):
        prompt = '''ddd'''
        self.instruction = {"role": "system", "content": prompt}
        self.chat_history.append(self.instruction)

    def get_word(self, word):
        self.word = word

    def turn(self):
        print(f'{self.player_id}번 플레이어 봇님, 설명할 차례입니다. : ')
        message = f"이제 너 차례야! {self.word}에 대해 한문장으로 설명해봐."
        self.chat_history.append({'role':'user', 'content':message})
        response = ollama.chat(model=self.model, messages=self.chat_history)
        bot_message = {"role": "user", "content": f'{self.player_id}번 플레이어는 이렇게 말했어.' + response.message.content}
        self.chat_history.append({'role':'assistant', 'content':response.message.content})
        
        return bot_message, response.message.content
    
    def guess_liar(self, player_list):
        print(f"{self.player_id}번 플레이어 봇님, 누가 라이어라고 생각하나요? (0 ~ {len(player_list)-1}): ")
        message = f"이제 라이어를 맞출거야. 너가 생각하는 라이어는 0-{len(player_list)-1} 중 몇번 플레이어인지 숫자 하나로만 대답해줘"
        self.chat_history.append({'role':'user', 'content':message})
        response = ollama.chat(model=self.model, messages=self.chat_history)
        self.chat_history.append({'role':'assistant', 'content':response.message.content})

        return response.message.content

    def connect_bot(self, bot_message, bot_list):
        for i in range(len(bot_list)):
            bot_list[i].chat_history.append(bot_message)


class Player():
    def __init__(self, id):
        self.player_id = id
        self.identity = 'human'
        self.word = None

    def get_word(self, word):
        self.word = word

    def turn(self):
        print(f'{self.player_id}번 플레이어님, 설명할 차례입니다. : ')
        message = input()
        bot_message = {"role": "user", "content": f'{self.player_id}번 플레이어는 이렇게 말했어.' + message}
        return bot_message, message
    
    def guess_liar(self, player_list):
        while True:
            try:
                liar = int(input(f"{self.player_id}번 플레이어님, 누가 라이어라고 생각하나요? (0 ~ {len(player_list)-1}): "))
                if 0 <= liar <= len(player_list)-1:
                    return liar
                else:
                    print(f"입력 범위를 벗어났습니다. 0 ~ {len(player_list)-1} 사이의 숫자를 입력하세요.")
            except ValueError:
                print("숫자를 입력해야 합니다.")

    def connect_bot(self, bot_message, bot_list):
        for i in range(len(bot_list)):
            bot_list[i].chat_history.append(bot_message)


def generate_players(player, n=2, offset=0):
    player_list = [player(i+offset) for i in range(n)] 

    return player_list

def set_sequence(num_humans, num_bots):
    players = generate_players(Player, num_humans)
    player_bots = generate_players(PlayerBot, num_bots, num_humans)
    players.extend(player_bots)
    random.shuffle(players)

    return player_bots, players

def start_game():
    num_humans = int(input('참가자 수를 입력하세요: '))
    num_bots = int(input('생성할 봇 수를 입력하세요: '))
    bot_list, player_list = set_sequence(num_humans, num_bots)
    
    game_object = LiarGame()
    main_word, sub_word = game_object.select_word()
    print('단어: ', main_word, ' 라이어 단어: ', sub_word)

    target_id = random.randint(0, len(player_list)-1)
    for player in player_list:
        player.word = sub_word if player.player_id == target_id else main_word
        print(f'라이어: {player.player_id}번 플레이어') if player.player_id == target_id else main_word

    # bot에 instruction 제공
    for i, player_bot in enumerate(bot_list):
        player_bot.input_instruction()

    turn = 0
    while True:
        current_player = player_list[turn]
        bot_message, message = current_player.turn()
        print(bot_message)
        current_player.connect_bot(bot_message, bot_list)
        turn += 1

        if turn % len(player_list) == 0:
            print('한 바퀴가 종료되었습니다. 라이어는 누구인지 투표해주세요')

            votes = []
            for player in player_list:
                vote = player.guess_liar(player_list)  # 각 플레이어가 투표
                print(vote)
                votes.append(vote)

            counter = Counter(votes)
            max_count = max(counter.values())
            
            # 최빈값 후보 리스트
            candidates = [idx for idx, cnt in counter.items() if cnt == max_count]

            if len(candidates) > 1:
                print(f"동률 발생! 후보: {[player_list[i].player_id for i in candidates]}")
                chosen = random.choice(candidates)
                print(f"랜덤으로 {player_list[chosen].player_id}번 플레이어가 선택되었습니다.")
            else:
                chosen = candidates[0]
                print(f"{player_list[chosen].player_id}번 플레이어가 라이어로 선택되었습니다.")

            # 라이어 판정
            if player_list[chosen].word == sub_word:
                print(f"정답! {player_list[chosen].player_id}번 플레이어는 라이어였습니다.")
                print('게임을 종료합니다.')
                break
            else:
                print(f"실패! {player_list[chosen].player_id}번 플레이어는 라이어가 아니었습니다.")

                for player in player_list:
                    if player.word == sub_word:
                        print(f"진짜 라이어는 {player.player_id}번 플레이어였습니다!")
                        print('게임을 종료합니다.')
                        break


if __name__ == "__main__":
    # os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    start_game()

