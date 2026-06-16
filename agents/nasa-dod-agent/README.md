# NASA/DoD Deep Agent

Iterative code review against NASA/DOD standards. Auto-fixes violations until a configurable rubric is met.

## Install

```bash
cd agents/nasa-dod-agent
uv pip install -e ".[dev]"
```

## Usage

```bash
# Set LLM credentials
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.openai.com/v1"  # optional
export OPENAI_MODEL="gpt-4o"                        # optional

# Run review
nasa-dod-agent review path/to/code

# Resume after crash
nasa-dod-agent review path/to/code

# Reset and start fresh
nasa-dod-agent review path/to/code --reset

# Undo all changes
nasa-dod-agent restore
```

## Config

Auto-generated at `.nasa-dod-agent/config.yaml` inside the target directory.
