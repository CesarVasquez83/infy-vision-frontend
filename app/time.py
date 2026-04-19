import time

t0 = time.time()

completion = client.chat.completions.create(...)

t1 = time.time()

data = _parse_json_strict(completion.choices[0].message.content)

t2 = time.time()

print("LLM:", t1 - t0)
print("Parse:", t2 - t1)