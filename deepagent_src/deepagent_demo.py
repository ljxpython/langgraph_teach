import os
from dotenv import load_dotenv
load_dotenv()
os.environ["LANGSMITH_TRACING"] = "false"


from deepagents import create_deep_agent

from deepagent_src.search_tools import internet_search
from deepagent_src.llms import get_gpt_model

# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

agent = create_deep_agent(
    model=get_gpt_model(),
    tools=[internet_search],
    system_prompt=research_instructions,
)

# result = agent.invoke({"messages": [{"role": "user", "content": "What is Deep Agents and how does it work?"}]})
#
# # Print the agent's response
# print(result["messages"][-1].content)


# stream = agent.stream_events({
#     "messages": [{"role": "user", "content": "北京的天气怎么样?"}],
# }, version="v3")
#
# for message in stream.messages:
#     for delta in message.text:
#         print(delta, end="", flush=True)
#
# final_state = stream.output
# print(final_state)

from langchain.messages import HumanMessage

messages = [HumanMessage(content="Add 3 and 4.")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()