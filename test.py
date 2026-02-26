from neo4j import GraphDatabase

uri = "neo4j+s://14e69a48.databases.neo4j.io"  # actual Aura URI
user = "neo4j"
pwd  = "0JYE6odmmCoLLSdbV8ySTxNvRt-qkSOD6_SWibUEmxk"

driver = GraphDatabase.driver(uri, auth=(user, pwd))
with driver.session() as session:
    result = session.run("RETURN 1 AS test")
    print(result.single()["test"])
driver.close()