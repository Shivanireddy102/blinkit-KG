import json
from knowledge_graph.neo4j.connection import get_session

BASE_PATH = "data/processed"

FILES = {
    "customers": f"{BASE_PATH}/customers_clean.json",
    "stores": f"{BASE_PATH}/stores_clean.json",
    "products": f"{BASE_PATH}/products_clean.json",
    "orders": f"{BASE_PATH}/orders_clean.json",
    "order_items": f"{BASE_PATH}/order_items_clean.json",
    "delivery": f"{BASE_PATH}/delivery_partners_clean.json",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


with get_session() as session:
    print("🧹 Clearing existing graph...")
    session.run("MATCH (n) DETACH DELETE n")

    # -------------------------
    # CREATE CUSTOMER NODES
    # -------------------------
    print("Creating Customer nodes...")
    customers = load_json(FILES["customers"])
    session.run("""
    UNWIND $rows AS row
    MERGE (c:Customer {id: row.customer_id})
    SET c.name = row.name,
        c.city = row.city
    """, rows=customers)

    # -------------------------
    # CREATE STORE NODES
    # -------------------------
    print("Creating Store nodes...")
    stores = load_json(FILES["stores"])
    session.run("""
    UNWIND $rows AS row
    MERGE (s:Store {id: row.store_id})
    SET s.name = row.store_name,
        s.city = row.city
    """, rows=stores)

    # -------------------------
    # CREATE PRODUCT NODES
    # -------------------------
    print("Creating Product nodes...")
    products = load_json(FILES["products"])
    session.run("""
    UNWIND $rows AS row
    MERGE (p:Product {id: row.product_id})
    SET p.name = row.product_name,
        p.category = row.category
    """, rows=products)

    # -------------------------
    # CREATE DELIVERY PARTNER NODES
    # -------------------------
    print("Creating DeliveryPartner nodes...")
    partners = load_json(FILES["delivery"])
    session.run("""
    UNWIND $rows AS row
    MERGE (d:DeliveryPartner {id: row.partner_id})
    SET d.name = row.partner_name
    """, rows=partners)

    # -------------------------
    # CREATE ORDERS + RELATIONSHIPS
    # -------------------------
    print("Creating Order nodes and relationships...")
    orders = load_json(FILES["orders"])
    session.run("""
    UNWIND $rows AS row
    MATCH (c:Customer {id: row.customer_id})
    MATCH (s:Store {id: row.store_id})
    MERGE (o:Order {id: row.order_id})
    SET o.order_date = row.order_date
    MERGE (c)-[:PLACED]->(o)
    MERGE (o)-[:FROM]->(s)
    """, rows=orders)

    # -------------------------
    # CREATE CONTAINS RELATIONSHIPS (FIXED NULL ISSUE ✅)
    # -------------------------
    print("Creating OrderItem relationships...")
    order_items = load_json(FILES["order_items"])
    session.run("""
    UNWIND $rows AS row
    MATCH (o:Order {id: row.order_id})
    MATCH (p:Product {id: row.product_id})
    MERGE (o)-[r:CONTAINS]->(p)
    SET r.quantity = coalesce(row.quantity, 1)
    """, rows=order_items)

    # -------------------------
    # LINK DELIVERY PARTNERS (SAFE VERSION)
    # -------------------------
    print("Linking Delivery Partners...")
    session.run("""
    MATCH (o:Order)
    MATCH (d:DeliveryPartner)
    WHERE o.id CONTAINS d.id
    MERGE (o)-[:DELIVERED_BY]->(d)
    """)

    print("🎉 Knowledge Graph loaded successfully!")
