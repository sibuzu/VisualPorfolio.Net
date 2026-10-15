## ADDED Requirements

### Requirement: Deploy Strategy Report independently
The repository SHALL provide `docker/strategy-report/` Dockerfiles and Compose configuration with unique frontend/backend service names on `sibuzu-net`, without mounting Visual Portfolio's project or account database directories.

The backend SHALL bind mount root `data/reports/` for original sources and per-report `config.json` files. The separate Strategy Report data volume SHALL hold its performance index database and migration backups.

#### Scenario: Start Strategy Report containers
- **WHEN** an operator builds and starts the Strategy Report Compose stack
- **THEN** its frontend and backend SHALL become healthy without replacing or stopping Visual Portfolio containers

### Requirement: Serve one public origin
The deployment configuration SHALL route `https://strategyreport.sibuzu.com/` to the Strategy Report frontend and proxy `/api/` requests to its backend on the internal container network.

#### Scenario: Browser request
- **WHEN** a browser loads the Strategy Report hostname and submits a report to `/api/`
- **THEN** the frontend SHALL load over HTTPS and the API request SHALL reach only the Strategy Report backend

### Requirement: Provide deployment verification and rollback
The repository SHALL document the external DNS/tunnel step, a smoke check for the homepage, health endpoint, and example report import, plus a rollback that leaves Visual Portfolio data and services intact.

#### Scenario: Route cannot be enabled
- **WHEN** the DNS or tunnel change has not been applied
- **THEN** operators SHALL still be able to verify the local containers and SHALL not report the public URL as live

#### Scenario: Roll back new site
- **WHEN** Strategy Report deployment fails acceptance checks
- **THEN** operators SHALL be able to remove its route and stop its containers without deleting or modifying Visual Portfolio data
