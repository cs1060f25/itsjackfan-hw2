# Comprehensive Test Plan for index.py

This document outlines a complete test suite for the numeric converter Flask application (`api/index.py`). The application converts between different number formats: English text, binary, octal, decimal, hexadecimal, and base64.

## Test Categories Overview

1. **Unit Tests for Individual Functions**
2. **Integration Tests for Flask Routes**
3. **Edge Cases and Boundary Conditions**
4. **Error Handling and Exception Cases**
5. **Input Validation Tests**
6. **Cross-Format Conversion Tests**

---

## 1. Unit Tests for Individual Functions

### 1.1 `text_to_number()` Function Tests

#### Success Cases:
- **Basic single digit words**: `"one"` → `1`, `"two"` → `2`, etc. (1-10)
- **Zero cases**: `"zero"` → `0`, `"nil"` → `0`
- **Case insensitivity**: `"ONE"` → `1`, `"Two"` → `2`, `"ZERO"` → `0`
- **Mixed case**: `"OnE"` → `1`, `"tWo"` → `2`

#### Edge Cases:
- **Whitespace handling**: `" one "` → `1`, `"  zero  "` → `0`
- **Hyphenated words**: `"twenty-one"` (currently not supported, should raise ValueError)
- **Empty string**: `""` → should raise ValueError
- **Multiple words**: `"one two"` → should raise ValueError

#### Failure Cases:
- **Invalid text**: `"eleven"` → ValueError (not in dictionary)
- **Non-English words**: `"uno"` → ValueError
- **Numbers as text**: `"1"` → ValueError
- **Special characters**: `"one!"` → should be handled (stripped by regex)
- **Punctuation**: `"one."` → should be handled (stripped by regex)

### 1.2 `number_to_text()` Function Tests

#### Success Cases:
- **Single digits**: `0` → `"zero"`, `1` → `"one"`, `9` → `"nine"`
- **Double digits**: `10` → `"ten"`, `42` → `"forty-two"`
- **Hundreds**: `100` → `"one hundred"`, `999` → `"nine hundred and ninety-nine"`
- **Thousands**: `1000` → `"one thousand"`, `1234` → `"one thousand, two hundred and thirty-four"`
- **Large numbers**: `1000000` → `"one million"`

#### Edge Cases:
- **Zero**: `0` → `"zero"`
- **Negative numbers**: `-1` → `"minus one"`, `-100` → `"minus one hundred"`
- **Very large numbers**: Test with numbers in billions/trillions range

#### Failure Cases:
- **Non-integer types**: `1.5` → should handle or raise appropriate error
- **String input**: `"123"` → should raise TypeError
- **None input**: `None` → should raise TypeError

### 1.3 `base64_to_number()` Function Tests

#### Success Cases:
- **Valid base64 strings**: 
  - `"QQ=="` (represents 'A' in ASCII, value 65)
  - `"AQAB"` (common RSA exponent, value 65537)
  - `"AQ=="` (value 1)
  - `"AA=="` (value 0)
- **Padding variations**: Test with different padding (=, ==)

#### Edge Cases:
- **Empty valid base64**: `"AA=="` → `0`
- **Single character**: `"QQ=="` → should work
- **Long base64 strings**: Test with very long encoded values

#### Failure Cases:
- **Invalid base64 characters**: `"!@#$"` → ValueError
- **Incorrect padding**: `"QQ"` (missing padding) → should raise ValueError
- **Empty string**: `""` → ValueError
- **Non-string input**: `123` → should raise appropriate error

### 1.4 `number_to_base64()` Function Tests

#### Success Cases:
- **Small numbers**: `0` → valid base64, `1` → `"AQ=="`, `65` → `"QQ=="`
- **Large numbers**: `65537` → `"AQAB"`, `1000000` → valid base64
- **Powers of 2**: `256`, `512`, `1024` → valid base64 strings

#### Edge Cases:
- **Zero**: `0` → should handle gracefully
- **Maximum integer values**: Test with very large integers

#### Failure Cases:
- **Negative numbers**: `-1` → should raise ValueError or handle appropriately
- **Non-integer types**: `1.5` → should raise appropriate error
- **String input**: `"123"` → should raise TypeError

---

## 2. Integration Tests for Flask Routes

### 2.1 `GET /` Route Tests

#### Success Cases:
- **Basic GET request**: Should return 200 status code
- **HTML content**: Should return the complete HTML template
- **Content-Type**: Should be `text/html`

### 2.2 `POST /convert` Route Tests

#### Success Cases - All Format Combinations:
Test all 36 possible conversion combinations (6 input types × 6 output types):

**From Text:**
- Text → Text: `"five"` → `"five"`
- Text → Binary: `"five"` → `"101"`
- Text → Octal: `"five"` → `"5"`
- Text → Decimal: `"five"` → `"5"`
- Text → Hexadecimal: `"five"` → `"5"`
- Text → Base64: `"five"` → appropriate base64

**From Binary:**
- Binary → Text: `"101"` → `"five"`
- Binary → Binary: `"101"` → `"101"`
- Binary → Octal: `"101"` → `"5"`
- Binary → Decimal: `"101"` → `"5"`
- Binary → Hexadecimal: `"101"` → `"5"`
- Binary → Base64: `"101"` → appropriate base64

**From Octal:**
- Octal → Text: `"5"` → `"five"`
- Octal → Binary: `"5"` → `"101"`
- Octal → Octal: `"5"` → `"5"`
- Octal → Decimal: `"5"` → `"5"`
- Octal → Hexadecimal: `"5"` → `"5"`
- Octal → Base64: `"5"` → appropriate base64

**From Decimal:**
- Decimal → Text: `"5"` → `"five"`
- Decimal → Binary: `"5"` → `"101"`
- Decimal → Octal: `"5"` → `"5"`
- Decimal → Decimal: `"5"` → `"5"`
- Decimal → Hexadecimal: `"5"` → `"5"`
- Decimal → Base64: `"5"` → appropriate base64

**From Hexadecimal:**
- Hexadecimal → Text: `"5"` → `"five"`
- Hexadecimal → Binary: `"5"` → `"101"`
- Hexadecimal → Octal: `"5"` → `"5"`
- Hexadecimal → Decimal: `"5"` → `"5"`
- Hexadecimal → Hexadecimal: `"5"` → `"5"`
- Hexadecimal → Base64: `"5"` → appropriate base64

**From Base64:**
- Base64 → Text: Valid base64 → appropriate text
- Base64 → Binary: Valid base64 → appropriate binary
- Base64 → Octal: Valid base64 → appropriate octal
- Base64 → Decimal: Valid base64 → appropriate decimal
- Base64 → Hexadecimal: Valid base64 → appropriate hex
- Base64 → Base64: Valid base64 → same base64

---

## 3. Edge Cases and Boundary Conditions

### 3.1 Numeric Boundary Tests
- **Zero handling**: All formats converting to/from 0
- **Maximum integer values**: Test with `sys.maxsize`
- **Minimum values**: Test with negative numbers where applicable
- **Single digit numbers**: 0-9 in all formats
- **Powers of 2**: 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024
- **Powers of 10**: 1, 10, 100, 1000, 10000

### 3.2 String Boundary Tests
- **Empty inputs**: `""` for all input types
- **Whitespace only**: `"   "`, `"\t"`, `"\n"`
- **Very long inputs**: Test with extremely long valid strings
- **Unicode characters**: Test with non-ASCII characters

### 3.3 Base64 Specific Edge Cases
- **Padding edge cases**: Strings with 0, 1, 2 padding characters
- **URL-safe base64**: Test if application handles URL-safe variants
- **Line breaks in base64**: Multi-line base64 strings

---

## 4. Error Handling and Exception Cases

### 4.1 HTTP Error Cases
- **Missing JSON body**: POST request without JSON → should return error
- **Malformed JSON**: Invalid JSON syntax → should return error
- **Missing required fields**: JSON without `input`, `inputType`, or `outputType`
- **Wrong HTTP method**: GET request to `/convert` → should return 405

### 4.2 Input Validation Error Cases
- **Invalid input types**: `inputType` not in allowed values
- **Invalid output types**: `outputType` not in allowed values
- **Null/None inputs**: `null` values in JSON fields

### 4.3 Conversion Error Cases

#### Binary Input Errors:
- **Invalid binary digits**: `"102"`, `"abc"`, `"1.0"`
- **Empty binary string**: `""`
- **Binary with spaces**: `"10 11"`

#### Octal Input Errors:
- **Invalid octal digits**: `"89"`, `"abc"`
- **Octal with decimal point**: `"7.5"`

#### Decimal Input Errors:
- **Non-numeric strings**: `"abc"`, `"12.34.56"`
- **Scientific notation**: `"1e5"` (may or may not be supported)
- **Decimal with letters**: `"123abc"`

#### Hexadecimal Input Errors:
- **Invalid hex characters**: `"xyz"`, `"gg"`
- **Hex with spaces**: `"ff aa"`
- **Hex with decimal**: `"ff.aa"`

#### Text Input Errors:
- **Unsupported number words**: `"eleven"`, `"twenty"`, `"hundred"`
- **Multiple numbers**: `"one two"`
- **Mixed text and numbers**: `"1 one"`

#### Base64 Input Errors:
- **Invalid characters**: `"@#$%"`
- **Incorrect length**: Strings that aren't multiples of 4
- **Invalid padding**: Incorrect use of `=` characters

---

## 5. Input Validation Tests

### 5.1 Content-Type Validation
- **Correct Content-Type**: `application/json`
- **Incorrect Content-Type**: `text/plain`, `application/xml`
- **Missing Content-Type**: No Content-Type header

### 5.2 JSON Structure Validation
- **Valid JSON structure**: Proper `input`, `inputType`, `outputType` fields
- **Extra fields**: JSON with additional unexpected fields
- **Wrong data types**: String where integer expected, etc.

### 5.3 Input Length Validation
- **Very short inputs**: Single character inputs
- **Very long inputs**: Extremely long strings (test for potential DoS)
- **Maximum reasonable length**: Test application limits

---

## 6. Security Tests

### 9.1 Input Sanitization
- **SQL injection attempts**: Test with SQL-like strings
- **XSS attempts**: Test with HTML/JavaScript in inputs
- **Path traversal**: Test with file path strings

### 9.2 DoS Protection
- **Extremely large inputs**: Test application limits
- **Resource exhaustion**: Very complex calculations

---

## Implementation Notes for Pytest

### Test Structure Recommendations:
1. **Separate test files**:
   - `test_unit_functions.py` - Unit tests for individual functions
   - `test_flask_routes.py` - Integration tests for Flask routes
   - `test_edge_cases.py` - Edge cases and boundary conditions
   - `test_error_handling.py` - Error scenarios

2. **Fixtures**:
   - Flask test client fixture
   - Sample data fixtures for different number formats
   - Mock data for testing edge cases

3. **Parameterized tests**:
   - Use `@pytest.mark.parametrize` for testing multiple input/output combinations
   - Create test matrices for all format conversions

4. **Test data organization**:
   - Separate test data files for large test cases
   - JSON files with test case definitions

### Coverage Goals:
- **Line coverage**: 100% of all functions
- **Branch coverage**: All conditional statements
- **Edge case coverage**: All boundary conditions
- **Error path coverage**: All exception handling paths

This comprehensive test plan ensures thorough validation of the numeric converter application, covering all functionality, edge cases, and potential failure modes.
