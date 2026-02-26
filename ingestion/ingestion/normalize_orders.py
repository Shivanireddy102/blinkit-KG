import json
import os

BASE_PATH = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\json"
OUTPUT_PATH = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\processed"

os.makedirs(OUTPUT_PATH, exist_ok=True)

input_file = os.path.join(BASE_PATH, "orders.json")
output_file = os.path.join(OUTPUT_PATH, "orders_clean.json")

clean_orders = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        clean_orders.append({
            "order_id": record["order_id"],
            "customer_id": record["customer_id"],
            "store_id": record["store_id"],
            "delivery_partner_id": record["delivery_partner_id"]
        })

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(clean_orders, f, indent=2)

print(f"Clean orders saved: {len(clean_orders)} records")
