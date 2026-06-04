# Security Policy

## Secrets

Do not commit:

- `.env`
- API keys
- customer files
- database dumps
- MinIO data
- production credentials

If a key is exposed, rotate it immediately in the provider dashboard.

## Local Development

Default credentials in `docker-compose.yml` are for local development only.

Before production:

- change MinIO credentials
- change database credentials
- disable debug mode
- disable anonymous access
- configure a strong API auth token or replace the MVP auth layer
- require admin role headers for operational endpoints such as `/metrics`
- restrict CORS
- enable authentication
- configure HTTPS

## Reporting

For private commercial usage, handle security reports through the project owner directly.
