# 508 Caption Cleaner

This tool automates the cleaning and formatting of auto-generated SRT subtitles to meet Section 508 accessibility guidelines. It uses local Large Language Models (LLMs) via [Ollama](https://ollama.com/) to correct grammar, adjust timing, and ensure formatting constraints.  The code for this project is mostly generated via Gemini.

## Features

*   **508 Compliance:** Formats captions to a maximum of 32 characters per line and 2 lines per caption.
*   **Grammar & Punctuation:** Fixes capitalization, spelling, and punctuation errors common in auto-generated transcripts.
*   **Smart Merging & Splitting:** Combines fragmented captions and splits overly long ones based on linguistic breaks.
*   **Two-Pass Processing:** Runs a standard pass followed by an offset "review" pass to fix sentence fragments cut off by chunk boundaries.
*   **Thinking Mode:** Supports visualizing the "Chain of Thought" for models that support it (e.g., DeepSeek-R1, Qwen).

## Prerequisites

1.  **Python 3.x**
2.  **Ollama**: You must have Ollama installed and running.
    *   [Download Ollama](https://ollama.com/download)
3.  **LLM Model**: Pull the model you intend to use.
    ```bash
    ollama pull llama3.1
    # OR
    ollama pull qwen2.5
    ```

## Installation

1.  Clone this repository or download the files.
2.  Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```
3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Create a `config.json` file. You can start by copying the example:
    ```bash
    cp config.json.example config.json
    ```

2.  Edit `config.json` to match your environment:
    ```json
    {
        "prompt_file": "captionprompt.md",
        "model_name": "llama3.1",
        "chunk_size": 5,
        "context_size": 8192,
        "think": false
    }
    ```
    *   **model_name**: The name of the model pulled in Ollama.
    *   **chunk_size**: How many subtitle blocks to process in one API call (default: 5).
    *   **think**: Set to `true` if using a reasoning model and you want to see the thought process in the console.

## Usage

Run the script from the command line, providing the input SRT file and the destination folder for the output.

```bash
python captioncleaner.py <input_file.srt> <output_folder>
```

### Example

```bash
python captioncleaner.py raw/lecture_01.srt processed/
```

This will create `processed/lecture_01.srt`.

### Optional Arguments

*   `--config`: Specify a custom configuration file path (defaults to `config.json`).

```bash
python captioncleaner.py raw/video.srt processed/ --config my_custom_config.json
```

## Files

*   `captioncleaner.py`: Main script logic.
*   `captionprompt.md`: The system prompt containing the 508 guidelines and formatting rules.
*   `508guidelines.md`: Reference document for accessibility standards.
*   `config.json`: User configuration settings.