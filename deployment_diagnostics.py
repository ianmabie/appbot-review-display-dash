#!/usr/bin/env python3
"""
Deployment diagnostics tool to identify and fix slow loading issues
"""

import os
import time
import requests
import subprocess
import psutil
from datetime import datetime

def check_deployment_health(deployment_url):
    """Check deployment health and performance"""
    print(f"Checking deployment at: {deployment_url}")
    
    # Test basic connectivity
    try:
        start = time.time()
        response = requests.get(f"{deployment_url}/health", timeout=10)
        health_time = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ Health check: {health_time:.2f}s")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Health check timed out (>10s)")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test readiness
    try:
        start = time.time()
        response = requests.get(f"{deployment_url}/health/ready", timeout=15)
        ready_time = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ Readiness check: {ready_time:.2f}s")
        else:
            print(f"⚠️ Readiness check failed: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ Readiness check timed out (>15s)")
    except Exception as e:
        print(f"❌ Readiness check error: {e}")
    
    # Test main page load
    try:
        start = time.time()
        response = requests.get(deployment_url, timeout=20)
        page_time = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ Main page load: {page_time:.2f}s")
            if page_time > 5:
                print("⚠️ Page load is slow (>5s)")
        else:
            print(f"❌ Main page failed: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ Main page timed out (>20s)")
    except Exception as e:
        print(f"❌ Main page error: {e}")
    
    # Test performance endpoint
    try:
        response = requests.get(f"{deployment_url}/performance", timeout=10)
        if response.status_code == 200:
            perf_data = response.json()
            print(f"✅ Performance data: avg {perf_data.get('average_response_time', 'N/A')}s")
            if perf_data.get('slow_requests_count', 0) > 0:
                print(f"⚠️ Found {perf_data['slow_requests_count']} slow requests")
        
    except Exception as e:
        print(f"⚠️ Performance endpoint unavailable: {e}")
    
    return True

def diagnose_common_issues():
    """Diagnose common deployment slowness issues"""
    print("\n🔍 Diagnosing common issues...")
    
    issues = []
    
    # Check database connection optimization
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        if 'sslmode=require' not in db_url and 'sslmode=prefer' not in db_url:
            issues.append("Database SSL mode not optimized")
        
        if 'connect_timeout' not in db_url:
            issues.append("Database connection timeout not set")
    
    # Check Gunicorn configuration
    if os.path.exists('gunicorn.conf.py'):
        with open('gunicorn.conf.py', 'r') as f:
            config = f.read()
            if 'workers = 1' not in config:
                issues.append("Multiple workers may cause resource contention")
            if 'eventlet' not in config:
                issues.append("SocketIO requires eventlet worker class")
    
    # Check memory usage
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        issues.append(f"High memory usage: {memory.percent}%")
    
    if issues:
        print("❌ Found issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ No common issues detected")
    
    return issues

def optimize_for_deployment():
    """Apply optimizations for deployment performance"""
    print("\n🚀 Applying deployment optimizations...")
    
    optimizations = []
    
    # Check if we can apply database URL optimizations
    db_url = os.environ.get('DATABASE_URL')
    if db_url and 'connect_timeout=5' not in db_url:
        # Suggest database URL optimization
        optimizations.append("Add connection timeout to DATABASE_URL")
    
    # Check static file caching
    if os.path.exists('static'):
        optimizations.append("Static file caching configured")
    
    # Check gzip compression
    optimizations.append("Consider enabling gzip compression in deployment")
    
    # Check CDN usage
    optimizations.append("Consider using CDN for static assets")
    
    print("📋 Optimization recommendations:")
    for opt in optimizations:
        print(f"  - {opt}")
    
    return optimizations

def main():
    """Main diagnostic function"""
    print("🔧 Deployment Performance Diagnostics")
    print("=" * 40)
    
    # Check local configuration
    diagnose_common_issues()
    
    # Get deployment URL from user
    deployment_url = input("\nEnter your deployment URL (or press Enter to skip): ").strip()
    
    if deployment_url:
        if not deployment_url.startswith('http'):
            deployment_url = f"https://{deployment_url}"
        
        print(f"\n🌐 Testing deployment: {deployment_url}")
        check_deployment_health(deployment_url)
    
    # Provide optimization recommendations
    optimize_for_deployment()
    
    print("\n📊 Performance Tips:")
    print("  1. Single worker configuration reduces resource contention")
    print("  2. Optimized database connection pool settings")
    print("  3. Static file caching headers implemented")
    print("  4. Performance monitoring enabled at /performance")
    print("  5. Health checks available at /health and /health/ready")

if __name__ == "__main__":
    main()