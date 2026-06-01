# Contributing

This repository is currently maintained as a private/commercial project.

## Development Rules

- Keep route handlers thin.
- Put business logic in `app/services`.
- Put SQL in `app/repositories`.
- Update `.env.example` when adding settings.
- Update `scripts/init_db.sql` when changing schema.
- Run `scripts/check.ps1` before publishing changes.

## Commit Style

Use short imperative messages:

```text
Add chat endpoint
Improve Ollama embedding errors
Document deployment flow
```
