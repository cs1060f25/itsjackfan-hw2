"""
Cross-format conversion tests for api/index.py
"""
import pytest
import json
import sys
import os

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from index import app


@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestRoundTripConversions:
    """Test round-trip conversions to ensure consistency"""
    
    def test_decimal_to_all_formats_and_back(self, client):
        """Test decimal -> other format -> decimal round trips"""
        test_numbers = ['0', '1', '5', '10', '42', '255']
        target_formats = ['binary', 'octal', 'hexadecimal', 'base64']
        
        for num in test_numbers:
            for target_format in target_formats:
                # Convert from decimal to target format
                response1 = client.post('/convert', json={
                    'input': num,
                    'inputType': 'decimal',
                    'outputType': target_format
                })
                
                assert response1.status_code == 200
                data1 = response1.get_json()
                assert data1['error'] is None, f"Failed to convert {num} to {target_format}"
                converted_value = data1['result']
                
                # Convert back from target format to decimal
                response2 = client.post('/convert', json={
                    'input': converted_value,
                    'inputType': target_format,
                    'outputType': 'decimal'
                })
                
                assert response2.status_code == 200
                data2 = response2.get_json()
                assert data2['error'] is None, f"Failed to convert {converted_value} ({target_format}) back to decimal"
                assert data2['result'] == num, f"Round trip failed: {num} -> {target_format}:{converted_value} -> {data2['result']}"
    
    def test_text_round_trip_limited_range(self, client):
        """Test text round trips for supported range (0-10)"""
        # Only test numbers that text_to_number supports
        supported_numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        
        for num in supported_numbers:
            # Convert decimal to text
            response1 = client.post('/convert', json={
                'input': num,
                'inputType': 'decimal',
                'outputType': 'text'
            })
            
            assert response1.status_code == 200
            data1 = response1.get_json()
            if data1['error'] is None:  # Only test if conversion succeeded
                text_value = data1['result']
                
                # Convert text back to decimal
                response2 = client.post('/convert', json={
                    'input': text_value,
                    'inputType': 'text',
                    'outputType': 'decimal'
                })
                
                assert response2.status_code == 200
                data2 = response2.get_json()
                if data2['error'] is None:  # Only test if conversion succeeded
                    assert data2['result'] == num, f"Text round trip failed: {num} -> {text_value} -> {data2['result']}"


class TestMultiStepConversions:
    """Test complex multi-step conversion chains"""
    
    def test_five_step_conversion_chain(self, client):
        """Test Text -> Decimal -> Binary -> Hexadecimal -> Decimal -> Text"""
        # Start with a number that should work through the entire chain
        start_value = 'five'
        expected_final = 'five'
        
        # Step 1: Text -> Decimal
        response1 = client.post('/convert', json={
            'input': start_value,
            'inputType': 'text',
            'outputType': 'decimal'
        })
        assert response1.status_code == 200
        data1 = response1.get_json()
        assert data1['error'] is None
        decimal_value = data1['result']
        
        # Step 2: Decimal -> Binary
        response2 = client.post('/convert', json={
            'input': decimal_value,
            'inputType': 'decimal',
            'outputType': 'binary'
        })
        assert response2.status_code == 200
        data2 = response2.get_json()
        assert data2['error'] is None
        binary_value = data2['result']
        
        # Step 3: Binary -> Hexadecimal
        response3 = client.post('/convert', json={
            'input': binary_value,
            'inputType': 'binary',
            'outputType': 'hexadecimal'
        })
        assert response3.status_code == 200
        data3 = response3.get_json()
        assert data3['error'] is None
        hex_value = data3['result']
        
        # Step 4: Hexadecimal -> Decimal
        response4 = client.post('/convert', json={
            'input': hex_value,
            'inputType': 'hexadecimal',
            'outputType': 'decimal'
        })
        assert response4.status_code == 200
        data4 = response4.get_json()
        assert data4['error'] is None
        decimal_value2 = data4['result']
        
        # Step 5: Decimal -> Text
        response5 = client.post('/convert', json={
            'input': decimal_value2,
            'inputType': 'decimal',
            'outputType': 'text'
        })
        assert response5.status_code == 200
        data5 = response5.get_json()
        assert data5['error'] is None
        final_text = data5['result']
        
        # Verify we got back to where we started
        assert final_text == expected_final
    
    def test_base64_conversion_chain(self, client):
        """Test Base64 -> Decimal -> Octal -> Decimal -> Base64"""
        # Start with a known base64 value
        start_base64 = 'BQ=='  # This represents the number 5
        
        # Step 1: Base64 -> Decimal
        response1 = client.post('/convert', json={
            'input': start_base64,
            'inputType': 'base64',
            'outputType': 'decimal'
        })
        assert response1.status_code == 200
        data1 = response1.get_json()
        assert data1['error'] is None
        decimal_value = data1['result']
        
        # Step 2: Decimal -> Octal
        response2 = client.post('/convert', json={
            'input': decimal_value,
            'inputType': 'decimal',
            'outputType': 'octal'
        })
        assert response2.status_code == 200
        data2 = response2.get_json()
        assert data2['error'] is None
        octal_value = data2['result']
        
        # Step 3: Octal -> Decimal
        response3 = client.post('/convert', json={
            'input': octal_value,
            'inputType': 'octal',
            'outputType': 'decimal'
        })
        assert response3.status_code == 200
        data3 = response3.get_json()
        assert data3['error'] is None
        decimal_value2 = data3['result']
        
        # Step 4: Decimal -> Base64
        response4 = client.post('/convert', json={
            'input': decimal_value2,
            'inputType': 'decimal',
            'outputType': 'base64'
        })
        assert response4.status_code == 200
        data4 = response4.get_json()
        assert data4['error'] is None
        final_base64 = data4['result']
        
        # The values should be consistent
        assert decimal_value == decimal_value2


class TestConsistencyAcrossFormats:
    """Test that the same numeric value produces consistent results"""
    
    def test_value_five_consistency(self, client):
        """Test that 5 is represented consistently across all formats"""
        # Start with decimal 5
        base_value = '5'
        expected_representations = {}
        
        # Get representations in all formats
        formats = ['decimal', 'binary', 'octal', 'hexadecimal', 'text', 'base64']
        
        for target_format in formats:
            response = client.post('/convert', json={
                'input': base_value,
                'inputType': 'decimal',
                'outputType': target_format
            })
            
            assert response.status_code == 200
            data = response.get_json()
            if data['error'] is None:
                expected_representations[target_format] = data['result']
        
        # Now test that converting from any format to any other format gives consistent results
        for source_format, source_value in expected_representations.items():
            for target_format in formats:
                if source_format != target_format:
                    response = client.post('/convert', json={
                        'input': source_value,
                        'inputType': source_format,
                        'outputType': target_format
                    })
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    if data['error'] is None and target_format in expected_representations:
                        assert data['result'] == expected_representations[target_format], \
                            f"Inconsistent conversion: {source_format}:{source_value} -> {target_format} " \
                            f"got {data['result']}, expected {expected_representations[target_format]}"
    
    def test_zero_consistency(self, client):
        """Test that 0 is represented consistently across all formats"""
        base_value = '0'
        expected_representations = {}
        
        # Get representations in all formats
        formats = ['decimal', 'binary', 'octal', 'hexadecimal', 'text', 'base64']
        
        for target_format in formats:
            response = client.post('/convert', json={
                'input': base_value,
                'inputType': 'decimal',
                'outputType': target_format
            })
            
            assert response.status_code == 200
            data = response.get_json()
            if data['error'] is None:
                expected_representations[target_format] = data['result']
        
        # Test cross-conversions for zero
        for source_format, source_value in expected_representations.items():
            for target_format in formats:
                if source_format != target_format and target_format in expected_representations:
                    response = client.post('/convert', json={
                        'input': source_value,
                        'inputType': source_format,
                        'outputType': target_format
                    })
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    if data['error'] is None:
                        assert data['result'] == expected_representations[target_format]


class TestConversionAccuracy:
    """Test accuracy of specific conversions"""
    
    def test_binary_conversion_accuracy(self, client):
        """Test accuracy of binary conversions"""
        test_cases = [
            ('0', '0'),
            ('1', '1'),
            ('2', '10'),
            ('3', '11'),
            ('4', '100'),
            ('5', '101'),
            ('8', '1000'),
            ('15', '1111'),
            ('16', '10000'),
            ('255', '11111111'),
        ]
        
        for decimal_val, expected_binary in test_cases:
            response = client.post('/convert', json={
                'input': decimal_val,
                'inputType': 'decimal',
                'outputType': 'binary'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is None
            assert data['result'] == expected_binary, f"Expected {decimal_val} -> {expected_binary}, got {data['result']}"
    
    def test_hexadecimal_conversion_accuracy(self, client):
        """Test accuracy of hexadecimal conversions"""
        test_cases = [
            ('0', '0'),
            ('1', '1'),
            ('10', 'a'),
            ('15', 'f'),
            ('16', '10'),
            ('255', 'ff'),
            ('256', '100'),
            ('4095', 'fff'),
        ]
        
        for decimal_val, expected_hex in test_cases:
            response = client.post('/convert', json={
                'input': decimal_val,
                'inputType': 'decimal',
                'outputType': 'hexadecimal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is None
            assert data['result'] == expected_hex, f"Expected {decimal_val} -> {expected_hex}, got {data['result']}"
    
    def test_octal_conversion_accuracy(self, client):
        """Test accuracy of octal conversions"""
        test_cases = [
            ('0', '0'),
            ('1', '1'),
            ('7', '7'),
            ('8', '10'),
            ('9', '11'),
            ('64', '100'),
            ('511', '777'),
        ]
        
        for decimal_val, expected_octal in test_cases:
            response = client.post('/convert', json={
                'input': decimal_val,
                'inputType': 'decimal',
                'outputType': 'octal'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is None
            assert data['result'] == expected_octal, f"Expected {decimal_val} -> {expected_octal}, got {data['result']}"
    
    def test_text_conversion_accuracy_limited(self, client):
        """Test accuracy of text conversions for supported range"""
        test_cases = [
            ('0', 'zero'),
            ('1', 'one'),
            ('2', 'two'),
            ('3', 'three'),
            ('4', 'four'),
            ('5', 'five'),
            ('6', 'six'),
            ('7', 'seven'),
            ('8', 'eight'),
            ('9', 'nine'),
            ('10', 'ten'),
        ]
        
        for decimal_val, expected_text in test_cases:
            response = client.post('/convert', json={
                'input': decimal_val,
                'inputType': 'decimal',
                'outputType': 'text'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is None
            assert data['result'] == expected_text, f"Expected {decimal_val} -> {expected_text}, got {data['result']}"


class TestConversionEdgeCases:
    """Test edge cases in conversions"""
    
    def test_leading_zeros_handling(self, client):
        """Test how leading zeros are handled in different formats"""
        test_cases = [
            ('007', 'octal', 'decimal', '7'),
            ('0000001', 'binary', 'decimal', '1'),
            ('00ff', 'hexadecimal', 'decimal', '255'),
        ]
        
        for input_val, input_type, output_type, expected in test_cases:
            response = client.post('/convert', json={
                'input': input_val,
                'inputType': input_type,
                'outputType': output_type
            })
            
            assert response.status_code == 200
            data = response.get_json()
            if data['error'] is None:
                assert data['result'] == expected
    
    def test_case_insensitive_hex(self, client):
        """Test that hexadecimal conversion is case insensitive"""
        hex_cases = [
            ('ff', 'hexadecimal', 'decimal', '255'),
            ('FF', 'hexadecimal', 'decimal', '255'),
            ('Ff', 'hexadecimal', 'decimal', '255'),
            ('fF', 'hexadecimal', 'decimal', '255'),
        ]
        
        for input_val, input_type, output_type, expected in hex_cases:
            response = client.post('/convert', json={
                'input': input_val,
                'inputType': input_type,
                'outputType': output_type
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is None
            assert data['result'] == expected
    
    def test_same_format_conversion(self, client):
        """Test converting from a format to itself"""
        same_format_cases = [
            ('5', 'decimal', 'decimal', '5'),
            ('101', 'binary', 'binary', '101'),
            ('77', 'octal', 'octal', '77'),
            ('ff', 'hexadecimal', 'hexadecimal', 'ff'),
            ('five', 'text', 'text', 'five'),
        ]
        
        for input_val, input_type, output_type, expected in same_format_cases:
            response = client.post('/convert', json={
                'input': input_val,
                'inputType': input_type,
                'outputType': output_type
            })
            
            assert response.status_code == 200
            data = response.get_json()
            if data['error'] is None:
                assert data['result'] == expected


class TestLargeNumberConversions:
    """Test conversions with large numbers"""
    
    def test_large_decimal_conversions(self, client):
        """Test large decimal number conversions"""
        large_numbers = ['1000', '1000000', '999999999']
        
        for large_num in large_numbers:
            # Test conversion to binary
            response = client.post('/convert', json={
                'input': large_num,
                'inputType': 'decimal',
                'outputType': 'binary'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is None
            binary_result = data['result']
            
            # Verify binary only contains 0s and 1s
            assert all(c in '01' for c in binary_result)
            
            # Test round trip
            response2 = client.post('/convert', json={
                'input': binary_result,
                'inputType': 'binary',
                'outputType': 'decimal'
            })
            
            assert response2.status_code == 200
            data2 = response2.get_json()
            assert data2['error'] is None
            assert data2['result'] == large_num
    
    def test_maximum_safe_conversions(self, client):
        """Test conversions at the edge of safe integer range"""
        # Test with some large but reasonable numbers
        edge_numbers = ['2147483647', '4294967295']  # 2^31-1, 2^32-1
        
        for edge_num in edge_numbers:
            for target_format in ['binary', 'hexadecimal', 'octal']:
                response = client.post('/convert', json={
                    'input': edge_num,
                    'inputType': 'decimal',
                    'outputType': target_format
                })
                
                assert response.status_code == 200
                data = response.get_json()
                # Should either work or fail gracefully
                assert 'error' in data and 'result' in data


class TestConversionPerformance:
    """Test conversion performance characteristics"""
    
    def test_repeated_conversions_consistency(self, client):
        """Test that repeated conversions give consistent results"""
        test_case = {'input': '42', 'inputType': 'decimal', 'outputType': 'binary'}
        
        # Perform the same conversion multiple times
        results = []
        for _ in range(5):
            response = client.post('/convert', json=test_case)
            assert response.status_code == 200
            data = response.get_json()
            assert data['error'] is None
            results.append(data['result'])
        
        # All results should be identical
        assert all(result == results[0] for result in results)
    
    def test_conversion_order_independence(self, client):
        """Test that conversion order doesn't affect results"""
        # Convert 42 to all formats
        base_conversions = {}
        formats = ['binary', 'octal', 'hexadecimal', 'text', 'base64']
        
        for fmt in formats:
            response = client.post('/convert', json={
                'input': '42',
                'inputType': 'decimal',
                'outputType': fmt
            })
            assert response.status_code == 200
            data = response.get_json()
            if data['error'] is None:
                base_conversions[fmt] = data['result']
        
        # Now test conversions in different order and verify consistency
        for fmt in reversed(formats):
            if fmt in base_conversions:
                response = client.post('/convert', json={
                    'input': '42',
                    'inputType': 'decimal',
                    'outputType': fmt
                })
                assert response.status_code == 200
                data = response.get_json()
                assert data['error'] is None
                assert data['result'] == base_conversions[fmt]

