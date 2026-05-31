import json
from pg_as_cache import PostgresCacheEngine

db_credentials = {
  "host": "localhost",
  "database": "cacheing",
  "user": "postgres",
  "password": "cacheing",
  "port": 5432
}

def run_test():
  # 1. Inisialisasi Cache Engine
  print("[1] Connecting to Postgres and initializing table...")
  cache = PostgresCacheEngine(db_config=db_credentials)

  # 2. SET operation (Insert / Update) similar to Redis style
  print("\n[2] Performing SET operation...")
  cache.set(key="session-abcd", value={"name": "A", "phone": "12345"}, ttl_seconds=60)
  cache.set(key="session-xyz", value={"name": "B", "phone": "67890"}, ttl_seconds=120)
  cache.set(key="user-profile:10", value={"role": "admin", "active": True}) # Without TTL (Persistent)
  print("-> Finished inserting/updating several entries.")

  # 3. Exact GET operation
  print("\n[3] Attempting exact GET (session-abcd)...")
  data_tunggal = cache.get("session-abcd")
  print(f"Result: {data_tunggal}")

  # 4. GET operation using Wildcard (*) to fetch all data matching the prefix pattern
  print("\n[4] Attempting GET using wildcard (session-*)...")
  banyak_data = cache.get("session-*")
  print(f"Result (Dictionary of all sessions):\n{json.dumps(banyak_data, indent=2)}")

  # 5. DELETE operation using Wildcard (*)
  print("\n[5] Attempting DELETE using wildcard (session-*)...")
  jumlah_dihapus = cache.delete("session-*")
  print(f"Result: Successfully deleted {jumlah_dihapus} cache entries.")

  # 6. Verify effect after bulk deletion
  print("\n[6] Rechecking data after deletion...")
  print(f"Fetch session-abcd again: {cache.get('session-abcd')} (Should be None)")
  print(f"Fetch user-profile:10 : {cache.get('user-profile:10')} (Should remain because it does not match the pattern)")

if __name__ == "__main__":
  run_test()