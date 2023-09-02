from dotenv import load_dotenv
import openai
import os
import googletrans

def use_dalle(prompt):
  translator = googletrans.Translator()
  prompt = translator.translate(prompt, dest = 'en')

  # ## chat-GPT활용
  load_dotenv()
  openai.api_key = os.getenv("openai.api_key")

  response = openai.Image.create(
    prompt= prompt.text,
    n=1, #만들 이미지 개수
    size="512x512" #이미지 크기
  )

  image_url = response['data'][0]['url']
  return image_url