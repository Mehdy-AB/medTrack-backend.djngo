# SonarQube Integration Guide

## Quick Start

### Prerequisites
- Docker Desktop running
- At least 4GB RAM allocated to Docker

### Start SonarQube

```bash
# Start SonarQube services
docker-compose --profile sonar up -d

# Wait ~2 minutes for startup, then open:
# http://localhost:9090
# Login: admin / admin
```

### Run Analysis

**Option 1: Using the script (Windows)**
```bash
run-sonar.bat
```

**Option 2: Manual commands**
```bash
# Run SonarQube Scanner (from project root)
docker run --rm --network=backend -v "%cd%:/usr/src" -w /usr/src ^
    sonarsource/sonar-scanner-cli ^
    -Dsonar.host.url=http://sonarqube:9000 ^
    -Dsonar.login=admin -Dsonar.password=admin
```

### View Results

1. Open http://localhost:9090
2. Login with `admin` / `admin`
3. Navigate to "Projects" > "medtrack-backend"

---

## Project Configuration

The `sonar-project.properties` file is configured to scan:

| Service | Source Path |
|---------|-------------|
| auth-service | `services/auth-service/src` |
| profile-service | `services/profile-service/src` |
| core-service | `services/core-service/src` |
| eval-service | `services/eval-service/src` |
| comm-service | `services/comm-service/src` |

### Exclusions
- Migration files (`**/migrations/**`)
- Cache files (`**/__pycache__/**`)
- Test files (analyzed separately)
- Static/media files

---

## Metrics Analyzed

- **Bugs**: Code defects that could lead to runtime errors
- **Vulnerabilities**: Security issues (SQL injection, XSS, etc.)
- **Code Smells**: Maintainability issues
- **Duplications**: Copy-paste code detection
- **Coverage**: Test coverage (if configured)

---

## Stop SonarQube

```bash
docker-compose --profile sonar down
```
