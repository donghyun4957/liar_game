from openai import OpenAI
import os
import re
from collections import Counter
import random
import ollama
# 'EEVE-Korean-10.8B'
class LiarGame():
    def __init__(self):
        self.word_list = ['키위', '사과', '바나나']

    def select_word(self):
        main_word, sub_word = random.sample(self.word_list, 2)
        return main_word, sub_word

class PlayerBot():
    def __init__(self, id=0):
        self.client = OpenAI()
        self.player_id = id
        self.identity = 'bot'
        self.is_done = False
        self.is_vote_done = False
        self.word = None
        self.instruction = None
        self.chat_history = []
        self.model = 'gpt-4o-mini'

    def input_instruction(self):
        prompt = f"""
        너는 '라이어 게임'의 {self.player_id}번 플레이어야.
        너는 '{self.word}'라는 단어를 받았어.
        너의 목표는 {self.word}가 정답이라는 전제에서 가장 의심스러운 사람을 찾는 거야.

        [게임 규칙]
        1. 모든 플레이어는 제시어를 하나 받는다. 단, 한 명은 라이어로 다른 단어를 받는다.
        2. 너가 설명할 때는, 절대 제시어를 말하지 않고 한 문장으로 자연스럽게 설명해라.
        3. 너무 구체적으로 말하지 말고, 다른 플레이어가 이해할 수 있을 정도만 일반적으로 말해라.
        4. 너가 받은 단어만 기준으로 설명하되 절대 그 단어를 말해서는 안된다.
        5. 설명 외의 불필요한 정보(예: 신뢰도, 투표 추천 등)는 절대로 작성을 금지한다.

        [투표 규칙]
        1. 한 바퀴가 끝나면 누가 라이어인지 추리해야 한다.
        2. 반드시 너가 받은 단어 '{self.word}'를 기준으로, 다른 플레이어들의 설명이 얼마나 너의 단어와 얼마나 부합하는지 비교해라.
        3. 가장 부합하지 않는 플레이어를 라이어로 선택한다.
        3. 출력은 숫자 하나만. 예: '0', '2'. 숫자 외에는 아무 것도 말하지 마라.

        항상 위 규칙을 지키고, 차례가 올 때마다 상황에 맞는 설명 또는 숫자 하나만 출력해라.
        """
        self.instruction = {"role": "system", "content": prompt}
        self.chat_history.append(self.instruction)

    def get_word(self, word):
        self.word = word

    def turn(self):
        print(f'{self.player_id}번 플레이어 봇님, 설명할 차례입니다. : ')
        message = f"너가 받은 제시어 '{self.word}'를 말하지 않고 다른 플레이어가 이해할 정도로 한국어 한 문장 설명해줘."
        self.chat_history.append({'role':'user', 'content':message})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                *self.chat_history,
            ],
            response_format={
                "type": "text"
            },
            temperature=1.0,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        answer = response.choices[0].message.content
        bot_message = {"role": "user", "content": f'{self.player_id}번 플레이어는 이렇게 말했어: {answer} 이 발언을 한 사람이 라이어일지 생각해봐.'}
        self.chat_history.append({'role':'assistant', 'content':answer})
        
        return bot_message, answer
    
    def done(self):
        self.is_done = True

    def vote_done(self):
        self.is_vote_done = True

    def guess_liar(self, player_list):
        message = f"""
        이제 라이어를 맞출거야. 아래의 답변 규칙을 고려해서 라이어가 몇번 플레이어인지 선택해줘.
        [답변 규칙]
        1. 지금까지 대화를 참고해서 가장 수상한 플레이어 번호 하나를 선택해. (0-{len(player_list)-1} 중 하나)
        2. 오직 0-{len(player_list)-1} 중 숫자 하나만 출력해.
        3. 너 자신은 절대 선택하지 마
        """
        self.chat_history.append({'role':'user', 'content':message})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                *self.chat_history,
            ],
            response_format={
                "type": "text"
            },
            temperature=1.0,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        answer = response.choices[0].message.content
        self.chat_history.append({'role':'assistant', 'content':answer})

        match = re.search(r'\d+', answer)
        if match:
            return int(match.group())  # 정수 변환
        else:
            return 0

    def connect_bot(self, bot_message, bot_list):
        for i in range(len(bot_list)):
            if bot_list[i].player_id != self.player_id:
                bot_list[i].chat_history.append(bot_message)

class Player():
    def __init__(self, id):
        self.player_id = id
        self.identity = 'human'
        self.is_done = False
        self.is_vote_done = False
        self.word = None

    def get_word(self, word):
        self.word = word

    def turn(self, message):
        bot_message = {"role": "user", "content": f'{self.player_id}번 플레이어는 이렇게 말했어: {message} 이 발언을 한 사람이 라이어일지 생각해봐.'}
        return bot_message, message
    
    def done(self):
        self.is_done = True

    def vote_done(self):
        self.is_vote_done = True

    def guess_liar(self, liar, player_list):
        while True:
            try:
                # liar = int(input(f"{self.player_id}번 플레이어님, 누가 라이어라고 생각하나요? (0 ~ {len(player_list)-1}): "))
                if 0 <= liar <= len(player_list)-1:
                    return int(liar)
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
    num_humans = 1
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
                vote = player.guess_liar(player_list)
                print(vote)
                votes.append(vote)

            counter = Counter(votes)
            max_count = max(counter.values())
            
            candidates = [idx for idx, cnt in counter.items() if cnt == max_count]

            if len(candidates) > 1:
                print('length candidates: ', candidates)
                print(f"동률 발생! 후보: {[votes[i] for i in candidates]}")
                chosen = random.choice(candidates)
                print('chosen: ', chosen)
                print(f"랜덤으로 {votes[chosen]}번 플레이어가 선택되었습니다.")
            else:
                chosen = candidates[0]
                print('length candidates: ', candidates)
                print('chosen: ', chosen)
                print(f"{votes[chosen]}번 플레이어가 라이어로 선택되었습니다.")

            if votes[chosen] == target_id:
                print(f"정답! {votes[chosen]}번 플레이어는 라이어였습니다.")
                print('게임을 종료합니다.')
                break
            else:
                print(f"실패! {votes[chosen]}번 플레이어는 라이어가 아니었습니다.")

                for player in player_list:
                    if player.word == sub_word:
                        print(f"진짜 라이어는 {player.player_id}번 플레이어였습니다!")
                        print('게임을 종료합니다.')
                        break
