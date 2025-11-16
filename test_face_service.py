#!/usr/bin/env python3
"""
Test script for face service.
"""
import requests
import json

def test_face_service():
    """Test the face service endpoints."""
    base_url = "http://localhost:8001"
    
    print("Testing Face Service...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"Root endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Root endpoint failed: {e}")
        return False
    
    # Test stats endpoint
    try:
        response = requests.get(f"{base_url}/face/stats", timeout=5)
        print(f"Stats: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Stats failed: {e}")
        return False
    
    print("Face service is working!")
    return True

if __name__ == "__main__":
    test_face_service()
