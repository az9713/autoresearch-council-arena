# Build a Minimal LLM Evaluation Loop in Python

If you want to stop manually testing prompts and start running systematic experiments, an evaluation loop is the right tool. This tutorial shows you how to build one using the OpenRouter API.

## What You Need

- Python 3.10+
- An OpenRouter API key (sign up at openrouter.ai)
- `httpx` installed: `pip install httpx`

## Step 1: Make an LLM API Call

```python
import httpx

API_KEY = "sk-or-your-key-here"

def call_llm(prompt: str) -> str:
    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    data = response.json()
    return data["choices"][0]["message"]["content"]
```

This sends a prompt to the model and returns the text response.

## Step 2: Define a Metric

Your metric function scores the LLM output. Higher is better. Here is a simple example that scores based on length:

```python
def score(text: str) -> float:
    words = len(text.split())
    return min(words / 200, 1.0)
```

In a real experiment, replace this with something meaningful — F1 score, BLEU, a rubric evaluated by another LLM, or any number you can extract from the output.

## Step 3: Write the Evaluation Loop

```python
best_score = 0.0
artifact = open("artifact.txt").read()

for i in range(20):
    prompt = f"Improve this text:\n\n{artifact}"
    candidate = call_llm(prompt)
    new_score = score(candidate)

    if new_score > best_score:
        best_score = new_score
        artifact = candidate
        with open("artifact.txt", "w") as f:
            f.write(artifact)
        print(f"Iter {i}: KEEP  score={new_score:.2f}")
    else:
        print(f"Iter {i}: DISCARD  score={new_score:.2f}  best={best_score:.2f}")
```

The loop generates a candidate, scores it, and keeps it only if the score improves. This is greedy hill-climbing: always move uphill, never sideways.

## Step 4: Run It

```bash
python loop.py
```

You should see output like:

```
Iter 0: KEEP  score=0.85
Iter 1: DISCARD  score=0.81  best=0.85
Iter 2: KEEP  score=0.91
Iter 3: DISCARD  score=0.88  best=0.91
```

The artifact file is updated whenever a better version is found.

## What's Next

This basic loop works but there are several things you could add:

- Querying multiple models in parallel and picking the best candidate
- Tracking costs so you don't overspend
- Saving all results to a file for later analysis
- Using git to version each improvement
- Adding a budget so the loop stops automatically
