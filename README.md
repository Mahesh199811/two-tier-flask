# Two-Tier Flask Application with CI/CD

A two-tier web application (Flask + MySQL) containerized with Docker and Docker Compose, deployed on an AWS EC2 Ubuntu server, with a Jenkins CI/CD pipeline for automated build, deployment, and health verification.

## Full Project Architecture

```
                    GitHub
                       │
                       │ git push
                       ▼
                  ┌─────────┐
                  │ Jenkins │
                  │  EC2    │
                  └────┬────┘
                       │
                 Docker Compose
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
     ┌─────────────┐     ┌─────────────┐
     │ Flask       │────►│ MySQL       │
     │ Container   │     │ Container   │
     │ Port 5000   │     │ Port 3306   │
     └──────┬──────┘     └──────┬──────┘
             │                   │
           EC2 :80          Docker Volume
             │
             ▼
          Internet
```

## Technology Stack

- AWS EC2 (Ubuntu Server 24.04 LTS, x86_64)
- Python / Flask
- MySQL 8.0
- Docker / Docker Compose
- Git / GitHub
- Jenkins / Java 21

## Current Compose Architecture

```
┌─────────────────┐        ┌─────────────────┐
│   flask-app      │ ---->  │   mysql-db       │
│  (Flask, :5000)  │        │  (MySQL 8.0)     │
│  exposed on :80  │        │  volume-backed   │
└─────────────────┘        └─────────────────┘
```

- **flask** service: Python 3.12 Flask app, built from the local [Dockerfile](Dockerfile), exposed on host port `80` by default.
- **mysql** service: MySQL 8.0 official image, data persisted in the `mysql_data` named volume.

## Project Structure

```
.
├── app.py                # Flask application with health and DB check routes
├── Dockerfile             # Flask app container image definition
├── docker-compose.yml     # Multi-container orchestration (flask + mysql)
└── requirements.txt       # Python dependencies
```

## Prerequisites

- AWS EC2 instance (Ubuntu Server 24.04 LTS) with security group allowing inbound `22` (SSH), `80` (Flask), `8080` (Jenkins)
- Docker Engine + Docker Compose plugin
- Git
- Java 21 + Jenkins (for CI/CD phases)

> Port `3306` (MySQL) should **not** be exposed publicly — only accessed internally via the Docker Compose network.

## Docker Networking Note

The Flask container connects to MySQL using the Compose service name as hostname — `mysql:3306` — **not** `localhost:3306`. Docker Compose creates an internal network where the service name resolves to the container's IP.

```
flask-app ── mysql:3306 ──► mysql-db
```

## Environment Variables

Configured in [docker-compose.yml](docker-compose.yml) for the `flask` service:

| Variable      | Description             | Default       |
|---------------|--------------------------|---------------|
| `APP_PORT`    | EC2/host port published for Flask | `80`          |
| `DB_HOST`     | MySQL host/service name  | `mysql`       |
| `DB_USER`     | MySQL username           | `appuser`     |
| `DB_PASSWORD` | MySQL password           | `apppassword` |
| `DB_NAME`     | MySQL database name      | `appdb`       |

For the `mysql` service:

| Variable              | Description                       |
|-----------------------|-------------------------------------|
| `MYSQL_ROOT_PASSWORD` | Root user password                  |
| `MYSQL_DATABASE`      | Database created on first init      |
| `MYSQL_USER`          | Application user created on first init |
| `MYSQL_PASSWORD`      | Password for `MYSQL_USER`           |

> **Note:** `MYSQL_USER`/`MYSQL_PASSWORD`/`MYSQL_ROOT_PASSWORD` are only applied the **first time** MySQL initializes an empty data directory. If you change credentials later, you must remove the `mysql_data` volume (`docker compose down -v`) for the changes to take effect.

## Getting Started

1. Clone the repository onto the EC2 instance (or locally) and navigate into the project folder.
2. Build and start the containers:

   ```bash
   docker compose up -d --build
   ```

3. Verify the containers, network, and volume:

   ```bash
   docker compose ps
   docker compose logs flask
   docker compose logs mysql
   docker network ls
   docker volume ls
   ```

## API Endpoints

| Endpoint   | Method | Description                                  |
|------------|--------|-----------------------------------------------|
| `/`        | GET    | Basic health message                          |
| `/health`  | GET    | Returns application health status as JSON     |
| `/db`      | GET    | Tests the MySQL connection and returns version|

Example:

```bash
curl http://localhost/
curl http://localhost/health
curl http://localhost/db
```

Expected `/db` success response:

```json
{
  "database": "connected",
  "mysql_version": "8.0.x"
}
```

## Stopping the Application

```bash
# Stop containers, keep data
docker compose down

# Stop containers and remove volumes (wipes MySQL data)
docker compose down -v
```

## Troubleshooting

- **`Host '...' is not allowed to connect to this MySQL server`**: Usually caused by a stale `mysql_data` volume from a previous run where `MYSQL_USER` env vars weren't applied. Reset with `docker compose down -v && docker compose up -d --build`.
- **`Access denied for user 'root'@'localhost'`**: The root password in the volume doesn't match `MYSQL_ROOT_PASSWORD`. Reset the volume as above, or recover via `--skip-grant-tables` if data must be preserved.
- **Connection refused from `flask` to `mysql`**: Ensure both services are on the same Docker Compose network (default behavior) and `DB_HOST` matches the `mysql` service name.
- **`Bind for 0.0.0.0:80 failed: port is already allocated`**: Jenkins sets `COMPOSE_PROJECT_NAME=two-tier-flask` so it replaces the same Compose stack each run. If port `80` is still held by an unrelated service, stop that service or change `APP_PORT`.

## Project Roadmap

| Phase | Description                              | Status      |
|-------|-------------------------------------------|-------------|
| 1     | AWS EC2 setup + security group             | ✅ Complete |
| 2     | Ubuntu server + Docker + Java + Jenkins    | ✅ Complete |
| 3     | Flask app + Dockerfile                     | ✅ Complete |
| 4     | Docker Compose + MySQL integration         | ✅ Complete |
| 5     | Git / GitHub integration                   | ✅ Complete |
| 6     | Jenkins CI/CD pipeline                     | ✅ Complete |
| 7     | End-to-end automated deployment            | ✅ Complete |
| 8     | Production hardening                       | ✅ Complete |

### Phase 4 — Docker Compose + MySQL ✅
Verified Flask → MySQL connectivity end-to-end:

```bash
curl http://localhost/db
# Expected:
# {"database": "connected", "mysql_version": "8.0.x"}
```

### Phase 5 — Git & GitHub ✅

Put the project under version control on the EC2 server and pushed it to GitHub via SSH.

```
Ubuntu EC2 (~/two-tier-flask) → Git → GitHub Repository → Phase 6: Jenkins
```

**5.1 — Verify the project**
```bash
cd ~/two-tier-flask
git --version
```

**5.2 — Create `.gitignore`**
```
__pycache__/
*.py[cod]
venv/
.venv/
.env
.env.*
.vscode/
.idea/
.DS_Store
*.log
*.tmp
*.swp
.pytest_cache/
.coverage
```
> `docker-compose.yml` includes lab-friendly default values so the project can run locally. In Jenkins/EC2, override them through environment variables or Jenkins-managed credentials.

**5.3 — Initialize Git**
```bash
git init
git branch -M main
git config --global user.name "Mahesh Gadhave"
git config --global user.email "YOUR_GITHUB_EMAIL"
```

**5.4 — First commit**
```bash
git add .
git commit -m "Initial commit: Flask MySQL Docker Compose application"
git log --oneline
```

**5.5 — Create the GitHub repository**
Create an empty repo named `two-tier-flask` on GitHub (no README/`.gitignore`/license, since files already exist locally).

**5.6 — Connect EC2 to GitHub**
```bash
git remote add origin https://github.com/YOUR_USERNAME/two-tier-flask.git
git remote -v
```

**5.7 — SSH authentication**
```bash
ssh-keygen -t ed25519 -C "YOUR_GITHUB_EMAIL"
cat ~/.ssh/id_ed25519.pub
```
Add the public key under GitHub → Settings → SSH and GPG keys, then test:
```bash
ssh -T git@github.com
```
> Never share `~/.ssh/id_ed25519` (private key).

**5.8 — Switch remote to SSH**
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/two-tier-flask.git
git remote -v
```

**5.9 — Push**
```bash
git push -u origin main
```

**5.10 — Test the workflow**
```bash
git add README.md
git commit -m "Add project README"
git push
```

**Completion checklist**
```bash
cd ~/two-tier-flask
git status
git branch
git remote -v
git log --oneline -5
```
Phase 5 is complete once `git push` succeeds and all files (`app.py`, `Dockerfile`, `docker-compose.yml`, `.gitignore`, `README.md`) are visible on GitHub under `main`.

### Phase 6 — Jenkins CI/CD pipeline ✅
```
GitHub → Jenkins → Checkout → Build Flask Docker image → Docker Compose Deploy → Health Check (/health) → Deployment Success
```

Completed Jenkins pipeline validation from GitHub push through Docker Compose deployment and `/health` verification.

### Phase 7 — End-to-end CI/CD testing ✅
Validated that a code change pushed to GitHub is automatically built and deployed by Jenkins, with the Flask app reflecting the update.

### Phase 8 — Production improvements ✅
- Jenkins credentials / environment variable management
- GitHub webhook trigger flow
- Configurable Compose deployment variables
- Stable Docker Compose project naming for repeatable deployments
- Health check stage in Jenkins
- Persistent MySQL storage with Docker volume
- Port conflict troubleshooting and safer deployment cleanup
- Basic security hardening: MySQL is internal-only, secrets are ignored via `.gitignore`, and runtime config is environment-driven
