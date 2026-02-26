import os
import json
import pandas as pd
from backend.services.config import DATA_PATH

CSV_DATA_PATH = os.path.join(DATA_PATH, "csv")
JSON_DATA_PATH = os.path.join(DATA_PATH, "json")


class DataLoader:
    def __init__(self):
        self.csv_path = CSV_DATA_PATH
        self.json_path = JSON_DATA_PATH

    def _load_products_from_csv(self, filename="products_clean.csv"):
        file_path = os.path.join(self.csv_path, filename)
        if not os.path.exists(file_path):
            return []

        df = pd.read_csv(file_path)
        df = df.fillna("")
        records = df.to_dict(orient="records")
        print(f"✅ Loaded CSV: {filename} ({len(records)} records)")
        return records

    def _load_products_from_json(self, filename="products_clean.json"):
        file_path = os.path.join(self.json_path, filename)
        if not os.path.exists(file_path):
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Supports JSON array or JSONL
        products = []
        if "\n" in content and not content.startswith("["):
            for line in content.split("\n"):
                line = line.strip()
                if line:
                    products.append(json.loads(line))
        else:
            data = json.loads(content)
            if isinstance(data, list):
                products = data
            elif isinstance(data, dict):
                products = [data]

        print(f"✅ Loaded JSON: {filename} ({len(products)} records)")
        return products

    def load_all_data(self):
        """
        Returns: List[dict] products
        Preference: CSV products_clean.csv first, fallback to JSON.
        """
        products = self._load_products_from_csv("products_clean.csv")
        if products:
            return products

        products = self._load_products_from_json("products_clean.json")
        return products