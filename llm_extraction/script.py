import os
from openai import OpenAI
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

client = OpenAI(api_key="")

SYSTEM = """You are an expert criminal justice policy analyst specializing in legislative analysis.
Your job is to carefully read bill text and identify whether it increases, extends, or creates criminal penalties."""

PROMPT = """
Analyze the following bill text and determine whether it increases, extends, or creates any of the penalties below.

Bill text:
{}

Return this exact JSON format:
{{
  "jail_time": true or false,
  "prison_time": true or false,
  "parole_time": true or false,
  "probation_time": true or false,
  "pretrial_detention_time": true or false,
  "fine_amount": true or false,
  "fee_amount": true or false,
  "mandatory_minimum_time": true or false,
  "maximum_sentence_time": true or false,
  "sentence_enhancement": true or false,
  "new_crime": true or false
}}"""

bill_dir = "/Users/eljahappelson/Desktop/bills/bill_text/bill_texts/"
all_files = [f for f in os.listdir(bill_dir) if f.endswith(".txt")]
#all_files = all_files[1:100]


def process(filename):
    filepath = os.path.join(bill_dir, filename)
    try:
        text = open(filepath).read()
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": PROMPT.format(text)},
            ],
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        result["bill_id"] = filename.replace(".txt", "")
        result["url"] = f"https://www.legis.la.gov/Legis/ViewDocument.aspx?d={filename.replace('.txt', '')}"
        return result
    except Exception as e:
        print(f"Skipping {filename}: {e}")
        return None

rows = []
total = len(all_files)
completed = 0

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(process, f): f for f in all_files}
    for future in as_completed(futures):
        completed += 1
        result = future.result()
        if result:
            rows.append(result)
        print(f"[{completed}/{total}] Done: {futures[future]}")

df = pd.DataFrame(rows)

docs = pd.read_csv("/Users/eljahappelson/Desktop/bills/bill_text/documents_text.csv")
docs["bill_id"] = docs["document_url"].str.extract(r'd=(\d+)').astype(str)
docs = docs[["bill_id", "bill_number"]]

df = df.merge(docs, on="bill_id", how="left")
print(df)


penalty_cols = ["jail_time", "prison_time", "parole_time", "probation_time",
                "pretrial_detention_time",
                "mandatory_minimum_time", "maximum_sentence_time",
                "sentence_enhancement", "new_crime"]

df_flagged = df[df[penalty_cols].any(axis=1)]
print(df_flagged)

df_flagged.to_csv("increase_bills.csv")
