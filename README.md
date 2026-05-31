# Postgres As Caching

A small example project that demonstrates a PostgreSQL-backed key-value cache engine.

- `pg_as_cache.py`: Implements `PostgresCacheEngine` with `set`, `get`, `delete`, and `purge_expired_ttl` methods.
- `main.py`: Shows how to use the cache engine with exact and wildcard key lookups, TTL support, and delete operations.

Use this project as a reference for storing JSON data in PostgreSQL and building cache-like behavior on top of a relational database.
