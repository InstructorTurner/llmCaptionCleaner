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

def process_srt(input_path, output_path, system_prompt, model_name, chunk_size):
    with open(input_path, "r", encoding="utf-8") as f:
        # srt.parse() handles the logic of keeping timestamps with their text
        subs = list(srt.parse(f.read()))

    processed_subs = []
    
    # Iterate through the list of subtitle objects in chunks
    for i in range(0, len(subs), chunk_size):
        chunk_objects = subs[i : i + chunk_size]
        
        # srt.compose() re-assembles the objects into a valid SRT string for the LLM
        raw_chunk_text = srt.compose(chunk_objects)
        
        print(f"Processing subtitle blocks {i+1} to {min(i+chunk_size, len(subs))}...")
        
        response = ollama.generate(
            model=model_name,
            system=system_prompt,
            prompt=f"Fix the following SRT chunk:\n\n{raw_chunk_text}",
            options={"temperature": 0}
        )
        
        try:
            # Parse the LLM response back into objects
            cleaned_chunk = list(srt.parse(response['response']))
            processed_subs.extend(cleaned_chunk)
        except Exception as e:
            print(f"Error parsing response for chunk starting at {i+1}: {e}")
            # If the LLM garbles the format, we keep the original to avoid data loss
            processed_subs.extend(chunk_objects)

    # Final re-assembly and re-indexing (fixes 1, 2, 3 sequence)
    final_output = srt.compose(processed_subs, reindex=True)
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
        
        process_srt(args.input_file, output_path, sys_prompt, config.get("model_name", "llama3.1"), config.get("chunk_size", 5))
    except Exception as err:
        print(f"Error: {err}")