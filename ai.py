# chat_agent.py
import os, asyncio, argparse, json
from openai import AsyncOpenAI
from dotenv import load_dotenv
import tiktoken

load_dotenv()


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Return the number of tokens a plain string will use for the given model."""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def parse_args():
    p = argparse.ArgumentParser(description="Tiny configurable ChatGPT agent")
    p.add_argument("-m", "--model",     default="gpt-4o-mini")
    p.add_argument("-t", "--temp",      type=float, default=0.7, help="temperature")
    p.add_argument("-p", "--top_p",     type=float, default=1.0)
    p.add_argument("-k", "--max_tokens",type=int,   default=512)
    p.add_argument("--pp",              type=float, default=0.0, help="presence_penalty")
    p.add_argument("--fp",              type=float, default=0.0, help="frequency_penalty")
    p.add_argument("--seed",            type=int,   default=None)
    p.add_argument("--stop",            nargs="*",  default=None,
                   help="one or more stop strings")
    return p.parse_args()

ARGS = parse_args()
client = AsyncOpenAI()  # needs OPENAI_API_KEY in env

# Comprehensive system prompt for documentation generation
SYSTEM = """
You are Lightning MD, an expert documentation generator for software repositories. Your purpose is to analyze code repositories and create comprehensive, well-structured documentation that helps developers understand the codebase quickly and effectively.

RULES TO FOLLOW:
1. Focus on clarity and conciseness while maintaining technical accuracy
2. Organize documentation logically with proper hierarchy (headings, sections, subsections)
3. Prioritize explaining the most important components and their relationships
4. Include relevant code examples when they add value
5. Adapt your writing style to the specified target audience
6. Maintain consistent terminology throughout the documentation
7. Focus on explaining 'why' and 'how' not just 'what' the code does
8. When documenting APIs, include parameters, return values, exceptions, and usage examples
9. Avoid making assumptions about implementation details not clearly visible in the code
10. Follow the structure, content, and style parameters specified in the user's request

YOUR OUTPUT SHOULD BE VALID MARKDOWN THAT RENDERS PROPERLY IN STANDARD MARKDOWN VIEWERS.
YOUR RESPONSE IS THE DIRECT MARKDOWN CONTENT DISPLAYED IN THE MARKDOWN VIEWER.
"""

async def get_ai_response(user_prompt_content: str, system_prompt_content: str, args_namespace: argparse.Namespace):
    """Generates a response from the AI based on provided prompts and parameters."""
    msgs = [
        {"role": "system", "content": system_prompt_content},
        {"role": "user", "content": user_prompt_content}
    ]

    # Count tokens
    #token_count = count_tokens(user_prompt_content + system_prompt_content)
    #print(f"Token count: {token_count}")

    #if token_count > args_namespace.max_tokens:
    #    print(f"Warning: Token count exceeds max_tokens ({token_count} > {args_namespace.max_tokens})")
    #    return "Token count exceeds max_tokens"


    try:
        completion = await client.chat.completions.create(
            model=args_namespace.model,
            messages=msgs,
            temperature=args_namespace.temp,
            top_p=args_namespace.top_p,
            max_tokens=args_namespace.max_tokens,
            presence_penalty=args_namespace.pp,
            frequency_penalty=args_namespace.fp,
            stop=args_namespace.stop,
            seed=args_namespace.seed,
            stream=False,  # We want the full response for this function
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error in get_ai_response: {e}")
        return "Error in get_ai_response"

async def chat():
    msgs = [{"role": "system", "content": SYSTEM}]
    print("ChatGPT-lite (Ctrl-C to quit)\n")
    while True:
        user = input("You ▸ ")
        msgs.append({"role": "user", "content": user})

        stream = await client.chat.completions.create(
            model=ARGS.model,
            messages=msgs,
            temperature=ARGS.temp,
            top_p=ARGS.top_p,
            max_tokens=ARGS.max_tokens,
            presence_penalty=ARGS.pp,
            frequency_penalty=ARGS.fp,
            stop=ARGS.stop,
            seed=ARGS.seed,
            stream=True,
        )

        reply = ""
        print("🤖▸ ", end="", flush=True)
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            reply += delta
            print(delta, end="", flush=True)
        print()
        msgs.append({"role": "assistant", "content": reply})

if __name__ == "__main__":
    try:
        asyncio.run(chat())
    except (KeyboardInterrupt, EOFError):
        print("\nBye!")
