"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
import os

# Add the api directory to the path so all test files can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

# Common test fixtures can be defined here
@pytest.fixture(scope="session")
def app():
    """Create application for testing"""
    from index import app
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

