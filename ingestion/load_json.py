import json
import os

BASE_PATH = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\json"

files = {
    "customers": "customers.json",
    "stores": "stores.json",
    "orders": "orders.json",
    "order_items": "order_items.json",
    "products": "products_clean.json",
    "delivery_partners": "delivery_partners.json"
}

data = {}

for name, filename in files.items():
    file_path = os.path.join(BASE_PATH, filename)
    records = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    data[name] = records
    print(f"{name}: {len(records)} records loaded")

print("\nSample customer record:")
print(data["customers"][0])
