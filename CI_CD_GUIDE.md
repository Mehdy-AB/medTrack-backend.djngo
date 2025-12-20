# CI/CD Pipeline Guide

## Overview

This project uses GitHub Actions for continuous integration and continuous deployment (CI/CD).

## Pipeline Stages

```
┌─────────┐    ┌───────────────────────┐    ┌────────────┐    ┌─────────┐
│  Lint   │ -> │   Unit Tests (5x)     │ -> │ SonarQube  │ -> │  Build  │
└─────────┘    └───────────────────────┘    └────────────┘    └─────────┘
```

### 1. Lint & Code Quality
- Black (code formatting)
- isort (import sorting)
- Flake8 (linting)

### 2. Unit Tests
Runs in parallel for each service:
- auth-service (21 tests)
- profile-service (23 tests)
- core-service (29 tests)
- eval-service (33 tests)
- comm-service (26 tests)

### 3. SonarQube Analysis
- Code quality metrics
- Bug detection
- Vulnerability scanning
- Code smell detection

### 4. Docker Build (main branch only)
- Builds all 5 service images
- Pushes to Docker Hub

---

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `SONAR_TOKEN` | SonarQube/SonarCloud authentication token |
| `SONAR_HOST_URL` | SonarQube server URL (e.g., `https://sonarcloud.io`) |
| `DOCKER_USERNAME` | Docker Hub username |
| `DOCKER_PASSWORD` | Docker Hub password |

### Setting Up Secrets

1. Go to GitHub repo → Settings → Secrets → Actions
2. Click "New repository secret"
3. Add each secret listed above

---

## SonarCloud Setup (Free for Open Source)

1. Go to [sonarcloud.io](https://sonarcloud.io)
2. Sign in with GitHub
3. Create a new project for your repository
4. Copy the token and add as `SONAR_TOKEN` secret
5. Set `SONAR_HOST_URL` to `https://sonarcloud.io`

---

## Local Testing

```bash
# Run linting
pip install flake8 black isort
black --check services/
isort --check-only services/
flake8 services/ --max-line-length=120 --exclude=migrations

# Run tests (requires Docker)
docker-compose up -d postgres
docker exec auth-service python manage.py test users

# Run SonarQube locally
docker-compose --profile sonar up -d
# Visit http://localhost:9090
```

---

## Workflow Triggers

| Event | Branch | Actions |
|-------|--------|---------|
| Push | main, develop | Full pipeline |
| Pull Request | main, develop | Full pipeline (no Docker push) |

---

## Badges

Add to your README.md:
```md
![CI/CD](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci-cd.yml/badge.svg)
![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=YOUR_PROJECT_KEY&metric=alert_status)
```
