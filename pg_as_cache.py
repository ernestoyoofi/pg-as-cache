import json
import psycopg2
from psycopg2 import extras

class PostgresCacheEngine:
  def __init__(self, db_config):
    self.config = db_config
    self._bootstrap_db()

  def _get_connection(self):
    return psycopg2.connect(**self.config)

  def _bootstrap_db(self):
    sql_init = """
    CREATE UNLOGGED TABLE IF NOT EXISTS pure_kv_cache (
      key TEXT PRIMARY KEY,
      value JSONB,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
      expired_at TIMESTAMP WITH TIME ZONE
    );
    
    CREATE INDEX IF NOT EXISTS idx_kv_cache_value_gin ON pure_kv_cache USING GIN (value);
    
    CREATE INDEX IF NOT EXISTS idx_kv_cache_expired_at ON pure_kv_cache (expired_at);
    """
    conn = self._get_connection()
    try:
      with conn.cursor() as cur:
        cur.execute(sql_init)
      conn.commit()
    except Exception as e:
      conn.rollback()
      raise RuntimeError(f"Failed to bootstrap database schema: {e}")
    finally:
      conn.close()

  def set(self, key: str, value: dict, ttl_seconds: int = None):
    sql = """
    INSERT INTO pure_kv_cache (key, value, expired_at)
    VALUES (
      %s, 
      %s, 
      CASE WHEN %s::INT IS NULL THEN NULL ELSE NOW() + (%s::INT || ' seconds')::INTERVAL END
    )
    ON CONFLICT (key) 
    DO UPDATE SET 
      value = EXCLUDED.value,
      expired_at = EXCLUDED.expired_at,
      created_at = NOW();
    """
    conn = self._get_connection()
    try:
      with conn.cursor() as cur:
        cur.execute(sql, (key, json.dumps(value), ttl_seconds, ttl_seconds))
      conn.commit()
      return True
    except Exception as e:
      conn.rollback()
      print(f"Error during SET operation: {e}")
      return False
    finally:
      conn.close()

  def get(self, key_pattern: str):
    conn = self._get_connection()
    results = {}
    
    try:
      with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
        if '*' in key_pattern:
          sql_pattern = key_pattern.replace('*', '%')
          sql = """
            SELECT key, value FROM pure_kv_cache 
            WHERE key LIKE %s AND (expired_at IS NULL OR expired_at > NOW());
          """
          cur.execute(sql, (sql_pattern,))
          rows = cur.fetchall()
          for row in rows:
            results[row['key']] = row['value']
          return results
        else:
          sql = """
            SELECT value FROM pure_kv_cache 
            WHERE key = %s AND (expired_at IS NULL OR expired_at > NOW());
          """
          cur.execute(sql, (key_pattern,))
          row = cur.fetchone()
          if row:
            return row['value']
          return None
    except Exception as e:
      print(f"Error during GET operation: {e}")
      return None
    finally:
      conn.close()

  def delete(self, key_pattern: str):
    conn = self._get_connection()
    try:
      with conn.cursor() as cur:
        if '*' in key_pattern:
          sql_pattern = key_pattern.replace('*', '%')
          sql = "DELETE FROM pure_kv_cache WHERE key LIKE %s;"
          cur.execute(sql, (sql_pattern,))
        else:
          sql = "DELETE FROM pure_kv_cache WHERE key = %s;"
          cur.execute(sql, (key_pattern,))
        
        deleted_rows = cur.rowcount
      conn.commit()
      return deleted_rows
    except Exception as e:
      conn.rollback()
      print(f"Error during DELETE operation: {e}")
      return 0
    finally:
      conn.close()

  def purge_expired_ttl(self):
    sql = "DELETE FROM pure_kv_cache WHERE expired_at < NOW();"
    conn = self._get_connection()
    try:
      with conn.cursor() as cur:
        cur.execute(sql)
        deleted = cur.rowcount
      conn.commit()
      return deleted
    except Exception as e:
      conn.rollback()
      print(f"Error while purging TTL expired data: {e}")
      return 0
    finally:
      conn.close()