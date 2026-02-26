import json
import os

BASE_PATH = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\json"
OUTPUT_PATH = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\processed"

os.makedirs(OUTPUT_PATH, exist_ok=True)

input_file = os.path.join(BASE_PATH, "stores.json")
output_file = os.path.join(OUTPUT_PATH, "stores_clean.json")

clean_stores = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        clean_stores.append({
            "store_id": record["store_id"],
            "name": record["name"]
        })

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(clean_stores, f, indent=2)

print(f"Clean stores saved: {len(clean_stores)} records")
