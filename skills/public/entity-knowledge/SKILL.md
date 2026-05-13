---
name: entity-knowledge
description: >
  A skill for querying the local database. When the user asks about
  geographic entities, people, administrative regions, organizations,
  weapons, or products, always query the local database first
  before falling back to web search or the model's own knowledge.
---

# Entity Knowledge Base Skill

## Overview

When the user asks about entities such as geographic locations, people, administrative regions, organizations, weapons, or products, query the local ClickHouse knowledge base (`entity_share_data`). The table covers ~11.5 million records across multiple entity types — geographic entities (34.8%), human (32.5%), administrative (17.5%), organization (8.0%), weapon (0.4%), and others. You have two tools available:

- **`get_table_schema`** — inspect column names, types, and comments
- **`execute_sql`** — run read-only SELECT queries

Both tools enforce read-only access. Data modification statements are rejected at the code level.

## Workflow

1. **Inspect structure first** — if unsure about columns, call `get_table_schema` before writing queries
2. **Start broad, then refine** — begin with simple conditions and a reasonable LIMIT; narrow down if too many results, broaden if too few
3. **Request full details** — once the target entity is identified, query the specific columns needed

## Important rules

1. **READ-ONLY**: Only use `SELECT` statements. The tool rejects INSERT, UPDATE, DELETE, and DDL.
2. **One table only**: All queries go against `entity_share_data`.
3. **Timestamp conversion**: Int64 timestamp columns (`date_of_birth`, `date_of_death`) must be converted with `fromUnixTimestamp()`.
