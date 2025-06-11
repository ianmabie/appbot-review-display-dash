#!/usr/bin/env python3
"""
Deployment verification script to check if all fixes are properly implemented.
Run this before deployment to ensure the application is ready.
"""

import os
import sys
import requests
import time
import subprocess
import signal
from datetime import datetime

def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def check_environment_variables():
    """Check if required environment variables are set"""
    log_message("Checking environment variables...")
    
    required_vars = ['DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        log_message(f"Missing environment variables: {missing_vars}", "ERROR")
        return False
    
    log_message("All required environment variables are set", "SUCCESS")
    return True

def check_file_structure():
    """Check if all required files exist"""
    log_message("Checking file structure...")
    
    required_files = [
        'main.py',
        'app.py', 
        'models.py',
        'wsgi.py',
        'gunicorn.conf.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        log_message(f"Missing files: {missing_files}", "ERROR")
        return False
    
    log_message("All required files are present", "SUCCESS")
    return True

def check_imports():
    """Check if imports work correctly"""
    log_message("Checking imports...")
    
    try:
        from main import app, socketio, database_ready
        log_message("Main imports successful", "SUCCESS")
        
        from wsgi import application
        log_message("WSGI imports successful", "SUCCESS")
        
        return True
    except Exception as e:
        log_message(f"Import error: {e}", "ERROR")
        return False

def check_health_endpoints():
    """Check if health endpoints are accessible"""
    log_message("Testing health endpoints...")
    
    # Start the application in background
    process = subprocess.Popen([sys.executable, 'wsgi.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
    
    # Wait for application to start
    time.sleep(5)
    
    try:
        # Test basic health check
        response = requests.get('http://localhost:5000/health', timeout=10)
        if response.status_code == 200:
            log_message("Basic health check: PASSED", "SUCCESS")
        else:
            log_message(f"Basic health check failed: {response.status_code}", "ERROR")
            return False
        
        # Test readiness check
        response = requests.get('http://localhost:5000/health/ready', timeout=10)
        if response.status_code == 200:
            log_message("Readiness check: PASSED", "SUCCESS")
        else:
            log_message(f"Readiness check failed: {response.status_code}", "ERROR")
            return False
        
        return True
        
    except Exception as e:
        log_message(f"Health check failed: {e}", "ERROR")
        return False
    finally:
        # Clean up process
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()

def check_gunicorn_compatibility():
    """Check if Gunicorn can start the application"""
    log_message("Testing Gunicorn compatibility...")
    
    try:
        # Test if Gunicorn can import the application
        result = subprocess.run([
            'python', '-c', 
            'from wsgi import application; print("Gunicorn import successful")'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            log_message("Gunicorn compatibility: PASSED", "SUCCESS")
            return True
        else:
            log_message(f"Gunicorn compatibility failed: {result.stderr}", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"Gunicorn test failed: {e}", "ERROR")
        return False

def main():
    """Run all deployment verification checks"""
    log_message("Starting deployment verification...")
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("File Structure", check_file_structure),
        ("Imports", check_imports),
        ("Health Endpoints", check_health_endpoints),
        ("Gunicorn Compatibility", check_gunicorn_compatibility)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        log_message(f"Running {name} check...")
        if check_func():
            passed += 1
        else:
            log_message(f"{name} check failed", "ERROR")
    
    log_message(f"Verification complete: {passed}/{total} checks passed")
    
    if passed == total:
        log_message("✅ Application is ready for deployment!", "SUCCESS")
        return True
    else:
        log_message("❌ Application has issues that need to be resolved", "ERROR")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)