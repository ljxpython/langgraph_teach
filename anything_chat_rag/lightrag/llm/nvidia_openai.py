import sys
import os
# pylint: disable  MC8zOmFIVnBZMlhtblk3a3ZiUG1yS002Um1NNWRRPT06ZGU2YTVhYzM=

if sys.version_info < (3, 9):
    pass
else:
    pass

import pipmaster as pm  # Pipmaster for dynamic library install

# install specific modules
if not pm.is_installed("openai"):
    pm.install("openai")
# type: ignore  MS8zOmFIVnBZMlhtblk3a3ZiUG1yS002Um1NNWRRPT06ZGU2YTVhYzM=

from openai import (
    AsyncOpenAI,
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from lightrag.utils import (
    wrap_embedding_func_with_attrs,
)


import numpy as np

# pylint: disable  Mi8zOmFIVnBZMlhtblk3a3ZiUG1yS002Um1NNWRRPT06ZGU2YTVhYzM=

@wrap_embedding_func_with_attrs(embedding_dim=2048, max_token_size=8192)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(
        (RateLimitError, APIConnectionError, APITimeoutError)
    ),
)
async def nvidia_openai_embed(
    texts: list[str],
    model: str = "nvidia/llama-3.2-nv-embedqa-1b-v1",
    # refer to https://build.nvidia.com/nim?filters=usecase%3Ausecase_text_to_embedding
    base_url: str = "https://integrate.api.nvidia.com/v1",
    api_key: str = None,
    input_type: str = "passage",  # query for retrieval, passage for embedding
    trunc: str = "NONE",  # NONE or START or END
    encode: str = "float",  # float or base64
) -> np.ndarray:
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    openai_async_client = (
        AsyncOpenAI() if base_url is None else AsyncOpenAI(base_url=base_url)
    )
    response = await openai_async_client.embeddings.create(
        model=model,
        input=texts,
        encoding_format=encode,
        extra_body={"input_type": input_type, "truncate": trunc},
    )
    return np.array([dp.embedding for dp in response.data])
