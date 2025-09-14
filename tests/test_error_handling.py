"""
Error handling and exception tests for api/index.py
"""
import pytest
import json
import sys
import os

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from index import app, text_to_number, number_to_text, base64_to_number, number_to_base64


@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHTTPErrorCases:
    """Test HTTP-level error cases"""
    
    def test_missing_json_body(self, client):
        """Test POST request without JSON body"""
        response = client.post('/convert')
        # Should return appropriate error status or handle gracefully
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.get_json()
            if data:  # If JSON response is returned
                assert 'error' in data
                assert data['error'] is not None
    
    def test_malformed_json(self, client):
        """Test POST request with malformed JSON"""
        malformed_json_cases = [
            '{"invalid": json}',
            '{invalid json}',
            '{"missing_quote: "value"}',
            '{"trailing_comma": "value",}',
            'not json at all'
        ]
        
        for malformed in malformed_json_cases:
            response = client.post('/convert', 
                                 data=malformed,
                                 content_type='application/json')
            # Should handle gracefully
            assert response.status_code in [200, 400, 500]
    
    def test_wrong_content_type(self, client):
        """Test POST request with wrong content type"""
        response = client.post('/convert',
                             data='{"input": "5", "inputType": "decimal", "outputType": "binary"}',
                             content_type='text/plain')
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 500]
    
    def test_missing_content_type(self, client):
        """Test POST request without content type"""
        response = client.post('/convert',
                             data='{"input": "5", "inputType": "decimal", "outputType": "binary"}')
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 500]
    
    def test_wrong_http_method(self, client):
        """Test wrong HTTP methods on /convert"""
        json_data = {'input': '5', 'inputType': 'decimal', 'outputType': 'binary'}
        
        # GET should return 405
        response = client.get('/convert')
        assert response.status_code == 405
        
        # PUT should return 405
        response = client.put('/convert', json=json_data)
        assert response.status_code == 405
        
        # DELETE should return 405
        response = client.delete('/convert')
        assert response.status_code == 405


class TestInputValidationErrors:
    """Test input validation error cases"""
    
    def test_missing_required_fields(self, client):
        """Test missing required fields in JSON"""
        # Missing 'input' field
        response = client.post('/convert', json={
            'inputType': 'decimal',
            'outputType': 'binary'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        assert data['result'] is None
        
        # Missing 'inputType' field
        response = client.post('/convert', json={
            'input': '5',
            'outputType': 'binary'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        assert data['result'] is None
        
        # Missing 'outputType' field
        response = client.post('/convert', json={
            'input': '5',
            'inputType': 'decimal'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        assert data['result'] is None
    
    def test_null_field_values(self, client):
        """Test null values in required fields"""
        null_cases = [
            {'input': None, 'inputType': 'decimal', 'outputType': 'binary'},
            {'input': '5', 'inputType': None, 'outputType': 'binary'},
            {'input': '5', 'inputType': 'decimal', 'outputType': None}
        ]
        
        for case in null_cases:
            response = client.post('/convert', json=case)
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            assert data['result'] is None
    
    def test_wrong_data_types(self, client):
        """Test wrong data types for fields"""
        wrong_type_cases = [
            {'input': 123, 'inputType': 'decimal', 'outputType': 'binary'},  # input as number
            {'input': ['5'], 'inputType': 'decimal', 'outputType': 'binary'},  # input as array
            {'input': '5', 'inputType': 123, 'outputType': 'binary'},  # inputType as number
            {'input': '5', 'inputType': 'decimal', 'outputType': ['binary']},  # outputType as array
        ]
        
        for case in wrong_type_cases:
            response = client.post('/convert', json=case)
            assert response.status_code == 200
            data = response.get_json()
            # Should handle gracefully with error
            assert 'error' in data and 'result' in data
    
    def test_invalid_input_types(self, client):
        """Test invalid inputType values"""
        invalid_input_types = [
            'invalid_type',
            'DECIMAL',  # Wrong case
            'base-64',  # Wrong format
            'txt',
            'bin',
            'oct',
            'hex',
            '',
            ' ',
            'decimal binary'  # Multiple types
        ]
        
        for invalid_type in invalid_input_types:
            response = client.post('/convert', json={
                'input': '5',
                'inputType': invalid_type,
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            assert data['result'] is None
    
    def test_invalid_output_types(self, client):
        """Test invalid outputType values"""
        invalid_output_types = [
            'invalid_type',
            'DECIMAL',  # Wrong case
            'base-64',  # Wrong format
            'txt',
            'bin',
            'oct',
            'hex',
            '',
            ' ',
            'decimal binary'  # Multiple types
        ]
        
        for invalid_type in invalid_output_types:
            response = client.post('/convert', json={
                'input': '5',
                'inputType': 'decimal',
                'outputType': invalid_type
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            assert data['result'] is None


class TestConversionSpecificErrors:
    """Test conversion-specific error cases"""
    
    def test_binary_input_errors(self, client):
        """Test invalid binary input cases"""
        invalid_binary_cases = [
            '102',     # Contains invalid digit 2
            '123',     # Contains invalid digits
            'abc',     # Contains letters
            '1.0',     # Contains decimal point
            '1 0 1',   # Contains spaces
            '10,11',   # Contains comma
            '1e5',     # Scientific notation
            '0b101',   # With prefix
        ]
        
        for invalid_binary in invalid_binary_cases:
            response = client.post('/convert', json={
                'input': invalid_binary,
                'inputType': 'binary',
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            assert data['result'] is None
    
    def test_octal_input_errors(self, client):
        """Test invalid octal input cases"""
        invalid_octal_cases = [
            '89',      # Contains invalid digits 8,9
            'abc',     # Contains letters
            '7.5',     # Contains decimal point
            '7 5',     # Contains spaces
            '0o77',    # With prefix
            '8',       # Invalid single digit
            '9',       # Invalid single digit
        ]
        
        for invalid_octal in invalid_octal_cases:
            response = client.post('/convert', json={
                'input': invalid_octal,
                'inputType': 'octal',
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            assert data['result'] is None
    
    def test_hexadecimal_input_errors(self, client):
        """Test invalid hexadecimal input cases"""
        invalid_hex_cases = [
            'xyz',     # Invalid hex characters
            'gg',      # Invalid hex character g
            'ff.aa',   # Contains decimal point
            'ff aa',   # Contains spaces
            'f,a',     # Contains comma
            'gh',      # Contains invalid characters
        ]
        
        for invalid_hex in invalid_hex_cases:
            response = client.post('/convert', json={
                'input': invalid_hex,
                'inputType': 'hexadecimal',
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            assert data['result'] is None
    
    def test_decimal_input_errors(self, client):
        """Test invalid decimal input cases"""
        invalid_decimal_cases = [
            'abc',         # Non-numeric
            '12.34.56',    # Multiple decimal points
            '123abc',      # Mixed letters and numbers
            '12 34',       # Spaces
            '12,345',      # Comma (might be valid in some locales)
            '12+34',       # Plus sign
            '12-34',       # Minus in middle
            '12/34',       # Division
            '12*34',       # Multiplication
        ]
        
        for invalid_decimal in invalid_decimal_cases:
            response = client.post('/convert', json={
                'input': invalid_decimal,
                'inputType': 'decimal',
                'outputType': 'binary'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            assert data['result'] is None
    
    def test_text_input_errors(self, client):
        """Test invalid text input cases"""
        invalid_text_cases = [
            'eleven',      # Not supported by current implementation
            'twenty',      # Not supported
            'hundred',     # Not supported
            'thousand',    # Not supported
            'million',     # Not supported
            'uno',         # Non-English
            'eins',        # German
            'uno dos',     # Multiple words
            'one two',     # Multiple supported words
            '1',           # Numeric string
            '123',         # Numeric string
            'first',       # Ordinal
            'second',      # Ordinal
            'dozen',       # Non-standard number word
            'score',       # Non-standard number word
        ]
        
        for invalid_text in invalid_text_cases:
            response = client.post('/convert', json={
                'input': invalid_text,
                'inputType': 'text',
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            assert data['result'] is None
    
    def test_base64_input_errors(self, client):
        """Test invalid base64 input cases"""
        invalid_base64_cases = [
            '!@#$',        # Invalid characters
            'QQ!!',        # Mixed valid/invalid characters
            'Q===',        # Too much padding
            'Q',           # Too short
            'QQ',          # Missing padding
            'QQQ',         # Wrong length
            'QQ= =',       # Space in padding
            'QQ\n==',      # Newline in middle
            'Q Q==',       # Space in middle
        ]
        
        for invalid_base64 in invalid_base64_cases:
            response = client.post('/convert', json={
                'input': invalid_base64,
                'inputType': 'base64',
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            assert data['result'] is None


class TestUnitFunctionErrors:
    """Test error handling in individual functions"""
    
    def test_text_to_number_errors(self):
        """Test text_to_number error cases"""
        error_cases = [
            '',            # Empty string
            'eleven',      # Unsupported number
            'one two',     # Multiple words
            '1',           # Numeric string
            'uno',         # Non-English
        ]
        
        for error_case in error_cases:
            with pytest.raises(ValueError):
                text_to_number(error_case)
    
    def test_number_to_text_errors(self):
        """Test number_to_text error cases"""
        error_cases = [
            '123',         # String input
            None,          # None input
            [],            # List input
            {},            # Dict input
        ]
        
        for error_case in error_cases:
            with pytest.raises((TypeError, ValueError)):
                number_to_text(error_case)
    
    def test_base64_to_number_errors(self):
        """Test base64_to_number error cases"""
        error_cases = [
            '',            # Empty string
            '!@#$',        # Invalid characters
            'QQ',          # Missing padding
            'Q===',        # Too much padding
            123,           # Non-string input
            None,          # None input
        ]
        
        for error_case in error_cases:
            with pytest.raises((ValueError, TypeError, AttributeError)):
                base64_to_number(error_case)
    
    def test_number_to_base64_errors(self):
        """Test number_to_base64 error cases"""
        error_cases = [
            -1,            # Negative number
            '123',         # String input
            1.5,           # Float input
            None,          # None input
            [],            # List input
        ]
        
        for error_case in error_cases:
            with pytest.raises((ValueError, TypeError)):
                number_to_base64(error_case)


class TestExtremeInputs:
    """Test extremely large or unusual inputs"""
    
    def test_extremely_long_strings(self, client):
        """Test very long input strings"""
        # Create extremely long strings
        long_decimal = '9' * 10000
        long_binary = '1' * 10000
        long_hex = 'f' * 10000
        long_text = 'one' * 1000
        
        test_cases = [
            (long_decimal, 'decimal'),
            (long_binary, 'binary'),
            (long_hex, 'hexadecimal'),
            (long_text, 'text'),
        ]
        
        for long_input, input_type in test_cases:
            response = client.post('/convert', json={
                'input': long_input,
                'inputType': input_type,
                'outputType': 'decimal'
            })
            
            # Should handle gracefully (either work or fail with error)
            assert response.status_code == 200
            data = response.get_json()
            assert 'error' in data and 'result' in data
    
    def test_negative_number_handling(self, client):
        """Test negative number inputs"""
        negative_cases = [
            ('-1', 'decimal'),
            ('-100', 'decimal'),
            ('-ff', 'hexadecimal'),  # Should fail
            ('-101', 'binary'),      # Should fail
        ]
        
        for neg_input, input_type in negative_cases:
            response = client.post('/convert', json={
                'input': neg_input,
                'inputType': input_type,
                'outputType': 'decimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            
            if input_type == 'decimal':
                # Negative decimals might be supported
                assert 'error' in data and 'result' in data
            else:
                # Negative non-decimals should fail
                assert data['error'] is not None
    
    def test_floating_point_inputs(self, client):
        """Test floating point number inputs"""
        float_cases = [
            ('1.5', 'decimal'),
            ('3.14159', 'decimal'),
            ('0.5', 'decimal'),
            ('-2.5', 'decimal'),
        ]
        
        for float_input, input_type in float_cases:
            response = client.post('/convert', json={
                'input': float_input,
                'inputType': input_type,
                'outputType': 'binary'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            # Current implementation likely doesn't support floats
            assert data['error'] is not None
            assert data['result'] is None


class TestConcurrencyErrors:
    """Test error handling under concurrent requests"""
    
    def test_multiple_error_requests(self, client):
        """Test multiple simultaneous error-causing requests"""
        # This is a basic test - real concurrency testing would need threading
        error_requests = [
            {'input': 'invalid', 'inputType': 'binary', 'outputType': 'decimal'},
            {'input': '89', 'inputType': 'octal', 'outputType': 'decimal'},
            {'input': 'xyz', 'inputType': 'hexadecimal', 'outputType': 'decimal'},
            {'input': 'eleven', 'inputType': 'text', 'outputType': 'decimal'},
            {'input': '!@#$', 'inputType': 'base64', 'outputType': 'decimal'},
        ]
        
        for error_request in error_requests:
            response = client.post('/convert', json=error_request)
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            assert data['result'] is None


class TestErrorMessageQuality:
    """Test that error messages are helpful and informative"""
    
    def test_error_messages_are_strings(self, client):
        """Test that error messages are non-empty strings"""
        error_cases = [
            {'input': 'invalid', 'inputType': 'binary', 'outputType': 'decimal'},
            {'input': '89', 'inputType': 'octal', 'outputType': 'decimal'},
            {'input': 'xyz', 'inputType': 'hexadecimal', 'outputType': 'decimal'},
        ]
        
        for error_case in error_cases:
            response = client.post('/convert', json=error_case)
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is not None
            assert isinstance(data['error'], str)
            assert len(data['error']) > 0
    
    def test_error_messages_not_stack_traces(self, client):
        """Test that error messages don't expose stack traces"""
        response = client.post('/convert', json={
            'input': 'invalid',
            'inputType': 'binary',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        error_msg = data['error'].lower()
        
        # Error messages shouldn't contain stack trace indicators
        stack_trace_indicators = ['traceback', 'file "', 'line ', 'exception', 'error at']
        for indicator in stack_trace_indicators:
            assert indicator not in error_msg

