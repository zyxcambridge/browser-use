# Browser Use

Make websites accessible for AI agents.

## Quickstart

```bash
# 1. Build the package with uv
uv build

# 2. Install the built wheel (replace the path if your version is different)
pip install dist/browser_use-0.1.45-py3-none-any.whl

python find_apply_jobs.py

```

## Roadmap

- [ ] **Long-running Execution**: Currently, running the script (e.g., `python find_apply_jobs.py`) does **not** keep running indefinitely and may terminate unexpectedly. Improving stability and enabling continuous operation is a planned enhancement.

## Installation

Browser Use requires **Python 3.11+**. We recommend using [uv](https://docs.astral.sh/uv/) for Python environment management.

### Create and activate a virtual environment

```bash
uv venv --python 3.11
source .venv/bin/activate
```

### Install dependencies

```bash
uv sync
```

### Build and install the package

```bash
uv build
pip install ./dist/browser_use-0.1.45-py3-none-any.whl
```

## Configuration

Copy the example environment file and set your API keys:

```bash
cp .env.example .env
```

Or manually create a `.env` file with the API key for the models you want to use:

```env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=
AZURE_ENDPOINT=
AZURE_OPENAI_API_KEY=
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
GROK_API_KEY=
NOVITA_API_KEY=
```

You can use any LLM model supported by LangChain. See [LangChain Models](https://python.langchain.com/docs/integrations/llms/) for available options and their specific API key requirements.

## Usage Example

Try the example script after installation:

```bash
uv run examples/simple.py
```

This will launch an agent that interacts with kayak.com to find a flight.

## Development

- Run the linter/formatter:

```bash
uv run ruff format examples/simple.py
```

- Explore more demos in the `examples/` directory.

## License

[MIT](LICENSE)
