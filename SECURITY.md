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
- configure a strong `JWT_SECRET_KEY`
- use JWT login with organization memberships for normal users
- use tenant-scoped API keys for integrations and revoke unused keys
- require admin role membership or admin role headers for operational endpoints such as `/metrics`
- restrict CORS
- configure HTTPS

## Reporting

For private commercial usage, handle security reports through the project owner directly.
