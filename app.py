import base64
import streamlit as st
import random
from collections import Counter
from liar_game import LiarGame, Player, PlayerBot, set_sequence

# ------------------- 함수 정의 -------------------
def set_bg(png_file):
    with open(png_file, "rb") as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
        }}
        </style>
        """, unsafe_allow_html=True)

def start_game():
    bot_list, player_list = set_sequence(st.session_state['num_humans'], st.session_state['num_bots'])
    game_object = LiarGame()
    main_word, sub_word = game_object.select_word()

    st.session_state['main_word'] = main_word
    st.session_state['sub_word'] = sub_word

    target_id = random.randint(0, len(player_list)-1)
    st.session_state['target_id'] = target_id

    for player in player_list:
        player.word = sub_word if player.player_id == target_id else main_word
    for bot in bot_list:
        bot.input_instruction()
        print(bot.instruction['content'])

    st.session_state['player_list'] = player_list
    st.session_state['bot_list'] = bot_list
    st.session_state['turn'] = 0
    st.session_state['game_state'] = 'running'

def render_player_logs():
    row1_cols = st.columns([1,1,1], gap="medium")
    row2_cols = st.columns([1,1,1], gap="medium")
    return row1_cols + row2_cols

def ready_voting():
    st.session_state['game_state'] = 'ready_voting'

def go_to_voting():
    st.session_state['game_state'] = 'voting'
    st.session_state['vote_turn'] = 0

def get_result():
    st.session_state['game_state'] = 'ending'

# ------------------- 페이지 설정 -------------------
st.set_page_config(page_title="라이어 게임", layout="wide")
st.markdown("<h1 style='text-align: center;'>라이어 게임 🕵️‍♂️</h1>", unsafe_allow_html=True)
# set_bg("images/liargame.jpg")
# ------------------- CSS 추가 -------------------
st.markdown("""
<style>
.player-card {
    background-color: #f0f0f0;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 10px;
    min-height: 80px;
}
.player-name {
    font-weight: bold;
    margin-bottom: 5px;
    text-align: center;
}
.chat-bubble {
    background-color: #ffffff;
    padding: 8px;
    border-radius: 8px;
    box-shadow: 0px 1px 3px rgba(0,0,0,0.2);
    margin-top: 5px;
    word-break: break-word;
}
.human .chat-bubble {
    background-color: #d1e7dd;
}
.bot .chat-bubble {
    background-color: #ffe5b4;
}
</style>
""", unsafe_allow_html=True)

# ------------------- 초기화 -------------------
for key, default in [('num_humans',0), ('num_bots',0), ('turn',0), ('vote_turn',0),
                     ('game_state',None), ('player_list',[]), ('bot_list',[]),
                     ('messages',{}), ('votes',[]), ('target_id',None),
                     ('main_word',""), ('sub_word',"")]:
    if key not in st.session_state:
        st.session_state[key] = default

# ------------------- 게임 초기 설정 -------------------
if st.session_state['game_state'] is None:
    col1, col2, col3 = st.columns([1, 2, 1])  # 가운데 열이 폭이 넓음
    st.session_state['num_humans'] = 1
    with col2:
        st.session_state['num_bots'] = st.number_input("생성할 봇 수를 입력하세요:", min_value=1, max_value=5, value=2, step=1)
        st.button("게임 시작", on_click=start_game)

player_list = st.session_state.get('player_list', [])
bot_list = st.session_state.get('bot_list', [])

player_cols = render_player_logs()
for i, player in enumerate(player_list):
    with player_cols[i]:
        msg = st.session_state['messages'].get(player.player_id, "")
        css_class = "human" if player.identity == 'human' else "bot"
        st.markdown(f"""
        <div class="player-card">
            <div class="player-name">{player.player_id}번 {'플레이어' if player.identity=='human' else '플레이어 봇'}</div>
            <div class="{css_class}">
                <div class="chat-bubble">{msg}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ------------------- 게임 진행 -------------------
if st.session_state['game_state'] == 'running':
    st.write(f"단어: {st.session_state['main_word']} (라이어 단어: {st.session_state['sub_word']})")
    st.write(f"라이어: {st.session_state['target_id']}")
    current_player = player_list[st.session_state['turn'] % len(player_list)]

    with player_cols[st.session_state['turn']]:
        if current_player.identity == 'human' and not current_player.is_done:
            user_input = st.text_input(
                "설명 입력:", 
                key=f"human_input_{st.session_state['turn']}", 
                placeholder="여기에 입력"
            )
            if st.button("입력 완료", key=f"submit_{st.session_state['turn']}"):
                bot_message, message = current_player.turn(user_input)
                current_player.connect_bot(bot_message, bot_list)
                st.session_state['messages'][current_player.player_id] = message
                current_player.done()
                st.session_state['turn'] += 1
                if (st.session_state['turn']) != len(player_list):
                    if st.button("Next", key=f"next_turn_{st.session_state['turn']}"):
                        pass
                else:
                    st.button("Next", on_click=ready_voting)

        elif current_player.identity == 'bot' and not current_player.is_done:
            with st.spinner(f"{current_player.player_id}번 봇이 설명 생성 중..."):
                bot_message, message = current_player.turn()
                current_player.connect_bot(bot_message, bot_list)
                st.session_state['messages'][current_player.player_id] = message
                current_player.done()
                st.session_state['turn'] += 1
            if (st.session_state['turn']) != len(player_list):
                if st.button("Next", key=f"next_turn_{st.session_state['turn']}"):
                    pass
            else:
                st.button("Next", on_click=ready_voting)

if st.session_state['turn'] >= len(player_list) and st.session_state['game_state'] == 'ready_voting':
    st.subheader("한 바퀴 종료! 투표 단계로 넘어갑니다.")
    st.button("투표하기", on_click=go_to_voting)

# ------------------- 투표 단계 -------------------
if st.session_state['game_state'] == 'voting':
    st.subheader("라이어를 투표하세요.")

    current_voter = player_list[st.session_state['vote_turn'] % len(player_list)]

    if current_voter.identity == 'human' and not current_voter.is_vote_done:
        vote_input = st.text_input(
            f"{current_voter.player_id}번 플레이어님, 라이어를 투표해주세요 (숫자 입력)",
            key=f"vote_input_{st.session_state['vote_turn']}"
        )
        if st.button("입력 완료", key=f"submit_{st.session_state['vote_turn']}"):
            vote_int = int(vote_input)
            human_vote = current_voter.guess_liar(vote_int, player_list)
            st.session_state['votes'].append(human_vote)
            st.session_state['vote_turn'] += 1
            current_voter.vote_done()
        if (st.session_state['vote_turn']) != len(player_list):
            if st.button("Next", key=f"next_turn_{st.session_state['vote_turn']}"):
                pass
        else:
            st.button("결과보기", on_click=get_result)

    elif current_voter.identity == 'bot' and not current_voter.is_vote_done:
        bot_vote = current_voter.guess_liar(player_list)
        st.session_state['votes'].append(bot_vote)
        st.session_state['vote_turn'] += 1
        current_voter.vote_done()
        st.write(f"{current_voter.player_id}번 봇은 {bot_vote}번 플레이어를 선택했습니다.")
        if (st.session_state['vote_turn']) != len(player_list):
            if st.button("Next", key=f"next_turn_{st.session_state['vote_turn']}"):
                pass
        else:
            st.button("결과보기", on_click=get_result)

if st.session_state['game_state'] == 'ending':
    st.subheader("결과 종합")
    
    counter_votes = Counter(st.session_state['votes'])
    max_count = max(counter_votes.values())
    candidates = [idx for idx, cnt in counter_votes.items() if cnt == max_count]
    chosen = random.choice(candidates) if len(candidates) > 1 else candidates[0]

    st.subheader(f"{st.session_state['votes'][chosen]}번 플레이어가 라이어로 선택되었습니다.")

    if st.session_state['votes'][chosen] == st.session_state['target_id']:
        st.success(f"정답! {st.session_state['votes'][chosen]}번 플레이어는 라이어였습니다.")
    else:
        st.error(f"실패! {st.session_state['votes'][chosen]}번 플레이어는 라이어가 아니었습니다.")
        for p in player_list:
            if p.word == st.session_state['sub_word']:
                st.info(f"진짜 라이어는 {p.player_id}번 플레이어였습니다.")

    st.session_state['game_state'] = 'finish'

# ------------------- 종료 -------------------
if st.session_state['game_state'] == 'finish':
    st.subheader("게임 종료")
    st.button("게임 다시 시작", on_click=lambda: st.session_state.clear())
