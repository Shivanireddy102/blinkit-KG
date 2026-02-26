import pandas as pd

base_path = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\csv"

stores = pd.read_csv(f"{base_path}\\stores.csv")
orders = pd.read_csv(f"{base_path}\\orders.csv")
order_items = pd.read_csv(f"{base_path}\\order_items.csv")
customers = pd.read_csv(f"{base_path}\\customers.csv")
products = pd.read_csv(f"{base_path}\\products_clean.csv")
delivery_partners = pd.read_csv(f"{base_path}\\delivery_partners.csv")
print("all csv files are loaded successfully")