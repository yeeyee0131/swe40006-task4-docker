# SWE40006 — Task 4 Docker Deployment

Four containerised applications developed for Software Deployment and Evolution.

## Applications

| Folder | Application | Purpose |
|---|---|---|
| `python-app` | Python demonstration | Prints a greeting and container runtime information |
| `hello-web` | Nginx website | Serves a custom Hello World webpage |
| `study-planner` | Flask and SQLite web app | Creates study tasks, tracks completion, and retains data in a Docker volume |
| `study-analyzer` | Python command-line app | Validates study-session CSV files and exports subject totals as JSON |

## Deployed demonstrations

- Hello World: http://85.211.182.124/
- Study Planner: http://85.211.182.124:8081/

Availability depends on the Azure VM remaining running. The Study Planner is a shared demonstration; use sample tasks only.

## Prerequisites

Install Docker with Linux container support. Run the local commands below in Windows PowerShell from the downloaded repository folder.

## Python demonstration

```powershell
Set-Location .\python-app
docker build -t thongyee/task4-python:1.0 .
docker run --rm thongyee/task4-python:1.0
Set-Location ..
```

The application prints its Python version and operating system, then exits.

## Hello World website

```powershell
Set-Location .\hello-web
docker build -t thongyee/task4-hello-web:1.2 .
docker run -d --name task4-hello-web --restart unless-stopped -p 8080:80 thongyee/task4-hello-web:1.2
Set-Location ..
```

Open http://localhost:8080/.

Published image: `thongyee/task4-hello-web:1.2`.

## Study Planner

```powershell
Set-Location .\study-planner
docker build -t thongyee/task4-study-planner:1.0 .
docker run -d --name task4-study-planner --restart unless-stopped -p 8081:8000 -v task4-study-data:/app/data thongyee/task4-study-planner:1.0
docker ps --filter "name=task4-study-planner"
Set-Location ..
```

Open http://localhost:8081/.

Features include task creation, completion and reopening, priority labels, due dates, overdue counts, and completion progress. SQLite stores the tasks in the named volume. The `/health` endpoint checks database access, and Docker monitors it through a health check.

Published image: `thongyee/task4-study-planner:1.0`.

### Persistence check

Create a sample task and mark it complete, then run:

```powershell
docker restart task4-study-planner
```

Refresh the webpage. The task and its completion status should remain.

## Study Hours Analyzer

```powershell
Set-Location .\study-analyzer
docker build -t thongyee/task4-study-analyzer:1.0 .
docker run --name task4-study-analyzer --mount "type=bind,source=$($PWD.Path),target=/data" thongyee/task4-study-analyzer:1.0 --input /data/sessions.csv --output /data/summary.json
Get-Content .\summary.json
docker inspect --format '{{.State.Status}} | Exit code: {{.State.ExitCode}}' task4-study-analyzer
```

Expected sample results:

- 7 sessions across 3 subjects
- 13.50 total study hours
- SWE40006: 7.00 hours
- Database Systems: 3.50 hours
- Web Development: 3.00 hours
- Average session: 1.93 hours
- Successful container exit code: 0

The JSON report is saved in the host folder through the bind mount.

### Invalid-input test

```powershell
docker run --name task4-study-analyzer-invalid --mount "type=bind,source=$($PWD.Path),target=/data" thongyee/task4-study-analyzer:1.0 --input /data/invalid-sessions.csv --output /data/invalid-summary.json
docker inspect --format '{{.State.Status}} | Exit code: {{.State.ExitCode}}' task4-study-analyzer-invalid
Test-Path .\invalid-summary.json
```

The supplied negative-hours entry is intentionally invalid. Expected results are a line-specific validation message, exit code 1, and no output report created on a fresh run.

## Azure deployment

The deployment used an Ubuntu 24.04 Azure VM with Docker installed.

Run these commands inside the VM’s SSH session:

```bash
sudo docker pull thongyee/task4-hello-web:1.2
sudo docker run -d --name task4-hello-web --restart unless-stopped -p 80:80 thongyee/task4-hello-web:1.2

sudo docker pull thongyee/task4-study-planner:1.0
sudo docker run -d --name task4-study-planner --restart unless-stopped -p 8081:8000 -v task4-study-data:/app/data thongyee/task4-study-planner:1.0
```

Azure network security rules allow TCP ports 80 and 8081 for the web demonstrations. SSH access on TCP port 22 is restricted to the administrator’s public IP.

### Analyzer deployment using an image archive

Docker Hub analyzer pushes returned HTTP 500 errors from the token service. Deployment therefore proceeded using `docker save`, secure file transfer, and `docker load`. Successful registry publication of the analyzer has not been confirmed.

From local PowerShell in `study-analyzer`:

```powershell
docker save -o task4-study-analyzer-1.0.tar thongyee/task4-study-analyzer:1.0
```

Transfer the archive and `sessions.csv` to the VM using SCP with your own SSH key. Then run inside the Azure SSH session:

```bash
sudo docker load -i ~/task4-study-analyzer-1.0.tar
mkdir -p ~/study-analyzer
cp ~/sessions.csv ~/study-analyzer/sessions.csv
sudo docker run --name task4-study-analyzer --user "$(id -u):$(id -g)" --mount "type=bind,source=$HOME/study-analyzer,target=/data" thongyee/task4-study-analyzer:1.0 --input /data/sessions.csv --output /data/summary.json
cat ~/study-analyzer/summary.json
sudo docker inspect --format '{{.State.Status}} | Exit code: {{.State.ExitCode}}' task4-study-analyzer
```

The Azure run produced the same sample totals and exit code 0.

## Repeating the commands

Named containers must have unique names. If a demonstration container already exists, inspect it first, then remove that specific container or use a different name before repeating `docker run`.

Removing a container does not remove the Study Planner’s named volume. Preserve that volume when retaining tasks.

Dependency ranges and base-image tags may resolve to newer versions during future builds.

## Repository contents

This repository contains application source, Dockerfiles, and sample CSV inputs. SSH private keys, database files, and Docker image archives are excluded.
