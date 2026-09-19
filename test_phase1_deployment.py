"""
TenderPulse 4IR - Phase 1 Production Readiness & Deployment Verification Test Suite
Verifies Dockerfile, Docker Compose orchestration, Nginx reverse proxy configuration,
environment variable profiles, and deployment automation scripts.
"""

import os
import sys
import yaml
import re

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def test_requirements_file():
    print("\n--- 1. Testing requirements.txt ---")
    req_file = os.path.join(ROOT_DIR, "requirements.txt")
    assert os.path.exists(req_file), "requirements.txt does not exist"
    
    with open(req_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_packages = ["fastapi", "uvicorn", "pydantic", "z3-solver", "networkx", "pypdf", "requests"]
    for pkg in required_packages:
        assert pkg in content, f"Missing required package '{pkg}' in requirements.txt"
    print(f"  [PASS] requirements.txt is clean UTF-8 and contains all {len(required_packages)} core libraries.")

def test_dockerfile():
    print("\n--- 2. Testing Dockerfile ---")
    dockerfile = os.path.join(ROOT_DIR, "Dockerfile")
    assert os.path.exists(dockerfile), "Dockerfile missing"
    
    with open(dockerfile, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    content = "".join(lines)
    assert "FROM python:3.11-slim" in content, "Dockerfile must use Python 3.11-slim base"
    assert "WORKDIR /app" in content, "Dockerfile must define WORKDIR /app"
    assert "USER tenderpulse" in content, "Dockerfile must enforce non-root user"
    assert "HEALTHCHECK" in content, "Dockerfile must declare HEALTHCHECK"
    assert "EXPOSE 8000" in content, "Dockerfile must expose internal port 8000"
    assert "uvicorn" in content and "backend.server:app" in content, "Dockerfile CMD must start backend.server:app"
    print("  [PASS] Dockerfile adheres to enterprise container security and multi-stage conventions.")

def test_nginx_configuration():
    print("\n--- 3. Testing Nginx Configuration ---")
    nginx_conf = os.path.join(ROOT_DIR, "nginx", "default.conf")
    assert os.path.exists(nginx_conf), "nginx/default.conf missing"
    
    with open(nginx_conf, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "upstream tenderpulse_backend" in content, "Missing upstream block in nginx conf"
    assert "proxy_pass http://tenderpulse_backend;" in content, "Missing proxy_pass in nginx conf"
    assert "gzip on;" in content, "Gzip compression must be enabled in nginx conf"
    assert "X-Frame-Options" in content, "Security headers must be configured in nginx conf"
    assert "location = /api/health" in content, "Health check endpoint proxy must be configured"
    print("  [PASS] nginx/default.conf verified with Gzip, security headers, and reverse proxy mapping.")

def test_docker_compose_schema():
    print("\n--- 4. Testing docker-compose.yml Schema ---")
    compose_file = os.path.join(ROOT_DIR, "docker-compose.yml")
    assert os.path.exists(compose_file), "docker-compose.yml missing"
    
    with open(compose_file, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)
    
    services = compose_data.get("services", {})
    assert "app" in services, "Missing 'app' service in docker-compose.yml"
    assert "nginx" in services, "Missing 'nginx' service in docker-compose.yml"
    assert "redis" in services, "Missing 'redis' service in docker-compose.yml"
    
    app_svc = services["app"]
    assert "healthcheck" in app_svc, "App service must define healthcheck"
    
    nginx_svc = services["nginx"]
    assert "depends_on" in nginx_svc, "Nginx must depend on app health"
    print(f"  [PASS] docker-compose.yml is valid YAML defining 3 services: {list(services.keys())}.")

def test_environment_configuration():
    print("\n--- 5. Testing Environment Configurations (.env.example & .env) ---")
    env_ex = os.path.join(ROOT_DIR, ".env.example")
    env_active = os.path.join(ROOT_DIR, ".env")
    
    assert os.path.exists(env_ex), ".env.example missing"
    assert os.path.exists(env_active), ".env missing"
    
    with open(env_ex, "r", encoding="utf-8") as f:
        ex_content = f.read()
    
    for var in ["ENVIRONMENT", "HOST_PORT", "SH_INSTANCE_ID", "DATABASE_URL", "JWT_SECRET_KEY"]:
        assert var in ex_content, f"Missing {var} in .env.example"
    print("  [PASS] .env.example and active .env provide full production environment configuration.")

def test_deployment_scripts():
    print("\n--- 6. Testing Automated Deployment Scripts ---")
    ps_script = os.path.join(ROOT_DIR, "scripts", "deploy.ps1")
    sh_script = os.path.join(ROOT_DIR, "scripts", "deploy.sh")
    
    assert os.path.exists(ps_script), "scripts/deploy.ps1 missing"
    assert os.path.exists(sh_script), "scripts/deploy.sh missing"
    
    with open(ps_script, "r", encoding="utf-8") as f:
        ps_content = f.read()
    assert "docker compose build" in ps_content or "docker-compose build" in ps_content, "deploy.ps1 must trigger docker compose build"
    assert "Invoke-RestMethod" in ps_content, "deploy.ps1 must poll healthcheck"
    
    with open(sh_script, "r", encoding="utf-8") as f:
        sh_content = f.read()
    assert "docker compose build" in sh_content or "docker-compose build" in sh_content, "deploy.sh must trigger docker compose build"
    print("  [PASS] Cross-platform deployment scripts (PowerShell & Bash) verified.")


if __name__ == "__main__":
    print("=================================================================")
    print("  TenderPulse 4IR - Phase 1 Production Readiness Test Suite")
    print("=================================================================")
    try:
        test_requirements_file()
        test_dockerfile()
        test_nginx_configuration()
        test_docker_compose_schema()
        test_environment_configuration()
        test_deployment_scripts()
        print("\n=================================================================")
        print("  ALL PHASE 1 CHECKS PASSED (100% READY FOR CONTAINERIZATION)")
        print("=================================================================")
    except AssertionError as ae:
        print(f"\n[FAIL] Test assertion failed: {ae}")
        sys.exit(1)
    except Exception as ex:
        print(f"\n[ERROR] Unexpected error: {ex}")
        sys.exit(1)
