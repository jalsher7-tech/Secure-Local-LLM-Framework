import time
from ctransformers import AutoModelForCausalLM
import os # Import the OS library to handle paths correctly

# --- CONFIGURATION (THE FIX IS HERE) ---
MODEL_PATH = os.path.join("assets", "tinyllama.gguf")
PROMPT = "Write a short story about a robot who discovers music."
MAX_TOKENS_TO_GENERATE = 256

print(f"--- CPU Performance Benchmark for OpsGuard ---")
print(f"Loading model from local path: {MODEL_PATH}")

# Add a check to see if the file actually exists before we start
if not os.path.exists(MODEL_PATH):
    print(f"\n[!] ERROR: Model file not found at '{MODEL_PATH}'")
    print("Please ensure the 'assets' folder and 'tinyllama.gguf' are in the same directory as this script.")
    exit()

# 1. Load the model (this part is not timed)
try:
    llm = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        model_type="llama",
        # Use a GPU layer count of 0 to force CPU-only mode for this test
        gpu_layers=0
    )
    print("Model loaded successfully. Starting benchmark...")
except Exception as e:
    print(f"Failed to load model: {e}")
    exit()

# 2. The Benchmark Loop
token_count = 0
start_time = 0

# The 'stream=True' parameter is the key. It gives us one token at a time.
stream = llm(
    PROMPT,
    max_new_tokens=MAX_TOKENS_TO_GENERATE,
    stream=True
)

print("\nGenerating text...")
for token in stream:
    # 3. Start the timer ONLY when the first token appears.
    if start_time == 0:
        start_time = time.time()

    # We print the tokens to see it working, but 'end=""' keeps it on one line.
    print(token, end="", flush=True)

    token_count += 1

# 4. Stop the timer after the last token is generated.
end_time = time.time()

print("\n\n--- Benchmark Results ---")

if token_count > 0 and start_time > 0:
    elapsed_time = end_time - start_time
    tokens_per_second = token_count / elapsed_time

    print(f"Generated Tokens: {token_count}")
    print(f"Time Elapsed (Generation Phase): {elapsed_time:.2f} seconds")
    print(f"Performance: {tokens_per_second:.2f} tokens/second")
else:
    print("Benchmark failed: No tokens were generated.")
