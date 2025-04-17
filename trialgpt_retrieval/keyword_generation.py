__author__ = "qiao"

"""
generate the search keywords for each patient
"""

import json
import os
from openai import AzureOpenAI, OpenAI

import sys


if os.getenv("OPENAI_ENDPOINT"):
    client = AzureOpenAI(
        api_version="2023-09-01-preview",
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
else:
    import httpx
    http_client = httpx.Client()
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        http_client=http_client
    )


def get_keyword_generation_messages(note):
	system = 'You are a helpful assistant and your task is to help search relevant clinical trials for a given patient description. Please first summarize the main medical problems of the patient. Then generate up to 32 key conditions for searching relevant clinical trials for this patient. The key condition list should be ranked by priority. Please output only a JSON dict formatted as Dict{{"summary": Str(summary), "conditions": List[Str(condition)]}}.'

	prompt =  f"Here is the patient description: \n{note}\n\nJSON output:"

	messages = [
		{"role": "system", "content": system},
		{"role": "user", "content": prompt}
	]
	
	return messages


if __name__ == "__main__":
	# the corpus: trec_2021, trec_2022, or sigir
	corpus = sys.argv[1]

	# the model index to use
	model = sys.argv[2]

	outputs = {}
	
	with open(f"dataset/{corpus}/queries.jsonl", "r") as f:
		for line in f.readlines():
			entry = json.loads(line)
			messages = get_keyword_generation_messages(entry["text"])

			response = client.chat.completions.create(
				model=model,
				messages=messages,
				temperature=0,
			)

			output = response.choices[0].message.content
			output = output.strip("`").strip("json")
			
			outputs[entry["_id"]] = json.loads(output)

			with open(f"results/retrieval_keywords_{model}_{corpus}.json", "w") as f:
				json.dump(outputs, f, indent=4)
