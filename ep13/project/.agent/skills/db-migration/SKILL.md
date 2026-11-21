---
name: db-migration
description: Change the database schema safely. Use when a task adds, renames or drops a table or column.
---
Every schema change is a numbered migration file in migrations/, never an edit of an old one.

1. Name the file NNNN_short_name.sql, where NNNN is the next number after the highest one in migrations/.
2. A migration has two sections: "-- up" and "-- down". The down section must undo the up section exactly.
3. Adding a column: it must be nullable or have a default, so old rows stay valid.
4. Renaming a column is done in three migrations over three releases: add the new column, copy and read from both, drop the old one.
5. Never drop a table in the same release that stops using it. Wait one release.
6. Run the migration on a copy of the staging database first. Write the row counts before and after in the pull request.
7. Large tables (more than a million rows) are changed in batches of 10,000 rows, with a pause between batches.
8. Tell the data team in the channel before the migration runs in production, and again when it is done.
