import os
# pyrefly: ignore [missing-import]
from llama_parse import LlamaParse
from langsmith import traceable

@traceable(name="LlamaParse Document Parser", run_type="tool")
async def parse_document(file_path: str) -> str:
    """
    Parse a document asynchronously using LlamaParse.
    
    Raises:
        RuntimeError: If LLAMA_CLOUD_API_KEY is not set.
    """
    api_key = os.environ.get("LLAMA_CLOUD_API_KEY")
    if not api_key:
        raise RuntimeError(
            "LLAMA_CLOUD_API_KEY environment variable is missing. "
            "Please register for a free key at https://cloud.llamaindex.ai "
            "and add it to your environment variables."
        )
        
    # Instantiate the parser inside the function call (lazy initialization)
    # This prevents the application from crashing on startup if the API key is not configured yet.
    parser = LlamaParse(
        api_key=api_key,
        result_type="markdown",
        verbose=True
    )
    
    # Perform asynchronous cloud parsing
    documents = await parser.aload_data(file_path)
    full_markdown = "\n\n".join([doc.text for doc in documents])
    return full_markdown
