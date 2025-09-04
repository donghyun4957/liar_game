import os
import ollama

def chat_with_eeve():

    print('='*10, '대화 시작', '='*10)
    print('종료하려면 exit를 입력하세요...')

    chat_history = []
    while True:
        user_input = input('당신: ')

        if user_input == '종료':
            print('='*10, '대화 종료', '='*10)
            break

        chat_history.append({'role':'user', 'content':user_input})

        response = ollama.chat(model='EEVE-Korean-10.8B', messages=chat_history)
        print(f'EEVE: {response.message.content}\n')

        chat_history.append({'role':'assistant', 'content':response.message.content})

chat_with_eeve()

if __name__ == "__main__":
    # os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    chat_with_eeve()