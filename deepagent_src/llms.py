import os
from dotenv import load_dotenv

load_dotenv()
from langchain.chat_models import init_chat_model
from langchain_deepseek.chat_models import ChatDeepSeek
from langchain_openai.chat_models import ChatOpenAI



def get_default_model():
    return ChatDeepSeek(model="deepseek-chat")

def get_doubao_model():
    return ChatOpenAI(
        model='doubao-seed-1-6-251015',
        api_key=os.getenv("DOUBAO_API_KEY"),
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    )

def get_gpt_model():
    return ChatOpenAI(
        model='gpt-5.5',
        api_key=os.getenv("CHATGPT_API_KEY"),
        base_url=os.getenv("CHATGPT_API_URL"),
    )
gpt_model= get_gpt_model()


# doubao_llm = get_doubao_model()

# response = gpt_model.invoke("你好")
# print(response)
#
# llm = get_gpt_model()
# response = llm.invoke("你好")
# print(response)
# for text in llm.stream("你好"):
#     print(text.content, end="", flush=True)