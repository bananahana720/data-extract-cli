---
name: infrastructure-orchestration
description: Use when - (1) Starting/stopping services, (2) Docker operations, (3) Deployment tasks, (4) Service dependencies exist, (5) Multiple services need coordination. Ensures proper service management using orchestration scripts instead of individual commands. Prevents service management errors and ensures proper startup/shutdown sequences.
---

# Infrastructure Orchestration Protocol

This skill ensures services are managed through proper orchestration scripts, preventing dependency issues and maintaining correct startup/shutdown sequences.

## Core Principle

**NEVER start/stop individual services when orchestration exists**

- MUST search for orchestration scripts: start.sh, launch.sh, stop.sh, docker-compose.yml
- MUST use orchestration for ALL service operations
- MUST follow sequence: Stop ALL → Change → Start ALL → Verify
- MUST test complete lifecycle

## Orchestration Discovery

### Step 1: Find Orchestration Scripts

```bash
# Search for orchestration files
fd -t f "(start|launch|stop|restart|run|up|down)\.(sh|bash|py)"
fd "docker-compose.*\.ya?ml"
fd "Makefile"
fd "(package|composer|Gemfile|requirements)"

# Check common locations
ls scripts/ | rg "(start|stop|launch)"
ls bin/ | rg "(start|stop|launch)"
ls . | rg "docker-compose"

# Check for process managers
rg "supervisor|systemd|pm2|forever" --type yaml --type json
```

### Step 2: Understand Dependencies

```python
def analyze_service_dependencies():
    """Map out service dependency graph."""

    dependencies = {}

    # Parse docker-compose.yml
    if Path("docker-compose.yml").exists():
        with open("docker-compose.yml") as f:
            compose = yaml.load(f)
            for service, config in compose.get('services', {}).items():
                dependencies[service] = config.get('depends_on', [])

    # Parse start scripts
    start_scripts = find_files("start*.sh")
    for script in start_scripts:
        deps = extract_service_order(script)
        dependencies.update(deps)

    return create_dependency_graph(dependencies)
```

## Service Management Patterns

### Docker Compose Orchestration

```bash
# ❌ WRONG - Starting individual containers
docker run -d postgres
docker run -d redis
docker run -d app

# ✅ CORRECT - Using orchestration
docker-compose up -d

# Full lifecycle management
docker-compose down  # Stop all
# Make changes
docker-compose up -d  # Start all
docker-compose ps  # Verify
```

### Script-Based Orchestration

```bash
# ❌ WRONG - Manual service starts
systemctl start postgresql
systemctl start redis
systemctl start nginx
npm start

# ✅ CORRECT - Using orchestration script
./scripts/start-all.sh

# Typical orchestration script structure
#!/bin/bash
# start-all.sh
echo "Starting infrastructure..."

# Start in dependency order
systemctl start postgresql
wait_for_service postgresql 5432

systemctl start redis
wait_for_service redis 6379

systemctl start elasticsearch
wait_for_service elasticsearch 9200

# Start application
npm start &
wait_for_service app 3000

echo "All services started successfully"
```

### Kubernetes Orchestration

```bash
# ❌ WRONG - Individual deployments
kubectl apply -f postgres-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f app-deployment.yaml

# ✅ CORRECT - Using orchestration
kubectl apply -f k8s/  # Apply all manifests
# OR
helm install myapp ./chart

# Proper lifecycle
kubectl delete -f k8s/  # Stop all
# Make changes
kubectl apply -f k8s/  # Start all
kubectl get pods  # Verify
```

## Service Lifecycle Management

### Complete Shutdown Sequence

```python
def shutdown_services_safely():
    """Shutdown services in reverse dependency order."""

    # Get dependency graph
    deps = get_service_dependencies()
    shutdown_order = topological_sort_reverse(deps)

    for service in shutdown_order:
        print(f"Stopping {service}...")

        # Graceful shutdown
        send_sigterm(service)
        if not wait_for_shutdown(service, timeout=30):
            print(f"Force stopping {service}")
            send_sigkill(service)

        # Verify stopped
        assert not is_running(service), f"{service} still running!"

    print("All services stopped")
```

### Complete Startup Sequence

```python
def start_services_safely():
    """Start services in dependency order with health checks."""

    # Get dependency graph
    deps = get_service_dependencies()
    startup_order = topological_sort(deps)

    started = []

    for service in startup_order:
        print(f"Starting {service}...")

        try:
            start_service(service)
            wait_for_healthy(service)
            started.append(service)
            print(f"✅ {service} is healthy")

        except Exception as e:
            print(f"❌ Failed to start {service}: {e}")
            # Rollback
            for s in reversed(started):
                stop_service(s)
            raise

    print("All services started successfully")
```

## Health Check Patterns

```python
def wait_for_healthy(service, timeout=60):
    """Wait for service to become healthy."""

    health_checks = {
        'postgres': lambda: check_postgres_connection(),
        'redis': lambda: check_redis_ping(),
        'elasticsearch': lambda: check_elastic_cluster(),
        'app': lambda: check_http_endpoint('/health'),
        'rabbitmq': lambda: check_amqp_connection(),
        'mongodb': lambda: check_mongo_connection()
    }

    check = health_checks.get(service)
    if not check:
        # Generic TCP check
        return wait_for_port(get_service_port(service))

    start = time.time()
    while time.time() - start < timeout:
        try:
            if check():
                return True
        except:
            pass
        time.sleep(1)

    raise TimeoutError(f"{service} not healthy after {timeout}s")
```

## Configuration Management

### Environment-Specific Orchestration

```bash
# Development
./scripts/dev/start.sh

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up

# Production
kubectl apply -k overlays/production/
```

### Secret Management

```python
def load_secrets_before_start():
    """Load secrets from vault before starting services."""

    # ❌ WRONG - Hardcoded secrets
    os.environ['DB_PASSWORD'] = 'hardcoded_password'

    # ✅ CORRECT - Load from secret manager
    secrets = load_from_vault([
        'db/password',
        'redis/password',
        'api/keys/external'
    ])

    for key, value in secrets.items():
        os.environ[key] = value

    # Now safe to start services
    run_orchestration_script()
```

## Common Orchestration Files

### docker-compose.yml
```yaml
version: '3.8'
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  app:
    build: .
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: ./start.sh
```

### Makefile
```makefile
.PHONY: start stop restart status

start:
	@echo "Starting all services..."
	@docker-compose up -d
	@./scripts/wait-for-healthy.sh
	@echo "All services ready"

stop:
	@echo "Stopping all services..."
	@docker-compose down
	@echo "All services stopped"

restart: stop start

status:
	@docker-compose ps
	@./scripts/health-check.sh
```

## Integration with BMAD

When working with BMAD workflows:
- Check workflow-manifest.csv for orchestration workflows
- Use task-manifest.csv for service task sequences
- Maintain consistency with existing orchestration patterns

## Scripts

### Orchestration Finder
See [scripts/find_orchestration.py](scripts/find_orchestration.py) - Discovers orchestration scripts

### Dependency Analyzer
See [scripts/analyze_dependencies.py](scripts/analyze_dependencies.py) - Maps service dependencies

## Critical Reminders

- **Never Skip Orchestration**: Individual commands break dependencies
- **Test Full Lifecycle**: Always test stop → start → verify
- **Health Checks Required**: Don't assume services are ready immediately
- **Rollback on Failure**: If any service fails, stop all and investigate
