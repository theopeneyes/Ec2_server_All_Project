from transformers import AutoTokenizer, pipeline, logging
from auto_gptq import AutoGPTQForCausalLM


local_folder = "LLaMa-2-13b-chat-GPTQ-4bit"


tokenizer = AutoTokenizer.from_pretrained(local_folder, use_fast=True)
model = AutoGPTQForCausalLM.from_quantized(local_folder,
        model_basename="model",
        use_safetensors=True,
        trust_remote_code=True,
        device="cuda:0",
        use_triton=False,
        quantize_config=None)
        