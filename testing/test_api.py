#!/usr/bin/env python3
"""
API Testing Script for Translation Platform
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class TranslationAPITester:
    def __init__(self, api_endpoint: str, api_key: str = None):
        self.api_endpoint = api_endpoint
        self.headers = {'Content-Type': 'application/json'}
        if api_key:
            self.headers['X-API-Key'] = api_key

    def test_basic_translation(self) -> bool:
        """Test basic translation functionality"""
        print("🧪 Testing basic translation...")
        
        payload = {
            "source_language": "en",
            "target_languages": ["es", "fr"],
            "sentences": ["Hello world", "How are you?"]
        }
        
        try:
            response = requests.post(self.api_endpoint, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Basic translation test passed")
                print(f"   Translation ID: {result.get('translation_id')}")
                return True
            else:
                print(f"❌ Basic translation test failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Basic translation test error: {str(e)}")
            return False

    def test_validation(self) -> bool:
        """Test input validation"""
        print("🧪 Testing input validation...")
        
        test_cases = [
            # Missing required field
            {
                "payload": {"source_language": "en", "target_languages": ["es"]},
                "expected_status": 400,
                "description": "Missing sentences field"
            },
            # Invalid language code
            {
                "payload": {
                    "source_language": "invalid",
                    "target_languages": ["es"],
                    "sentences": ["test"]
                },
                "expected_status": 400,
                "description": "Invalid source language code"
            },
            # Empty sentences array
            {
                "payload": {
                    "source_language": "en",
                    "target_languages": ["es"],
                    "sentences": []
                },
                "expected_status": 400,
                "description": "Empty sentences array"
            }
        ]
        
        passed = 0
        for i, test_case in enumerate(test_cases):
            try:
                response = requests.post(
                    self.api_endpoint, 
                    headers=self.headers, 
                    json=test_case["payload"]
                )
                
                if response.status_code == test_case["expected_status"]:
                    print(f"   ✅ Validation test {i+1} passed: {test_case['description']}")
                    passed += 1
                else:
                    print(f"   ❌ Validation test {i+1} failed: {test_case['description']}")
                    print(f"      Expected {test_case['expected_status']}, got {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Validation test {i+1} error: {str(e)}")
        
        success = passed == len(test_cases)
        print(f"{'✅' if success else '❌'} Validation tests: {passed}/{len(test_cases)} passed")
        return success

    def test_multiple_languages(self) -> bool:
        """Test translation to multiple languages"""
        print("🧪 Testing multiple language translation...")
        
        payload = {
            "source_language": "en",
            "target_languages": ["es", "fr", "de", "it", "pt"],
            "sentences": ["Good morning", "Thank you", "Welcome"]
        }
        
        try:
            response = requests.post(self.api_endpoint, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('summary', {})
                expected_translations = len(payload['sentences']) * len(payload['target_languages'])
                actual_translations = summary.get('translations_generated', 0)
                
                if actual_translations == expected_translations:
                    print(f"✅ Multiple language test passed")
                    print(f"   Generated {actual_translations} translations")
                    return True
                else:
                    print(f"❌ Multiple language test failed")
                    print(f"   Expected {expected_translations}, got {actual_translations}")
                    return False
            else:
                print(f"❌ Multiple language test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Multiple language test error: {str(e)}")
            return False

    def test_performance(self) -> bool:
        """Test API performance"""
        print("🧪 Testing API performance...")
        
        payload = {
            "source_language": "en",
            "target_languages": ["es"],
            "sentences": ["Performance test sentence"] * 50  # 50 sentences
        }
        
        try:
            start_time = time.time()
            response = requests.post(self.api_endpoint, headers=self.headers, json=payload)
            end_time = time.time()
            
            duration = end_time - start_time
            
            if response.status_code == 200 and duration < 30:  # Should complete within 30 seconds
                print(f"✅ Performance test passed")
                print(f"   Duration: {duration:.2f} seconds for 50 sentences")
                return True
            else:
                print(f"❌ Performance test failed")
                print(f"   Duration: {duration:.2f} seconds (>30s threshold)")
                print(f"   Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Performance test error: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Run all test suites"""
        print("🚀 Starting Translation Platform API Tests")
        print(f"Endpoint: {self.api_endpoint}")
        print("=" * 50)
        
        tests = [
            self.test_basic_translation,
            self.test_validation,
            self.test_multiple_languages,
            self.test_performance
        ]
        
        passed = 0
        for test in tests:
            if test():
                passed += 1
            print()
        
        print("=" * 50)
        success_rate = (passed / len(tests)) * 100
        print(f"📊 Test Results: {passed}/{len(tests)} tests passed ({success_rate:.1f}%)")
        
        if passed == len(tests):
            print("🎉 All tests passed! The translation platform is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the logs and fix issues.")
            return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <api_endpoint> [api_key]")
        print("Example: python test_api.py https://abc123.execute-api.eu-west-1.amazonaws.com/dev/translate")
        sys.exit(1)
    
    api_endpoint = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = TranslationAPITester(api_endpoint, api_key)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

