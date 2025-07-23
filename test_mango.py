from pymongo import MongoClient

# Replace <db-name> with a real existing database (like "test" or "users")
uri = "mongodb+srv://admin:Macbook1234@logincluster.kybphm5.mongodb.net/test?retryWrites=true&w=majority&appName=loginCluster"

try:
    client = MongoClient(uri)
    db_list = client.list_database_names()  # Try to list databases
    print("✅ Connected successfully!")
    print("Databases:", db_list)
except Exception as e:
    print("❌ Connection failed:", e)
