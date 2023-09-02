#고객키워드 = 상세키워드, 제품디자인 = 한 줄 정리, 디자인 이유 = 디자인 이유
#상세설명을 썼을 때 ->  generate_job_name_detail/ 안썻을때 ->generate_job_name_short

from dotenv import load_dotenv
import openai
import os
import json
import re
#import googletrans

#JSON으로 확실하게 출력하는 함수
def read_string_to_list(input_string):
    if input_string is None:
        return None

    try:
        input_string = input_string.replace("'", "\"")  # Replace single quotes with double quotes for valid JSON
        data = json.loads(input_string)
        return data
    except json.JSONDecodeError:
        print("Error: Invalid JSON string")
        return None

# ## chat-GPT활용
load_dotenv()
openai.api_key = os.getenv("openai.api_key")

# openai.api_key = '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'

#상세 정보가 들어왔을때 쓰는 함수
def generate_job_name_detail(product,basic_info,more_info):
    #제품 = product ; 기본정보 = basic_info; 세부사항 = more_info

    separate = "'''"

    Prompt = f"""
    You are an imaginative painter skilled at understanding persona's needs. 
    You can comprehend both persona and product information, creating imaginative product designs. 
    The text, separated by triple backquotes {separate}. 
    
    Perform the following actions:
    1 - You must choose two keywords for clustering persona characteristics from this given list '['활동적','차분한','호기심','합리적','팝','새로움','단순함','예민함','자신감','성실함','용감함','창의적']'- nothing else. Ensuring that you only choose two keywords from the given list. 
    
    2 - Describe the design using concise keywords a lot, do not make sentences, arrange in a row physically. Go into details. And focusing on colors, shape and characteristic.
    ex)직사각형 모양, 깔끔하고 안정적인 분위기, 다크 우드 컬러, 현대적인 디자인, 심플하고 세련된 형태
    
    3 – Provide really detailed explanations for the reasoning behind your design idea. Do not make list.
    
    4 - Output a JSON objet that containing the following keys: 고객키워드, 제품디자인, 디자인이유. Do not sumarize '3-디자인이유' , print out the orginal content as is.
    
    Separate your answers with line breaks.
    You must complete all actions.
    Answer in Korean.
    """

    Text = f"""#Information 제품: {product} \n 페르소나: {basic_info} 선호 \n {more_info}"""

    messages = [{'role': 'system', 'content': Prompt},
                {'role': 'user', 'content': f'{separate}{Text}{separate}.'}]
    #print(f"messages here:{messages}")

    chat = openai.ChatCompletion.create(
        model='gpt-3.5-turbo-0613',
        messages=messages,
        temperature=0.6
    )

    reply = chat.choices[0].message.content
    #print(f'ChatGPT: {reply}', '\n') #gpt결과 출력

    pattern = r"(\{.*\})"
    match = re.search(pattern, reply, re.DOTALL)
    return match


# 상세 정보가 안 들어왔을때 쓰는 함수
def generate_job_name_short(product, basic_info):
    # 제품 = product ; 기본정보 = basic_info

    separate = "'''"

    Prompt = f"""
    You are an imaginative painter skilled at understanding persona's needs. 
    You can comprehend both persona and product information, creating imaginative product designs. 
    The text, separated by triple backquotes {separate}. 

    Perform the following actions:
    1 - Describe the design using concise keywords a lot, do not make sentences, arrange in a row physically. Go into details. And focusing on colors, shape and characteristic.
    ex)직사각형 모양, 깔끔하고 안정적인 분위기, 다크 우드 컬러, 현대적인 디자인, 심플하고 세련된 형태

    2 – Provide really detailed explanations for the reasoning behind your design idea. Do not make list.

    3 - Output a JSON objet that containing the following keys: 제품디자인, 디자인이유. Do not sumarize '2-디자인이유' , print out the orginal content as is.

    Separate your answers with line breaks.
    You must complete all actions.
    Answer in Korean.
    """

    Text = f"""#Information 제품: {product} \n 페르소나: {basic_info} 선호"""

    messages = [{'role': 'system', 'content': Prompt},
                {'role': 'user', 'content': f'{separate}{Text}{separate}.'}]
    #print(f"messages here:{messages}")

    chat = openai.ChatCompletion.create(
        model='gpt-3.5-turbo-0613',
        messages=messages,
        temperature=0.6
    )

    reply = chat.choices[0].message.content
    #print(f'ChatGPT: {reply}', '\n') #gpt결과 출력

    pattern = r"(\{.*\})"
    match = re.search(pattern, reply, re.DOTALL)
    return match

#결과 출력하기
#input_values = (product,basic_info,more_info) #입력되는 값 input_values = (product,basic_info) 일수도 있음
def gpt_input_values(input_values):
    max_attempts = 2
    matching_function = generate_job_name_detail if len(input_values) == 3 else generate_job_name_short

    for attempts in range(max_attempts):
        match = matching_function(*input_values)
        if match:
            extracted_json = match.group(1)
            data = read_string_to_list(extracted_json)
            # print(f'final:\n{json.dumps(data, indent=2, ensure_ascii=False)}')
            return data
        elif attempts == max_attempts - 1:
            print('error')