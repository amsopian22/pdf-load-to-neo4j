#!/usr/bin/env python3
"""
Test script to validate SK date extraction functionality
"""

import re
from datetime import datetime

def extract_sk_date_from_content(content):
    """Extract SK date from document content using various patterns"""
    
    # Indonesian month mapping
    months = {
        'januari': '01', 'februari': '02', 'maret': '03', 'april': '04',
        'mei': '05', 'juni': '06', 'juli': '07', 'agustus': '08',
        'september': '09', 'oktober': '10', 'november': '11', 'desember': '12'
    }
    
    date_patterns = [
        # Pattern: "12 Januari 2024" atau "12 januari 2024"
        r'(\d{1,2})\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+(\d{4})',
        # Pattern: "12-01-2024" atau "12/01/2024"
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        # Pattern: "2024-01-12"
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
        # Pattern dalam teks SK: "tanggal 12 Januari 2024"
        r'tanggal\s+(\d{1,2})\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+(\d{4})',
        # Pattern: "ditetapkan pada tanggal 12 Januari 2024"
        r'ditetapkan.*tanggal\s+(\d{1,2})\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+(\d{4})'
    ]
    
    content_lower = content.lower()
    
    for pattern in date_patterns:
        matches = re.findall(pattern, content_lower, re.IGNORECASE)
        if matches:
            match = matches[0]
            
            if len(match) == 3:
                if pattern.startswith(r'(\d{4})'):
                    # Format: YYYY-MM-DD
                    year, month, day = match
                    if month.isdigit():
                        return {
                            'raw_date': f"{day.zfill(2)}-{month.zfill(2)}-{year}",
                            'day': int(day) if day.isdigit() else int(month),
                            'month': int(month) if month.isdigit() else int(day),
                            'year': int(year),
                            'month_name': None,
                            'formatted_date': f"{year}-{month.zfill(2)}-{day.zfill(2) if day.isdigit() else month.zfill(2)}"
                        }
                elif match[1].isdigit():
                    # Format: DD-MM-YYYY atau DD/MM/YYYY
                    day, month, year = match
                    return {
                        'raw_date': f"{day.zfill(2)}-{month.zfill(2)}-{year}",
                        'day': int(day),
                        'month': int(month),
                        'year': int(year),
                        'month_name': None,
                        'formatted_date': f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    }
                else:
                    # Format dengan nama bulan: DD Month YYYY
                    day, month_name, year = match
                    month_num = months.get(month_name.lower(), '01')
                    return {
                        'raw_date': f"{day} {month_name.title()} {year}",
                        'day': int(day),
                        'month': int(month_num),
                        'year': int(year),
                        'month_name': month_name.title(),
                        'formatted_date': f"{year}-{month_num}-{day.zfill(2)}"
                    }
    
    return None

def test_sk_date_extraction():
    """Test SK date extraction with various input formats"""
    
    test_cases = [
        {
            'content': 'Keputusan ini ditetapkan pada tanggal 15 Januari 2024',
            'expected_year': 2024,
            'expected_month': 1,
            'expected_day': 15
        },
        {
            'content': 'SK nomor 123/2024 tanggal 05 Februari 2024',
            'expected_year': 2024,
            'expected_month': 2,
            'expected_day': 5
        },
        {
            'content': 'Ditetapkan di Jakarta pada tanggal 12-03-2024',
            'expected_year': 2024,
            'expected_month': 3,
            'expected_day': 12
        },
        {
            'content': 'Keputusan tertanggal 2024-04-20 tentang pengangkatan',
            'expected_year': 2024,
            'expected_month': 4,
            'expected_day': 20
        },
        {
            'content': 'Surat Keputusan tanggal 25/05/2024',
            'expected_year': 2024,
            'expected_month': 5,
            'expected_day': 25
        }
    ]
    
    print("=== Testing SK Date Extraction ===")
    
    for i, test_case in enumerate(test_cases, 1):
        content = test_case['content']
        expected_year = test_case['expected_year']
        expected_month = test_case['expected_month']
        expected_day = test_case['expected_day']
        
        result = extract_sk_date_from_content(content)
        
        print(f"\nTest {i}:")
        print(f"Input: {content}")
        
        if result:
            print(f"Extracted: {result['raw_date']}")
            print(f"Formatted: {result['formatted_date']}")
            print(f"Day: {result['day']}, Month: {result['month']}, Year: {result['year']}")
            
            # Verify results
            if (result['year'] == expected_year and 
                result['month'] == expected_month and 
                result['day'] == expected_day):
                print("✅ PASS")
            else:
                print(f"❌ FAIL - Expected: {expected_day}/{expected_month}/{expected_year}")
        else:
            print("❌ FAIL - No date extracted")
    
    print(f"\n=== Testing Complete ===")

if __name__ == "__main__":
    test_sk_date_extraction()