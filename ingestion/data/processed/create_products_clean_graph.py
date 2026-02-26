print("🔥 FIXED — JSON PARSER WITH AUTO-DETECTION 🔥")

import json
import os

BASE = r"C:\Users\gcboo\OneDrive\Desktop\Neo4jImport\data\processed"
INPUT = os.path.join(BASE, "products_clean.json")
OUTPUT = os.path.join(BASE, "products_clean_graph.json")

products = []

# First, try to detect the JSON format
with open(INPUT, "r", encoding="utf-8") as f:
    first_line = f.readline().strip()
    f.seek(0)  # Reset to beginning
    
    # Check if it's a JSON array
    if first_line.startswith('['):
        print("📋 Detected: JSON Array format")
        try:
            # Load entire file as JSON array
            data = json.load(f)
            if isinstance(data, list):
                products = data
            else:
                products = [data]
        except json.JSONDecodeError as e:
            print(f"❌ Error reading JSON array: {e}")
            print("💡 Trying line-by-line parsing...")
            
            # Fallback: try reading line by line
            f.seek(0)
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and line not in ['[', ']', '[,', '],']:
                    # Remove trailing comma if exists
                    line = line.rstrip(',')
                    try:
                        products.append(json.loads(line))
                    except json.JSONDecodeError:
                        print(f"⚠️ Skipping invalid line {line_num}")
                        continue
    
    # Check if it's JSONL (JSON Lines) format
    elif first_line.startswith('{'):
        print("📋 Detected: JSON Lines (JSONL) format")
        f.seek(0)
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    products.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"⚠️ Skipping invalid line {line_num}: {e}")
                    continue
    
    else:
        print("❌ Unknown JSON format")
        print(f"First line: {first_line[:100]}")

print(f"✅ Loaded {len(products)} products")

if not products:
    print("❌ No products loaded! Check your input file.")
    exit(1)

# Show sample of loaded data
print("\n📊 Sample product:")
print(json.dumps(products[0], indent=2)[:300])

# Create graph-ready products
graph_products = []

for p in products:
    # Handle different possible field names
    product_id = p.get("product_id") or p.get("id") or p.get("Product ID")
    title = (
        p.get("product_name") or 
        p.get("title") or 
        p.get("Product Name") or 
        p.get("name") or 
        str(product_id)
    )
    
    if product_id:  # Only add if we have an ID
        graph_products.append({
            "product_id": str(product_id),
            "title": str(title)
        })

print(f"\n✅ Processed {len(graph_products)} valid products")

# Save to output file
try:
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(graph_products, f, indent=2, ensure_ascii=False)
    
    print(f"✅ products_clean_graph.json CREATED")
    print(f"📁 Location: {OUTPUT}")
    print(f"📊 Total products: {len(graph_products)}")
    
except Exception as e:
    print(f"❌ Error writing output file: {e}")