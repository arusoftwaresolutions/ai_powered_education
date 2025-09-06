#!/usr/bin/env python3
"""
AI Debug Script - Test Hugging Face API connectivity
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_huggingface_api():
    """Test Hugging Face API with different models"""
    
    # Get API token
    api_token = os.getenv('HF_API_TOKEN')
    
    if not api_token:
        print("❌ HF_API_TOKEN not found in environment variables")
        print("💡 Please set HF_API_TOKEN in your .env file or environment")
        return False
    
    print(f"✅ API Token found: {api_token[:10]}...")
    
    # Test models in order of reliability
    test_models = [
        "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
        "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small", 
        "https://api-inference.huggingface.co/models/gpt2",
        "https://api-inference.huggingface.co/models/distilgpt2"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    for i, model_url in enumerate(test_models, 1):
        print(f"\n🧪 Testing Model {i}: {model_url}")
        
        # Test payload optimized for DialoGPT
        payload = {
            "inputs": "Human: What is 2+2?\n\nAssistant:",
            "parameters": {
                "max_new_tokens": 50,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True,
                "repetition_penalty": 1.1
            }
        }
        
        try:
            print(f"📤 Sending request to {model_url}")
            response = requests.post(model_url, headers=headers, json=payload, timeout=30)
            
            print(f"📥 Response Status: {response.status_code}")
            print(f"📥 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! Response: {result}")
                
                if isinstance(result, list) and len(result) > 0:
                    answer = result[0].get('generated_text', '')
                    print(f"🤖 Generated Text: {answer}")
                    
                    # Extract assistant response
                    if 'Assistant:' in answer:
                        clean_answer = answer.split('Assistant:')[-1].strip()
                        print(f"🎯 Clean Answer: {clean_answer}")
                    
                    print(f"✅ Model {i} is working! Use this URL: {model_url}")
                    return True
                else:
                    print(f"⚠️  Unexpected response format: {result}")
            elif response.status_code == 503:
                print(f"⏳ Model is loading (503) - this is normal for Hugging Face")
                print(f"💡 Try again in a few minutes")
            elif response.status_code == 401:
                print(f"❌ Authentication failed (401) - check your API token")
                return False
            elif response.status_code == 404:
                print(f"❌ Model not found (404)")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ Request timeout")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print(f"\n❌ All models failed. Check your API token and internet connection.")
    return False

def test_without_token():
    """Test if we can make requests without token (some models allow this)"""
    print(f"\n🧪 Testing without API token...")
    
    test_models = [
        "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
        "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small",
        "https://api-inference.huggingface.co/models/gpt2"
    ]
    
    for model_url in test_models:
        print(f"\n🧪 Testing {model_url} without token")
        
        payload = {
            "inputs": "Hello, how are you?",
            "parameters": {
                "max_new_tokens": 20,
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(model_url, json=payload, timeout=10)
            print(f"📥 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success without token! Response: {result}")
                return True
            else:
                print(f"❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    print("🔍 AI Debug Script - Testing Hugging Face API")
    print("=" * 50)
    
    # Test with token first
    success = test_huggingface_api()
    
    if not success:
        print(f"\n🔄 Trying without API token...")
        test_without_token()
    
    print(f"\n📋 Summary:")
    print(f"1. Check if HF_API_TOKEN is set in your environment")
    print(f"2. Verify the token is valid at https://huggingface.co/settings/tokens")
    print(f"3. Try the working model URL in your HF_API_URL environment variable")
    print(f"4. Some models may need time to load (503 errors are normal)")
