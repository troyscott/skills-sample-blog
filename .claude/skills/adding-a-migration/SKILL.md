---
name: adding-a-migration
description: Change the database schema by adding a numbered SQL migration and applying it with a backup. Use when the user asks to add, change or remove a field, column or table, store something new about posts, change the schema, or run migrations.
---

# Adding a migration

Follow these steps exactly.

1. Create `migrations/NNN_short_name.sql`, where NNN is one more than the highest existing number. Plain SQLite SQL.
2. Never edit, rename or delete a migration that has been applied. To fix one, add a new migration.
3. Apply it. Run exactly this command, and don't change it or run SQL by hand:

   ~~~bash
   python scripts/migrate.py --verify --backup
   ~~~

4. Read the output. Success looks like:

   ~~~text
   backup: backups/blog-20261102-121101.db
   applied: 003_add_summary.sql
   ~~~

   If it prints `error:`, stop and show the user the whole message. A failed migration is rolled back. Don't restore a backup without asking.
5. Update the code and tests that use the changed table, then run `pytest`.
