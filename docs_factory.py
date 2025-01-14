import streamlit as st
from langchain_aws import ChatBedrock

def generate_readme(readable_files):
    """
    Generates README content based on the list of readable files using the Anthropic ChatBedrock model.

    Args:
        readable_files (list of str): List of file paths relative to the repository root.

    Returns:
        str: Generated README content.
    """
    # Accessing AWS credentials and Anthropic API key from secrets
    aws_access_key_id = st.secrets["aws"]["access_key_id"]
    aws_secret_access_key = st.secrets["aws"]["secret_access_key"]
    aws_region = st.secrets["aws"]["region"]


    llm = ChatBedrock(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        model_kwargs=dict(temperature=0),
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region=aws_region,
    
    )
    # Prepare the prompt for the model
    file_list = "\n".join(readable_files)
    prompt = (
        "You are a helpful assistant that generates a comprehensive README.md file for a software project.\n\n"
        "Here is a list of the project's readable files:\n"
        f"{file_list}\n\n"
        "Based on these files, generate a detailed README.md that includes sections like Introduction, Installation, Usage, and Contributing."
    )

    # Invoke the model
    messages = [
        ("system", "You are a helpful assistant that generates README.md files."),
        ("user", prompt),
    ]

    ai_msg = llm.invoke(messages)
    return ai_msg.content