"""
Integration tests for Flask routes in api/index.py
"""
import pytest
import json
import sys
import os

# Add the api directory to the path so we can import the Flask app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from index import app


@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestIndexRoute:
    """Test the GET / route"""
    
    def test_index_route_success(self, client):
        """Test GET / returns 200 and HTML content"""
        response = client.get('/')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')
        
        # Check that the response contains expected HTML elements
        html_content = response.get_data(as_text=True)
        assert 'Numeric Converter' in html_content
        assert '<form' in html_content or 'convert()' in html_content
        assert 'inputType' in html_content
        assert 'outputType' in html_content


class TestConvertRoute:
    """Test the POST /convert route"""
    
    def test_convert_route_method_not_allowed(self, client):
        """Test GET /convert returns 405 Method Not Allowed"""
        response = client.get('/convert')
        assert response.status_code == 405
    
    def test_missing_json_body(self, client):
        """Test POST /convert without JSON body"""
        response = client.post('/convert')
        # Should return 400 or handle gracefully with error
        assert response.status_code in [200, 400, 500]
    
    def test_malformed_json(self, client):
        """Test POST /convert with malformed JSON"""
        response = client.post('/convert', 
                             data='{"invalid": json}',
                             content_type='application/json')
        assert response.status_code in [200, 400, 500]
    
    def test_missing_required_fields(self, client):
        """Test POST /convert with missing required fields"""
        # Missing input field
        response = client.post('/convert',
                             json={'inputType': 'decimal', 'outputType': 'binary'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        
        # Missing inputType field
        response = client.post('/convert',
                             json={'input': '5', 'outputType': 'binary'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        
        # Missing outputType field
        response = client.post('/convert',
                             json={'input': '5', 'inputType': 'decimal'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None


class TestAllFormatConversions:
    """Test all 36 possible format combinations (6x6)"""
    
    # Test data for each format
    test_values = {
        'text': 'five',
        'binary': '101',
        'octal': '5',
        'decimal': '5',
        'hexadecimal': '5',
        'base64': 'BQ=='  # base64 for 5
    }
    
    expected_outputs = {
        'text': 'five',
        'binary': '101',
        'octal': '5',
        'decimal': '5',
        'hexadecimal': '5',
        'base64': 'BQ=='  # This might vary based on implementation
    }
    
    formats = ['text', 'binary', 'octal', 'decimal', 'hexadecimal', 'base64']
    
    @pytest.mark.parametrize("input_format", formats)
    @pytest.mark.parametrize("output_format", formats)
    def test_format_conversion(self, client, input_format, output_format):
        """Test conversion between all format pairs"""
        input_value = self.test_values[input_format]
        
        response = client.post('/convert', json={
            'input': input_value,
            'inputType': input_format,
            'outputType': output_format
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # The conversion should either succeed or fail gracefully
        assert 'result' in data
        assert 'error' in data
        
        # If no error, result should be a string
        if data['error'] is None:
            assert isinstance(data['result'], str)
            assert len(data['result']) > 0
        else:
            # If there's an error, result should be None
            assert data['result'] is None
            assert isinstance(data['error'], str)


class TestSpecificConversions:
    """Test specific conversion scenarios"""
    
    def test_decimal_to_binary(self, client):
        """Test decimal to binary conversion"""
        response = client.post('/convert', json={
            'input': '5',
            'inputType': 'decimal',
            'outputType': 'binary'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is None
        assert data['result'] == '101'
    
    def test_binary_to_decimal(self, client):
        """Test binary to decimal conversion"""
        response = client.post('/convert', json={
            'input': '101',
            'inputType': 'binary',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is None
        assert data['result'] == '5'
    
    def test_decimal_to_hexadecimal(self, client):
        """Test decimal to hexadecimal conversion"""
        response = client.post('/convert', json={
            'input': '255',
            'inputType': 'decimal',
            'outputType': 'hexadecimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is None
        assert data['result'] == 'ff'
    
    def test_text_to_decimal(self, client):
        """Test text to decimal conversion"""
        response = client.post('/convert', json={
            'input': 'five',
            'inputType': 'text',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is None
        assert data['result'] == '5'
    
    def test_decimal_to_text(self, client):
        """Test decimal to text conversion"""
        response = client.post('/convert', json={
            'input': '5',
            'inputType': 'decimal',
            'outputType': 'text'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is None
        assert data['result'] == 'five'
    
    def test_zero_conversion(self, client):
        """Test zero conversion across formats"""
        # Test decimal 0 to text
        response = client.post('/convert', json={
            'input': '0',
            'inputType': 'decimal',
            'outputType': 'text'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is None
        assert data['result'] == 'zero'
        
        # Test text zero to decimal
        response = client.post('/convert', json={
            'input': 'zero',
            'inputType': 'text',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is None
        assert data['result'] == '0'


class TestLargeNumbers:
    """Test conversion of large numbers"""
    
    def test_large_decimal_conversion(self, client):
        """Test large decimal number conversion"""
        response = client.post('/convert', json={
            'input': '1000000',
            'inputType': 'decimal',
            'outputType': 'text'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is None
        assert 'million' in data['result'].lower()
    
    def test_large_binary_conversion(self, client):
        """Test large binary number conversion"""
        response = client.post('/convert', json={
            'input': '11111111',  # 255 in binary
            'inputType': 'binary',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is None
        assert data['result'] == '255'


class TestErrorHandling:
    """Test error handling in conversions"""
    
    def test_invalid_binary_input(self, client):
        """Test invalid binary input"""
        response = client.post('/convert', json={
            'input': '102',  # Invalid binary (contains 2)
            'inputType': 'binary',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        assert data['result'] is None
    
    def test_invalid_octal_input(self, client):
        """Test invalid octal input"""
        response = client.post('/convert', json={
            'input': '89',  # Invalid octal (contains 8,9)
            'inputType': 'octal',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        assert data['result'] is None
    
    def test_invalid_hex_input(self, client):
        """Test invalid hexadecimal input"""
        response = client.post('/convert', json={
            'input': 'xyz',  # Invalid hex characters
            'inputType': 'hexadecimal',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        assert data['result'] is None
    
    def test_invalid_text_input(self, client):
        """Test invalid text input"""
        response = client.post('/convert', json={
            'input': 'eleven',  # Not supported by current implementation
            'inputType': 'text',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        assert data['result'] is None
    
    def test_invalid_base64_input(self, client):
        """Test invalid base64 input"""
        response = client.post('/convert', json={
            'input': '!@#$',  # Invalid base64 characters
            'inputType': 'base64',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        assert data['result'] is None
    
    def test_invalid_input_type(self, client):
        """Test invalid input type"""
        response = client.post('/convert', json={
            'input': '5',
            'inputType': 'invalid_type',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        assert data['result'] is None
    
    def test_invalid_output_type(self, client):
        """Test invalid output type"""
        response = client.post('/convert', json={
            'input': '5',
            'inputType': 'decimal',
            'outputType': 'invalid_type'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        assert data['result'] is None
    
    def test_empty_input(self, client):
        """Test empty input"""
        response = client.post('/convert', json={
            'input': '',
            'inputType': 'decimal',
            'outputType': 'binary'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error'] is not None
        assert data['result'] is None


class TestResponseFormat:
    """Test response format consistency"""
    
    def test_success_response_format(self, client):
        """Test successful response format"""
        response = client.post('/convert', json={
            'input': '5',
            'inputType': 'decimal',
            'outputType': 'binary'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Check response structure
        assert 'result' in data
        assert 'error' in data
        assert data['error'] is None
        assert isinstance(data['result'], str)
    
    def test_error_response_format(self, client):
        """Test error response format"""
        response = client.post('/convert', json={
            'input': 'invalid',
            'inputType': 'binary',
            'outputType': 'decimal'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Check response structure
        assert 'result' in data
        assert 'error' in data
        assert data['result'] is None
        assert isinstance(data['error'], str)
        assert len(data['error']) > 0
    
    def test_content_type(self, client):
        """Test response content type"""
        response = client.post('/convert', json={
            'input': '5',
            'inputType': 'decimal',
            'outputType': 'binary'
        })
        
        assert response.status_code == 200
        assert response.content_type.startswith('application/json')

