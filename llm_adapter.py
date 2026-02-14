import ollama
import os

class LLMProvider:
    def __init__(self, config):
        self.config = config

    def query(self, prompt, system_prompt):
        raise NotImplementedError("Subclasses must implement query method")

class OllamaProvider(LLMProvider):
    def query(self, prompt, system_prompt):
        model_name = self.config.get("model_name", "llama3.1")
        context_size = self.config.get("context_size", 4096)
        think = self.config.get("think", False)

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ]

        if think:
            stream = ollama.chat(
                model=model_name,
                messages=messages,
                options={
                    "temperature": 0,
                    "num_ctx": context_size
                },
                stream=True,
                think=True
            )
            
            response_text = ""
            in_thinking = False
            
            for chunk in stream:
                # Handle thinking output
                if chunk.message.thinking and not in_thinking:
                    in_thinking = True
                    print('Thinking:\n', end='')

                if chunk.message.thinking:
                    print(chunk.message.thinking, end='', flush=True)
                elif chunk.message.content:
                    if in_thinking:
                        print('\n\nAnswer:\n', end='')
                        in_thinking = False
                    
                    content = chunk.message.content
                    response_text += content
                    print(content, end='', flush=True)
            print("\n--------------------")
            return response_text
        else:
            response = ollama.chat(
                model=model_name,
                messages=messages,
                options={
                    "temperature": 0,
                    "num_ctx": context_size
                },
                stream=False
            )
            return response['message']['content']

class GeminiProvider(LLMProvider):
    def __init__(self, config):
        super().__init__(config)
        try:
            import google.generativeai as genai
            self.genai = genai
        except ImportError:
            raise ImportError("The 'google-generativeai' package is required for Gemini provider.")

        api_key = self.config.get("api_key") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key not found. Set 'api_key' in config or GOOGLE_API_KEY env var.")
        
        self.genai.configure(api_key=api_key)

    def query(self, prompt, system_prompt):
        model_name = self.config.get("model_name", "gemini-1.5-flash")
        model = self.genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
        response = model.generate_content(prompt, generation_config=self.genai.types.GenerationConfig(temperature=0))
        return response.text

def get_provider(config):
    provider_name = config.get("provider", "ollama").lower()
    if provider_name == "ollama":
        return OllamaProvider(config)
    elif provider_name == "gemini":
        return GeminiProvider(config)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")