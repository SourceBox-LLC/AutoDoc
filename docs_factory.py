import streamlit as st
from langchain_aws import ChatBedrock

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


def generate_readme(readable_files, optional_prompt=""):
    """
    Generates README content based on the dictionary of readable files and their contents using the Anthropic ChatBedrock model.


    Args:
        readable_files (dict of str: str): Dictionary mapping file paths to their content.

    Returns:
        str: Generated README content.
    """
    # Prepare the prompt for the model
    files_info = "\n\n".join([f"### {file}\n{content}" for file, content in readable_files.items()])
    prompt = (
        "You are a helpful assistant that generates a comprehensive README.md file for a software project.\n\n"
        "Here is the content of the project's readable files:\n"
        f"{files_info}\n\n"
        "Based on these files, generate a detailed README.md that includes sections like Introduction, Installation, Usage, and Contributing."
        "You MUST take this second prompt into consideration when creating the README.md file:"
        f"{optional_prompt}\n\n"
    )


    # Invoke the model
    messages = [
        ("system", "You are a helpful assistant that generates README.md files."),
        ("user", prompt),
    ]

    ai_msg = llm.invoke(messages)
    return ai_msg.content