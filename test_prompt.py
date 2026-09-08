#!/usr/bin/env python3
"""
Test a system prompt against an inference endpoint (e.g. ai.sleepyhost.com).

Usage:
    python3 test_prompt.py                     # uses GENERIC-AI-SYSTEM-PROMPT.md
    python3 test_prompt.py --prompt-file my_prompt.txt
    python3 test_prompt.py --prompt-file my_prompt.txt --user-query "Who are you?"
    python3 test_prompt.py --api https://my.openai.proxy.com/v1/chat/completions

Requires: pip install requests
"""

import argparse
import json
import os
import sys

import requests


def load_prompt(path: str) -> str:
    """Read the system prompt from disk."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def send_request(endpoint: str, api_key: str, model: str, system_prompt: str, user_query: str, temperature: float = 0.7, max_tokens: int = 512) -> dict:
    """
    Send a chat completion request.
    Works with OpenAI-compatible endpoints. Adjust `payload` if your API
    uses a different schema (e.g. Anthropic Messages, Ollama, etc.).
    """
    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # OpenAI-compatible /v1/chat/completions payload
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_query})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    response = requests.post(endpoint, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def extract_assistant_text(response_json: dict) -> str:
    """Extract the assistant's text from an OpenAI-compatible response."""
    choices = response_json.get("choices", [])
    if not choices:
        return "(no choices in response)"
    message = choices[0].get("message", {})
    return message.get("content", "(no content in message)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Load a system prompt and test it against an API endpoint."
    )
    parser.add_argument(
        "--prompt-file",
        default="GENERIC-AI-SYSTEM-PROMPT.md",
        help="Path to the system prompt file to load. Default: GENERIC-AI-SYSTEM-PROMPT.md",
    )
    parser.add_argument(
        "--user-query",
        default="Who are you? What model are you? Who created you?",
        help="The user message to send after the system prompt.",
    )
    parser.add_argument(
        "--api",
        default="https://ai.sleepyhost.com/v1/chat/completions",
        help="Chat completions endpoint URL. Default: https://ai.sleepyhost.com/v1/chat/completions",
    )
    parser.add_argument(
        "--model",
        default="default",
        help="Model name to request. Default: 'default'",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("API_KEY", ""),
        help="API key (or set API_KEY env var).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Max tokens to generate.",
    )
    parser.add_argument(
        "--no-system-prompt",
        action="store_true",
        help="Omit the system prompt from the request. Useful for baseline comparison to verify output differences are actually caused by the prompt.",
    )
    parser.add_argument(
        "--dump-raw",
        action="store_true",
        help="Print the raw JSON response.",
    )

    args = parser.parse_args()

    # 1. Load the prompt file
    if not os.path.isfile(args.prompt_file):
        print(f"Error: Prompt file not found: {args.prompt_file}", file=sys.stderr)
        return 1

    if args.no_system_prompt:
        system_prompt = ""
        print("System prompt: DISABLED (--no-system-prompt)")
    else:
        system_prompt = load_prompt(args.prompt_file)
        print(f"Loaded prompt: {args.prompt_file} ({len(system_prompt)} chars)")
    print(f"Endpoint:      {args.api}")
    print(f"Model:         {args.model}")
    print(f"User query:    {args.user_query}")
    print("-" * 60)

    # 2. Send the request
    try:
        response_json = send_request(
            endpoint=args.api,
            api_key=args.api_key,
            model=args.model,
            system_prompt=system_prompt,
            user_query=args.user_query,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    except requests.exceptions.ConnectionError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        print("\nTip: Check that the endpoint is reachable and the URL is correct.", file=sys.stderr)
        return 1
    except requests.exceptions.HTTPError as exc:
        print(f"HTTP error: {exc}", file=sys.stderr)
        try:
            err_body = exc.response.json()
            print(f"Error body: {json.dumps(err_body, indent=2)}", file=sys.stderr)
        except Exception:
            print(f"Response text: {exc.response.text}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    # 3. Print the result
    if args.dump_raw:
        print("\n--- RAW JSON RESPONSE ---")
        print(json.dumps(response_json, indent=2))
        print("--- END RAW RESPONSE ---\n")

    assistant_text = extract_assistant_text(response_json)
    print("ASSISTANT RESPONSE:")
    print(assistant_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
