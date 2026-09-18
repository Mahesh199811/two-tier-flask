# Two-Tier Flask + MySQL Application with Jenkins CI/CD

This project documents a complete beginner-friendly DevOps workflow: a Flask web application connects to a MySQL database, both services run as Docker containers with Docker Compose, and Jenkins deploys the application automatically after code is pushed to GitHub.

The project is complete through Phase 8: EC2 setup, Docker, Flask, MySQL, GitHub, Jenkins CI/CD, end-to-end deployment, and basic production hardening.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Application Endpoints](#application-endpoints)
- [Environment Variables](#environment-variables)
- [Phase 1: Create the EC2 Server](#phase-1-create-the-ec2-server)
- [Phase 2: Connect to Ubuntu](#phase-2-connect-to-ubuntu)
- [Phase 3: Prepare Ubuntu](#phase-3-prepare-ubuntu)
- [Phase 4: Install Docker and Docker Compose](#phase-4-install-docker-and-docker-compose)
- [Phase 5: Install Java and Jenkins](#phase-5-install-java-and-jenkins)
- [Phase 6: Give Jenkins Docker Access](#phase-6-give-jenkins-docker-access)
- [Phase 7: Run the App Manually with Docker Compose](#phase-7-run-the-app-manually-with-docker-compose)
- [Phase 8: Configure Jenkins CI/CD](#phase-8-configure-jenkins-cicd)
- [GitHub Webhook Setup](#github-webhook-setup)
- [End-to-End Test](#end-to-end-test)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)
- [Rollback Strategy](#rollback-strategy)
- [Clean Up](#clean-up)
- [Learning Outcomes](#learning-outcomes)
- [External References](#external-references)

## Project Overview

The goal is to learn how a real deployment pipeline works at a small scale.

Flow:

```text
Developer machine
    |
    | git push
    v
GitHub repository
    |
    | webhook / Jenkins build trigger
    v
Jenkins on EC2
    |
    | docker compose build
    | docker compose down
    | docker compose up -d
    v
Flask container + MySQL container
    |
    v
Application available on EC2 public IP, port 80
```

The project teaches:

- Linux server basics
- AWS EC2 and security groups
- Docker images and containers
- Docker Compose multi-container networking
- Flask API development
- MySQL container deployment with persistent storage
- Git and GitHub workflow
- Jenkins pipeline automation
- Basic deployment troubleshooting

## Architecture

```text
                    GitHub
                       |
                       | git push
                       v
                  +---------+
                  | Jenkins |
                  |   EC2   |
                  +----+----+
                       |
                       | docker compose
                       v
              +-------------------+
              | Docker Compose    |
              |                   |
              |  +-------------+  |
Internet ---> |  | Flask       |  |
   :80        |  | port 5000   |  |
              |  +------+------+  |
              |         |         |
              |         | mysql:3306
              |         v         |
              |  +-------------+  |
              |  | MySQL 8.0   |  |
              |  | port 3306   |  |
              |  +------+------+  |
              |         |         |
              |  Docker volume    |
              +-------------------+
```

Important networking idea:

- Users access Flask through the EC2 public IP on host port `80`.
- Flask runs inside the container on port `5000`.
- MySQL runs inside the Docker network on port `3306`.
- MySQL is not exposed to the internet.
- Flask connects to MySQL using the Docker Compose service name `mysql`, not `localhost`.

## Technology Stack

| Layer | Tool |
|---|---|
| Cloud server | AWS EC2 Ubuntu |
| Operating system | Ubuntu Server 24.04 LTS |
| Backend | Python Flask |
| Database | MySQL 8.0 |
| Containerization | Docker |
| Multi-container orchestration | Docker Compose |
| Source control | Git and GitHub |
| CI/CD | Jenkins |
| Runtime dependency | Java 21 for Jenkins |

## Repository Structure

```text
two-tier-flask/
|-- app.py
|-- requirements.txt
|-- Dockerfile
|-- docker-compose.yml
|-- Jenkinsfile
|-- .gitignore
`-- README.md
```

File explanation:

| File | Purpose |
|---|---|
| `app.py` | Flask application with `/`, `/health`, and `/db` routes |
| `requirements.txt` | Python packages required by the Flask app |
| `Dockerfile` | Builds the Flask application image |
| `docker-compose.yml` | Runs Flask and MySQL together |
| `Jenkinsfile` | Defines the Jenkins CI/CD pipeline |
| `.gitignore` | Prevents cache, virtual environment, and secret files from being committed |
| `README.md` | Project documentation |

## Application Endpoints

| Endpoint | Purpose |
|---|---|
| `/` | Confirms the Flask application is running |
| `/health` | Used by Jenkins to verify deployment health |
| `/db` | Tests Flask-to-MySQL connectivity and returns the MySQL version |

Test locally or on EC2:

```bash
curl http://localhost/
curl http://localhost/health
curl http://localhost/db
```

If testing from your browser using EC2:

```text
http://<EC2_PUBLIC_IP>/
http://<EC2_PUBLIC_IP>/health
http://<EC2_PUBLIC_IP>/db
```

Expected `/health` response:

```json
{
  "status": "healthy"
}
```

Expected `/db` response:

```json
{
  "database": "connected",
  "mysql_version": "8.0.x"
}
```

## Environment Variables

The Compose file includes defaults so the project can run quickly in a lab environment.

Flask service variables:

| Variable | Default | Meaning |
|---|---|---|
| `APP_PORT` | `80` | Host/EC2 port published for Flask |
| `DB_HOST` | `mysql` | MySQL Compose service name |
| `DB_USER` | `appuser` | MySQL application user |
| `DB_PASSWORD` | `apppassword` | MySQL application password |
| `DB_NAME` | `appdb` | MySQL database name |

MySQL service variables:

| Variable | Default | Meaning |
|---|---|---|
| `MYSQL_ROOT_PASSWORD` | `rootpassword` | MySQL root password |
| `MYSQL_DATABASE` | `appdb` | Database created during first MySQL initialization |
| `MYSQL_USER` | `appuser` | Application database user |
| `MYSQL_PASSWORD` | `apppassword` | Password for `MYSQL_USER` |

Important MySQL volume note:

MySQL initialization variables are applied only when the data directory is empty. If you change `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`, or `MYSQL_DATABASE` after the first run, remove the volume before restarting:

```bash
docker compose down -v
docker compose up -d --build
```

## Phase 1: Create the EC2 Server

Recommended EC2 settings:

| Setting | Value |
|---|---|
| AMI | Ubuntu Server 24.04 LTS |
| Architecture | x86_64 |
| Instance type | `t2.micro` or `t3.micro` for learning |
| Storage | 20 GB or more |
| Public IP | Enabled |
| Key pair | Create or use an existing SSH key |
| VPC | Default VPC is fine for this project |

Security group rules:

| Port | Protocol | Source | Purpose |
|---|---|---|---|
| `22` | TCP | Your IP only | SSH access |
| `80` | TCP | `0.0.0.0/0` | Flask application |
| `8080` | TCP | Your IP only | Jenkins UI |

Do not expose MySQL port `3306` publicly. The MySQL container should only be reachable inside the Docker Compose network.

## Phase 2: Connect to Ubuntu

From your local terminal:

```bash
chmod 400 <KEY_FILE>.pem
ssh -i <KEY_FILE>.pem ubuntu@<EC2_PUBLIC_IP>
```

Verify the connected user:

```bash
whoami
```

Expected:

```text
ubuntu
```

Check OS details:

```bash
cat /etc/os-release
```

Check server resources:

```bash
free -h
df -h
nproc
```

## Phase 3: Prepare Ubuntu

Update packages:

```bash
sudo apt update
sudo apt upgrade -y
```

Install useful command-line tools:

```bash
sudo apt install -y \
  git \
  curl \
  wget \
  vim \
  unzip \
  ca-certificates \
  gnupg \
  lsb-release
```

Verify Git:

```bash
git --version
```

## Phase 4: Install Docker and Docker Compose

Remove conflicting old packages if they exist:

```bash
sudo apt remove -y docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc || true
```

Add Docker's official apt repository:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

Create the Docker apt source:

```bash
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
```

Install Docker Engine and Docker Compose plugin:

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Start and enable Docker:

```bash
sudo systemctl enable docker
sudo systemctl start docker
sudo systemctl status docker
```

Verify Docker:

```bash
sudo docker run hello-world
docker --version
docker compose version
```

Allow the Ubuntu user to run Docker without `sudo`:

```bash
sudo usermod -aG docker ubuntu
exit
```

Reconnect:

```bash
ssh -i <KEY_FILE>.pem ubuntu@<EC2_PUBLIC_IP>
```

Test Docker without `sudo`:

```bash
docker ps
docker compose version
```

## Phase 5: Install Java and Jenkins

Jenkins requires Java. Install OpenJDK 21:

```bash
sudo apt update
sudo apt install -y fontconfig openjdk-21-jre
java -version
```

Add the Jenkins LTS apt repository:

```bash
sudo wget -O /etc/apt/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key
```

```bash
echo "deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc]" \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null
```

Install Jenkins:

```bash
sudo apt update
sudo apt install -y jenkins
```

Enable and start Jenkins:

```bash
sudo systemctl enable jenkins
sudo systemctl start jenkins
sudo systemctl status jenkins
```

Get the initial admin password:

```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

Open Jenkins in your browser:

```text
http://<EC2_PUBLIC_IP>:8080
```

Recommended setup:

1. Paste the initial admin password.
2. Install suggested plugins.
3. Create the first admin user.
4. Confirm Jenkins URL.

Recommended plugins for this project:

- Git
- GitHub
- Pipeline
- Pipeline: SCM Step

Most of these are normally included when you choose "Install suggested plugins."

## Phase 6: Give Jenkins Docker Access

Jenkins runs as the Linux user `jenkins`. That user must be able to communicate with the Docker daemon.

Add Jenkins to the Docker group:

```bash
sudo usermod -aG docker jenkins
```

Restart Jenkins so the new group membership is applied:

```bash
sudo systemctl restart jenkins
sudo systemctl status jenkins
```

Verify Jenkins can run Docker:

```bash
sudo -u jenkins docker ps
sudo -u jenkins docker compose version
```

If these commands work, Jenkins can run the Docker commands inside the pipeline.

## Phase 7: Run the App Manually with Docker Compose

Clone the repository on the EC2 server:

```bash
cd ~
git clone git@github.com:<YOUR_GITHUB_USERNAME>/two-tier-flask.git
cd two-tier-flask
```

If you use HTTPS instead of SSH:

```bash
git clone https://github.com/<YOUR_GITHUB_USERNAME>/two-tier-flask.git
cd two-tier-flask
```

Check files:

```bash
ls -la
```

Build and start the application:

```bash
docker compose up -d --build
```

Check containers:

```bash
docker compose ps
```

Check logs:

```bash
docker compose logs
docker compose logs flask
docker compose logs mysql
```

Test from the EC2 server:

```bash
curl http://localhost/
curl http://localhost/health
curl http://localhost/db
```

Test from your browser:

```text
http://<EC2_PUBLIC_IP>/
http://<EC2_PUBLIC_IP>/health
http://<EC2_PUBLIC_IP>/db
```

Stop the app but keep database data:

```bash
docker compose down
```

Stop the app and delete MySQL data:

```bash
docker compose down -v
```

## Phase 8: Configure Jenkins CI/CD

The `Jenkinsfile` is already included in this repository.

Pipeline stages:

| Stage | What it does |
|---|---|
| `Checkout` | Pulls the latest source code from GitHub |
| `Docker Build` | Builds the Flask Docker image |
| `Deploy` | Stops old containers and starts the updated stack |
| `Verify Containers` | Shows running Compose services |
| `Health Check` | Calls `http://localhost:${APP_PORT}/health` |

Current pipeline:

```groovy
pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = 'two-tier-flask'
        APP_PORT = '80'
        DB_HOST = 'mysql'
        DB_USER = 'appuser'
        DB_PASSWORD = 'apppassword'
        DB_NAME = 'appdb'
        MYSQL_ROOT_PASSWORD = 'rootpassword'
        MYSQL_DATABASE = 'appdb'
        MYSQL_USER = 'appuser'
        MYSQL_PASSWORD = 'apppassword'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker compose build'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker compose down --remove-orphans'
                sh 'docker compose up -d'
            }
        }

        stage('Verify Containers') {
            steps {
                sh 'docker compose ps'
            }
        }

        stage('Health Check') {
            steps {
                sh 'sleep 10'
                sh "curl -f http://localhost:${APP_PORT}/health"
            }
        }
    }

    post {
        success {
            echo 'Deployment successful!'
        }

        failure {
            echo 'Deployment failed!'
        }
    }
}
```

Why `COMPOSE_PROJECT_NAME` matters:

Docker Compose normally derives the project name from the folder name. Jenkins workspaces can have names like `two-tier-flask-pipeline`, which creates different container names and networks. Setting `COMPOSE_PROJECT_NAME=two-tier-flask` makes every deployment target the same Compose project.

Why the health check matters:

The deployment is not considered successful just because containers started. Jenkins also checks `/health` to confirm Flask is responding.

## Jenkins Job Setup

In Jenkins:

```text
Dashboard
  -> New Item
  -> Pipeline
```

Use:

```text
Name: two-tier-flask-pipeline
Type: Pipeline
```

Pipeline configuration:

```text
Definition: Pipeline script from SCM
SCM: Git
Repository URL: git@github.com:<YOUR_GITHUB_USERNAME>/two-tier-flask.git
Branch Specifier: */main
Script Path: Jenkinsfile
```

Because this project uses `checkout scm`, Jenkins must know the Git repository from the job configuration.

If your repository is public and you use HTTPS, credentials may not be needed:

```text
https://github.com/<YOUR_GITHUB_USERNAME>/two-tier-flask.git
```

If your repository is private or you use SSH, configure Jenkins credentials.

## Jenkins SSH Access to GitHub

If using `git@github.com:<USER>/<REPO>.git`, create an SSH key for the `jenkins` user:

```bash
sudo -u jenkins mkdir -p /var/lib/jenkins/.ssh
sudo -u jenkins ssh-keygen -t ed25519 -C "jenkins@two-tier-flask" -f /var/lib/jenkins/.ssh/id_ed25519 -N ""
sudo cat /var/lib/jenkins/.ssh/id_ed25519.pub
```

Add the public key to GitHub:

```text
GitHub repository
  -> Settings
  -> Deploy keys
  -> Add deploy key
```

Use:

```text
Title: Jenkins EC2 key
Key: paste the public key
Allow write access: unchecked
```

Test SSH as Jenkins:

```bash
sudo -u jenkins ssh -T git@github.com
```

Accept the host key if prompted.

Important: never share or commit `/var/lib/jenkins/.ssh/id_ed25519`. That is the private key.

## GitHub Webhook Setup

The webhook makes GitHub notify Jenkins when code is pushed.

In GitHub:

```text
Repository
  -> Settings
  -> Webhooks
  -> Add webhook
```

Use:

```text
Payload URL: http://<EC2_PUBLIC_IP>:8080/github-webhook/
Content type: application/json
Events: Just the push event
Active: checked
```

In Jenkins job configuration, enable:

```text
GitHub hook trigger for GITScm polling
```

Test the webhook:

1. Push a commit to GitHub.
2. Open Jenkins.
3. Confirm the pipeline starts automatically.
4. Check GitHub webhook deliveries if it does not trigger.

## End-to-End Test

Make a small application change:

```bash
vim app.py
```

Example change:

```python
return "Two-Tier Flask Application v3 - Jenkins CI/CD Working!"
```

Commit and push:

```bash
git status
git add app.py
git commit -m "Test Jenkins auto deployment"
git push
```

Watch Jenkins:

```text
Jenkins
  -> two-tier-flask-pipeline
  -> Build History
  -> Console Output
```

Expected pipeline result:

```text
Checkout             SUCCESS
Docker Build         SUCCESS
Deploy               SUCCESS
Verify Containers    SUCCESS
Health Check         SUCCESS
Finished: SUCCESS
```

Verify the deployed app:

```bash
curl http://<EC2_PUBLIC_IP>/
curl http://<EC2_PUBLIC_IP>/health
curl http://<EC2_PUBLIC_IP>/db
```

## Common Commands

Docker Compose:

```bash
docker compose build
docker compose up -d
docker compose up -d --build
docker compose down
docker compose down -v
docker compose ps
docker compose logs
docker compose logs -f flask
docker compose logs -f mysql
docker compose config
```

Docker containers and images:

```bash
docker ps
docker ps -a
docker images
docker volume ls
docker network ls
docker system df
```

Jenkins service:

```bash
sudo systemctl status jenkins
sudo systemctl restart jenkins
sudo journalctl -u jenkins -n 100 --no-pager
```

Docker service:

```bash
sudo systemctl status docker
sudo systemctl restart docker
sudo journalctl -u docker -n 100 --no-pager
```

Network/ports:

```bash
sudo ss -ltnp
sudo ss -ltnp | grep ':80'
sudo ss -ltnp | grep ':8080'
```

Git:

```bash
git status
git branch
git remote -v
git log --oneline -5
git pull
git add .
git commit -m "Your message"
git push
```

## Troubleshooting

### Port 80 is already allocated

Error:

```text
Bind for 0.0.0.0:80 failed: port is already allocated
```

Find what is using port `80`:

```bash
sudo ss -ltnp | grep ':80'
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

If an old Compose stack is running:

```bash
COMPOSE_PROJECT_NAME=two-tier-flask docker compose down --remove-orphans
docker compose up -d
```

If Apache or Nginx is using port `80`, stop it if it is not needed:

```bash
sudo systemctl stop apache2
sudo systemctl disable apache2
```

or:

```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

Alternative: use another host port:

```bash
APP_PORT=5002 docker compose up -d --build
curl http://localhost:5002/health
```

### Jenkins cannot run Docker

Error examples:

```text
permission denied while trying to connect to the Docker daemon socket
docker: permission denied
```

Fix:

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
sudo -u jenkins docker ps
```

### Jenkins checkout fails

If using SSH, test as Jenkins:

```bash
sudo -u jenkins ssh -T git@github.com
```

Check repository URL:

```bash
git remote -v
```

For a Jenkins Pipeline from SCM job, confirm:

```text
Repository URL is correct
Branch is */main
Script Path is Jenkinsfile
Credentials are configured if repo is private
```

### Flask cannot connect to MySQL

Check both containers:

```bash
docker compose ps
```

Check MySQL logs:

```bash
docker compose logs mysql
```

Check Flask logs:

```bash
docker compose logs flask
```

Verify environment variables:

```bash
docker compose config
```

Remember:

```text
DB_HOST must be mysql
```

Do not use:

```text
localhost
```

Inside a container, `localhost` means the same container, not the MySQL container.

### MySQL user or password does not update

If you changed MySQL environment variables after the first run, remove the volume:

```bash
docker compose down -v
docker compose up -d --build
```

Warning: `docker compose down -v` deletes the MySQL data volume.

### Health check fails in Jenkins

Run manually on the EC2 server:

```bash
curl -v http://localhost/health
docker compose ps
docker compose logs flask
```

If the app needs more time to start, increase the sleep in the Jenkinsfile:

```groovy
sh 'sleep 20'
```

### Jenkins webhook does not trigger

Check:

```text
GitHub webhook URL is http://<EC2_PUBLIC_IP>:8080/github-webhook/
Jenkins security group allows your GitHub delivery to reach port 8080
Jenkins job has GitHub hook trigger for GITScm polling enabled
GitHub webhook delivery shows status 200
```

You can still run the pipeline manually:

```text
Jenkins -> Job -> Build Now
```

## Rollback Strategy

Simple learning-project rollback:

1. Find the last good commit:

   ```bash
   git log --oneline
   ```

2. Revert the bad commit:

   ```bash
   git revert <BAD_COMMIT_SHA>
   git push
   ```

3. Jenkins rebuilds and redeploys the previous working code.

Manual emergency rollback on EC2:

```bash
cd ~/two-tier-flask
git fetch origin
git checkout <GOOD_COMMIT_SHA>
docker compose up -d --build
curl http://localhost/health
```

After emergency rollback, return the Git branch to a clean state using a normal Git revert or a new fixing commit.

## Clean Up

Stop containers:

```bash
docker compose down
```

Stop containers and remove MySQL data:

```bash
docker compose down -v
```

Remove unused Docker data:

```bash
docker system prune
```

Remove unused Docker data including unused images:

```bash
docker system prune -a
```

Check Docker disk usage:

```bash
docker system df
```

## Project Roadmap

| Phase | Description | Status |
|---|---|---|
| 1 | AWS EC2 setup and security group | Complete |
| 2 | Ubuntu server preparation | Complete |
| 3 | Docker and Docker Compose installation | Complete |
| 4 | Flask app and Dockerfile | Complete |
| 5 | Docker Compose with MySQL | Complete |
| 6 | GitHub repository integration | Complete |
| 7 | Jenkins CI/CD pipeline | Complete |
| 8 | End-to-end deployment and basic hardening | Complete |

## Learning Outcomes

After completing this project, you should understand:

- How to provision and access a Linux EC2 server.
- How Docker images are built from a Dockerfile.
- How Docker Compose runs multiple services together.
- Why containers use service names like `mysql` instead of `localhost`.
- How volumes preserve database data.
- How Jenkins runs shell commands to build and deploy software.
- How GitHub webhooks trigger CI/CD pipelines.
- How to inspect logs, ports, containers, networks, and volumes.
- How to recover from common deployment failures.

## External References

- Docker Engine on Ubuntu: https://docs.docker.com/engine/install/ubuntu/
- Jenkins on Linux: https://www.jenkins.io/doc/book/installing/linux/
- GitHub webhooks: https://docs.github.com/en/webhooks/about-webhooks
- Creating GitHub webhooks: https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks
