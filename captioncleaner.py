import ollama
import srt
import os
import argparse
import json


def load_system_prompt(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def process_single_chunk(chunk_objects, system_prompt, model_name, context_size, info_str):
    if not chunk_objects:
        return []

    raw_chunk_text = srt.compose(chunk_objects)
    print(f"{info_str}...")

    response = ollama.generate(
        model=model_name,
        system=system_prompt,
        prompt=f"Fix the following SRT chunk:\n\n{raw_chunk_text}",
        options={
            "temperature": 0,
            "num_ctx": context_size
        }
    )

    try:
        return list(srt.parse(response['response']))
    except Exception as e:
        print(f"Error parsing response: {e}")
        return chunk_objects

def clean_pass(subs, system_prompt, model_name, chunk_size, context_size, offset=0, pass_name="Pass 1"):
    processed_subs = []
    n = len(subs)

    # Determine start index based on offset
    current_idx = 0
    if offset > 0:
        # Process the initial offset chunk
        end_idx = min(offset, n)
        chunk_objects = subs[0:end_idx]
        processed_subs.extend(process_single_chunk(chunk_objects, system_prompt, model_name, context_size, f"[{pass_name}] Processing blocks 1 to {end_idx}"))
        current_idx = end_idx

    # Iterate through the list of subtitle objects in chunks
    for i in range(current_idx, n, chunk_size):
        chunk_objects = subs[i : i + chunk_size]
        info_str = f"[{pass_name}] Processing blocks {i+1} to {min(i+chunk_size, n)}"
        processed_subs.extend(process_single_chunk(chunk_objects, system_prompt, model_name, context_size, info_str))

    return processed_subs

def process_srt(input_path, output_path, system_prompt, model_name, chunk_size, context_size):
    with open(input_path, "r", encoding="utf-8") as f:
        # srt.parse() handles the logic of keeping timestamps with their text
        subs = list(srt.parse(f.read()))

    # Pass 1: Standard chunking
    print(f"--- Starting Pass 1 ({len(subs)} subs) ---")
    subs = clean_pass(subs, system_prompt, model_name, chunk_size, context_size, offset=0, pass_name="Pass 1")

    # Pass 2: Offset chunking (Review)
    print(f"\n--- Starting Pass 2 (Review) ---")
    # Offset by half the chunk size to bridge boundaries
    offset = chunk_size // 2
    subs = clean_pass(subs, system_prompt, model_name, chunk_size, context_size, offset=offset, pass_name="Pass 2")

    # Final re-assembly and re-indexing (fixes 1, 2, 3 sequence)
    final_output = srt.compose(subs, reindex=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_output)
    print(f"\nSuccess! Processed {len(subs)} captions into {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean auto-generated captions based on 508 guidelines.")
    parser.add_argument("input_file", help="Path to the input SRT file")
    parser.add_argument("output_folder", help="Folder to save the cleaned SRT file")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")

    args = parser.parse_args()

    try:
        if not os.path.exists(args.config):
            raise FileNotFoundError(f"Config file not found: {args.config}")

        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)

        if not os.path.exists(args.output_folder):
            os.makedirs(args.output_folder)

        output_path = os.path.join(args.output_folder, os.path.basename(args.input_file))
        
        sys_prompt = load_system_prompt(config.get("prompt_file", "captionprompt.md"))
        
        process_srt(
            args.input_file, 
            output_path, 
            sys_prompt, 
            config.get("model_name", "llama3.1"), 
            config.get("chunk_size", 5),
            config.get("context_size", 4096)
        )
    except Exception as err:
        print(f"Error: {err}")