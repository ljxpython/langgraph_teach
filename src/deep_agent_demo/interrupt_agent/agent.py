import os

from langchain.tools import tool
from deepagents import create_deep_agent
from langchain_deepseek import ChatDeepSeek
from src.llms import get_default_model
from langgraph.checkpoint.memory import MemorySaver

@tool
def delete_file(path: str) -> str:
    """Delete a file from the filesystem."""
    return f"Deleted {path}"

@tool
def read_file(path: str) -> str:
    """Read a file from the filesystem."""
    return f"Contents of {path}"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return f"Sent email to {to}"



# Checkpointer is REQUIRED for human-in-the-loop
# checkpointer = MemorySaver()
# os.environ["DEEPSEEK_API_KEY"] = "sk-ab8dda459d2a4203b71c6aa2065b411a"
# deepseek = ChatDeepSeek(model="deepseek-chat")

agent = create_deep_agent(
    model=get_default_model(),
    tools=[delete_file, read_file, send_email],
    interrupt_on={
        "delete_file": True,  # Default: approve, edit, reject
        "read_file": False,   # No interrupts needed
        "send_email": {"allowed_decisions": ["approve", "reject"]},  # No editing
    },
    # checkpointer=checkpointer  # Required!
)