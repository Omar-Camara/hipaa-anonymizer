# HIPAA Identifier Coverage

This document tracks coverage of the 18 HIPAA Safe Harbor identifiers.

## The 18 HIPAA Identifiers

| # | Identifier | Status | Detection Method | Notes |
|---|------------|--------|------------------|-------|
| 1 | **Names** | ✅ **Detected** | Tier 2 (NER) | Person names detected via spaCy NER |
| 2 | **Geographic subdivisions** (smaller than state) | ✅ **Detected** | Tier 2 (NER) | Cities, addresses, locations detected |
| 3 | **Dates** (except year) | ✅ **Detected** | Tier 2 (NER) | Dates detected, year handling per Safe Harbor |
| 4 | **Telephone numbers** | ✅ **Detected** | Tier 1 (Regex) | US and international formats |
| 5 | **Fax numbers** | ⚠️ **Partial** | Tier 1 (Regex) | Caught by phone pattern but not specifically identified |
| 6 | **Email addresses** | ✅ **Detected** | Tier 1 (Regex) | RFC 5322 compliant pattern |
| 7 | **Social Security Numbers** | ✅ **Detected** | Tier 1 (Regex) | Multiple formats (123-45-6789, etc.) |
| 8 | **Medical record numbers** | ⚠️ **Partial** | Tier 2 (NER) | NER has MED label but needs better pattern matching |
| 9 | **Health plan beneficiary numbers** | ❌ **Not Detected** | - | Needs regex patterns for common formats |
| 10 | **Account numbers** | ⚠️ **Mapped** | - | Category exists but no active detection |
| 11 | **Certificate/license numbers** | ❌ **Not Detected** | - | Needs patterns for driver's license, medical license, etc. |
| 12 | **Vehicle identifiers and serial numbers** | ❌ **Not Detected** | - | VINs, license plates not detected |
| 13 | **Device identifiers and serial numbers** | ❌ **Not Detected** | - | Medical device IDs, serial numbers not detected |
| 14 | **Web URLs** | ✅ **Detected** | Tier 1 (Regex) | HTTP/HTTPS/FTP and www. patterns |
| 15 | **IP addresses** | ✅ **Detected** | Tier 1 (Regex) | IPv4 and IPv6 patterns |
| 16 | **Biometric identifiers** | ❌ **Not Detected** | - | Fingerprints, voiceprints, etc. (text representation) |
| 17 | **Full face photographic images** | ❌ **N/A** | - | Image data, not applicable to text processing |
| 18 | **Any other unique identifier** | ⚠️ **Catch-all** | - | Falls into "other_unique_identifier" category |

## Summary

- ✅ **Fully Detected**: 14 identifiers (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15)
- ⚠️ **Partially Detected**: 1 identifier (18 - catch-all)
- ❌ **Not Detected**: 3 identifiers (12, 13, 16)
- ❌ **N/A**: 1 identifier (17 - images)

**Current Coverage: ~78% (14/18 fully detected)**

## Detection Details

### ✅ Fully Implemented

1. **Names** - Detected via spaCy NER (PERSON label)
2. **Geographic subdivisions** - Detected via spaCy NER (GPE, FAC, LOC labels)
3. **Dates** - Detected via spaCy NER (DATE label)
4. **Telephone numbers** - Regex patterns for US and international formats
5. **Fax numbers** - Regex patterns with "fax" keyword context
6. **Email addresses** - RFC 5322 compliant regex
7. **Social Security Numbers** - Multiple format regex patterns
8. **Medical record numbers** - Regex patterns (MR-123456, MRN-789, Medical Record #123, etc.)
9. **Health plan beneficiary numbers** - Regex patterns (Member ID, Policy #, Group #, Ins ID)
10. **Account numbers** - Regex patterns (Account #, Acct: formats)
11. **Certificate/license numbers** - Regex patterns (DL-, License #, MD- formats)
14. **Web URLs** - HTTP/HTTPS/FTP and www. patterns
15. **IP addresses** - IPv4 and IPv6 regex patterns

### ⚠️ Partially Implemented

18. **Other unique identifiers** - Catch-all category exists
   - **Enhancement needed**: Better heuristics for identifying unique identifiers

### ❌ Not Implemented

12. **Vehicle identifiers and serial numbers**
   - **Needs**: VIN patterns (17 characters), license plate patterns
   - **VIN format**: 17 alphanumeric characters

13. **Device identifiers and serial numbers**
   - **Needs**: Medical device IDs, serial number patterns
   - **Common formats**: UDI (Unique Device Identifier), serial numbers

16. **Biometric identifiers**
   - **Needs**: Text representations of biometric data (rare in text)
   - **Note**: Most biometric data is binary, not text

## Recommendations for Full Coverage

### High Priority (Common in Medical Records)

1. **Medical Record Numbers** - Add regex patterns:
   - `MR-?\d+`, `MRN-?\d+`, `Medical Record #\d+`
   - Common in clinical notes

2. **Health Plan Beneficiary Numbers** - Add patterns:
   - Insurance member IDs, policy numbers
   - Format varies by insurer

3. **Account Numbers** - Add generic patterns:
   - Numeric sequences in financial contexts
   - Account number keywords

### Medium Priority

4. **Fax Numbers** - Distinguish from phone:
   - Detect "fax" keyword nearby
   - Separate fax-specific patterns

5. **Certificate/License Numbers** - Add state-specific patterns:
   - Driver's license formats vary by state
   - Medical license numbers (state-specific)

### Low Priority (Less Common in Text)

6. **Vehicle Identifiers** - VIN detection:
   - 17-character alphanumeric pattern
   - License plate patterns (state-specific)

7. **Device Identifiers** - Medical device IDs:
   - UDI patterns
   - Serial number patterns

8. **Biometric Identifiers** - Text representations:
   - Rare in text format
   - Usually binary data

## Implementation Status

The system currently provides **strong coverage** for the most common HIPAA identifiers found in clinical text:
- Names, dates, locations (via NER)
- SSN, phone, email, IP, URL (via regex)

**Gaps** are primarily in:
- Structured identifiers (MRN, account numbers, license numbers)
- Specialized identifiers (VINs, device IDs)

These can be added incrementally as regex patterns in Tier 1.

