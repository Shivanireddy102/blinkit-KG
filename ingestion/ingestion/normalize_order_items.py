import json
import os

BASE_PATH = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\json"
OUTPUT_PATH = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\processed"

os.makedirs(OUTPUT_PATH, exist_ok=True)

input_file = os.path.join(BASE_PATH, "order_items.json")
output_file = os.path.join(OUTPUT_PATH, "order_items_clean.json")

clean_order_items = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        clean_order_items.append({
            "order_id": record["order_id"],
            "product_id": record["product_id"]
        })

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(clean_order_items, f, indent=2)

print(f"Clean order items saved: {len(clean_order_items)} records")
