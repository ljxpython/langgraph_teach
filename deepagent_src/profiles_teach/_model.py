from __future__ import annotations

import os
import sys
from pathlib import Path


os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from deepagent_src.llms import get_gpt_model


MODEL_PROFILE_KEY = "openai:gpt-5.5"


def get_real_model():
    return get_gpt_model()

