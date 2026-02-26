import json
import os

BASE_PATH = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\json"
OUTPUT_PATH = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\processed"

os.makedirs(OUTPUT_PATH, exist_ok=True)

input_file = os.path.join(BASE_PATH, "customers.json")
output_file = os.path.join(OUTPUT_PATH, "customers_clean.json")

clean_customers = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        clean_customers.append({
            "customer_id": record["customer_id"],
            "name": record["name"]
        })

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(clean_customers, f, indent=2)

print(f"Clean customers saved: {len(clean_customers)} records")
