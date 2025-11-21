import logging

from file_rag.core.llms import deepseek_model, image_llm_model
from langchain.agents import create_agent

logger = logging.getLogger(__name__)

_image_model = image_llm_model or deepseek_model

if _image_model is None:
    raise RuntimeError("无法创建图片处理模型：既没有图像模型也没有文本模型可用")

if image_llm_model is None:
    logger.warning("图像模型不可用，已退化为文本模型处理图片消息")

agent = create_agent(
    model=_image_model,
    tools=[],
    system_prompt="你是AI智能助手，专门针对用户上传的图片，回答用户问题。请仔细分析图片内容并提供详细的回答。",
    name="image_chat_agent",
)
