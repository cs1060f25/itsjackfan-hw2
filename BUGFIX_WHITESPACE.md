# Bug Fix: Whitespace Handling in Text-to-Number Conversion

## Problem
The `text_to_number()` function in `api/index.py` failed to handle leading/trailing whitespace, causing valid inputs like `" one "` to raise `ValueError` instead of returning `1`.

**Root Cause:** After regex processing on line 12, whitespace was preserved, causing dictionary lookup failures:
```python
text = re.sub(r'[^a-zA-Z\s-]', '', text.lower())  # " one " remains " one "
if text in number_words:  # " one " not found in {"one": 1}
```

## Solution
**File:** `api/index.py`  
**Change:** Added `text = text.strip()` on line 15 (after regex, before dictionary lookup)

```python
def text_to_number(text):
    """Convert English text number to integer"""
    # Remove any non-alphanumeric characters and convert to lowercase
    text = re.sub(r'[^a-zA-Z\s-]', '', text.lower())
    
    # Strip leading and trailing whitespace
    text = text.strip()  # <-- ADDED THIS LINE
    
    # Special case for zero
    if text in ['zero', 'nil']:
        return 0
```

## Results
**Fixed Tests:**
- ✅ `tests/test_unit_functions.py::TestTextToNumber::test_whitespace_handling`
- ✅ `tests/test_edge_cases.py::TestTextSpecificEdgeCases::test_text_mixed_case_with_spaces`

**Examples Now Working:**
```python
text_to_number(" one ")     # Returns 1 (was ValueError)
text_to_number("  two  ")   # Returns 2 (was ValueError) 
text_to_number("\tthree\t") # Returns 3 (was ValueError)
text_to_number("\nfour\n")  # Returns 4 (was ValueError)
```

**Regression Test:** All 9 existing `TestTextToNumber` tests continue to pass, confirming no functionality was broken.

**Impact:** Improves web application robustness for real-world user input containing accidental whitespace from HTML forms, copy-paste operations, and mobile keyboards.
