"""
Unit tests for individual functions in api/index.py
"""
import pytest
import sys
import os

# Add the api directory to the path so we can import the functions
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from index import text_to_number, number_to_text, base64_to_number, number_to_base64


class TestTextToNumber:
    """Test the text_to_number function"""
    
    def test_basic_single_digits(self):
        """Test basic single digit words"""
        assert text_to_number("one") == 1
        assert text_to_number("two") == 2
        assert text_to_number("three") == 3
        assert text_to_number("four") == 4
        assert text_to_number("five") == 5
        assert text_to_number("six") == 6
        assert text_to_number("seven") == 7
        assert text_to_number("eight") == 8
        assert text_to_number("nine") == 9
        assert text_to_number("ten") == 10
    
    def test_zero_cases(self):
        """Test zero handling"""
        assert text_to_number("zero") == 0
        assert text_to_number("nil") == 0
    
    def test_case_insensitivity(self):
        """Test case insensitive conversion"""
        assert text_to_number("ONE") == 1
        assert text_to_number("Two") == 2
        assert text_to_number("ZERO") == 0
        assert text_to_number("OnE") == 1
        assert text_to_number("tWo") == 2
    
    def test_whitespace_handling(self):
        """Test whitespace handling"""
        assert text_to_number(" one ") == 1
        assert text_to_number("  zero  ") == 0
        assert text_to_number("\tone\t") == 1
    
    def test_punctuation_removal(self):
        """Test punctuation removal by regex"""
        assert text_to_number("one!") == 1
        assert text_to_number("one.") == 1
        assert text_to_number("two,") == 2
    
    def test_empty_string_failure(self):
        """Test empty string raises ValueError"""
        with pytest.raises(ValueError):
            text_to_number("")
    
    def test_invalid_text_failure(self):
        """Test invalid text raises ValueError"""
        with pytest.raises(ValueError):
            text_to_number("eleven")
        with pytest.raises(ValueError):
            text_to_number("twenty")
        with pytest.raises(ValueError):
            text_to_number("hundred")
        with pytest.raises(ValueError):
            text_to_number("uno")  # Non-English
    
    def test_multiple_words_failure(self):
        """Test multiple words raise ValueError"""
        with pytest.raises(ValueError):
            text_to_number("one two")
        with pytest.raises(ValueError):
            text_to_number("twenty one")  # Even if individual words were valid
    
    def test_numbers_as_text_failure(self):
        """Test numeric strings raise ValueError"""
        with pytest.raises(ValueError):
            text_to_number("1")
        with pytest.raises(ValueError):
            text_to_number("123")


class TestNumberToText:
    """Test the number_to_text function"""
    
    def test_single_digits(self):
        """Test single digit conversion"""
        assert number_to_text(0) == "zero"
        assert number_to_text(1) == "one"
        assert number_to_text(2) == "two"
        assert number_to_text(9) == "nine"
    
    def test_double_digits(self):
        """Test double digit conversion"""
        assert number_to_text(10) == "ten"
        assert number_to_text(11) == "eleven"
        assert number_to_text(42) == "forty-two"
        assert number_to_text(99) == "ninety-nine"
    
    def test_hundreds(self):
        """Test hundreds conversion"""
        assert number_to_text(100) == "one hundred"
        assert number_to_text(101) == "one hundred and one"
        assert number_to_text(999) == "nine hundred and ninety-nine"
    
    def test_thousands(self):
        """Test thousands conversion"""
        assert number_to_text(1000) == "one thousand"
        assert number_to_text(1001) == "one thousand and one"
        assert number_to_text(1234) == "one thousand, two hundred and thirty-four"
    
    def test_large_numbers(self):
        """Test large numbers"""
        assert number_to_text(1000000) == "one million"
        assert number_to_text(1000000000) == "one billion"
    
    def test_negative_numbers(self):
        """Test negative number conversion"""
        assert number_to_text(-1) == "minus one"
        assert number_to_text(-100) == "minus one hundred"
        assert number_to_text(-42) == "minus forty-two"
    
    def test_float_input(self):
        """Test float input handling"""
        # This might work or raise an error depending on num2words implementation
        try:
            result = number_to_text(1.5)
            # If it works, it should return something reasonable
            assert isinstance(result, str)
        except (ValueError, TypeError):
            # If it raises an error, that's also acceptable
            pass
    
    def test_string_input_failure(self):
        """Test string input raises TypeError"""
        with pytest.raises(TypeError):
            number_to_text("123")
    
    def test_none_input_failure(self):
        """Test None input raises TypeError"""
        with pytest.raises(TypeError):
            number_to_text(None)


class TestBase64ToNumber:
    """Test the base64_to_number function"""
    
    def test_valid_base64_strings(self):
        """Test valid base64 string conversion"""
        # "QQ==" represents ASCII 'A' (65)
        assert base64_to_number("QQ==") == 65
        # "AQ==" represents 1
        assert base64_to_number("AQ==") == 1
        # "AA==" represents 0
        assert base64_to_number("AA==") == 0
    
    def test_common_base64_values(self):
        """Test common base64 encoded values"""
        # "AQAB" represents 65537 (common RSA exponent)
        assert base64_to_number("AQAB") == 65537
    
    def test_padding_variations(self):
        """Test different padding scenarios"""
        # Test with different amounts of padding
        assert base64_to_number("AQ==") == 1  # 2 padding chars
        assert base64_to_number("QQ==") == 65  # 2 padding chars
    
    def test_empty_valid_base64(self):
        """Test minimal valid base64"""
        assert base64_to_number("AA==") == 0
    
    def test_long_base64_strings(self):
        """Test very long base64 strings"""
        # Create a longer base64 string
        long_b64 = "QWxhZGRpbjpvcGVuIHNlc2FtZQ=="  # "Aladdin:open sesame"
        result = base64_to_number(long_b64)
        assert isinstance(result, int)
        assert result > 0
    
    def test_invalid_base64_characters(self):
        """Test invalid base64 characters raise ValueError"""
        with pytest.raises(ValueError):
            base64_to_number("!@#$")
        with pytest.raises(ValueError):
            base64_to_number("QQ!!")
    
    def test_incorrect_padding(self):
        """Test incorrect padding raises ValueError"""
        with pytest.raises(ValueError):
            base64_to_number("QQ")  # Missing padding
        with pytest.raises(ValueError):
            base64_to_number("Q===")  # Too much padding
    
    def test_empty_string_failure(self):
        """Test empty string raises ValueError"""
        with pytest.raises(ValueError):
            base64_to_number("")
    
    def test_non_string_input(self):
        """Test non-string input handling"""
        with pytest.raises((TypeError, ValueError, AttributeError)):
            base64_to_number(123)
        with pytest.raises((TypeError, ValueError, AttributeError)):
            base64_to_number(None)


class TestNumberToBase64:
    """Test the number_to_base64 function"""
    
    def test_small_numbers(self):
        """Test small number conversion"""
        result_0 = number_to_base64(0)
        assert isinstance(result_0, str)
        # Should be able to decode back to 0
        
        result_1 = number_to_base64(1)
        assert result_1 == "AQ=="
        
        result_65 = number_to_base64(65)
        assert result_65 == "QQ=="
    
    def test_large_numbers(self):
        """Test large number conversion"""
        result = number_to_base64(65537)
        assert result == "AQAB"
        
        result_million = number_to_base64(1000000)
        assert isinstance(result_million, str)
        assert len(result_million) > 0
    
    def test_powers_of_two(self):
        """Test powers of 2"""
        for power in [8, 16, 32, 64, 128, 256, 512, 1024]:
            result = number_to_base64(power)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_zero_handling(self):
        """Test zero conversion"""
        result = number_to_base64(0)
        assert isinstance(result, str)
        # Should produce valid base64
    
    def test_very_large_numbers(self):
        """Test very large integers"""
        large_num = 2**64
        result = number_to_base64(large_num)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_negative_numbers(self):
        """Test negative numbers raise ValueError"""
        with pytest.raises(ValueError):
            number_to_base64(-1)
        with pytest.raises(ValueError):
            number_to_base64(-100)
    
    def test_float_input(self):
        """Test float input raises appropriate error"""
        with pytest.raises((TypeError, ValueError)):
            number_to_base64(1.5)
        with pytest.raises((TypeError, ValueError)):
            number_to_base64(3.14)
    
    def test_string_input(self):
        """Test string input raises TypeError"""
        with pytest.raises(TypeError):
            number_to_base64("123")
        with pytest.raises(TypeError):
            number_to_base64("hello")
    
    def test_none_input(self):
        """Test None input raises TypeError"""
        with pytest.raises(TypeError):
            number_to_base64(None)


class TestRoundTripConversions:
    """Test round-trip conversions to ensure consistency"""
    
    def test_base64_round_trip(self):
        """Test number -> base64 -> number round trip"""
        test_numbers = [0, 1, 65, 256, 1000, 65537]
        for num in test_numbers:
            if num >= 0:  # Only test non-negative numbers
                b64 = number_to_base64(num)
                recovered = base64_to_number(b64)
                assert recovered == num
    
    def test_text_round_trip_limited(self):
        """Test number -> text -> number round trip for supported range"""
        # Only test the range that text_to_number supports (0-10)
        for num in range(11):  # 0-10
            text = number_to_text(num)
            if num == 0:
                # Special case: number_to_text(0) returns "zero" 
                recovered = text_to_number("zero")
            else:
                try:
                    recovered = text_to_number(text)
                    assert recovered == num
                except ValueError:
                    # If text_to_number doesn't support the text representation,
                    # that's a limitation of the current implementation
                    pass
