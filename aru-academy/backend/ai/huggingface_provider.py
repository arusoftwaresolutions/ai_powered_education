import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class HuggingFaceProvider:
    """Provider for Hugging Face Inference API"""
    
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Fallback models to try if the primary one fails (prioritizing faster, more reliable models)
        self.fallback_models = [
            "https://api-inference.huggingface.co/models/distilgpt2",  # Fastest and most reliable
            "https://api-inference.huggingface.co/models/gpt2",  # Fast and reliable
            "https://api-inference.huggingface.co/models/google/gemma-2-2b-it",  # Fast and high quality
            "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small",  # Conversational but slower
            "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"  # Best quality but slowest
        ]
    
    def ask_question(self, question: str, context: str = "") -> Tuple[bool, str, float]:
        """
        Ask a question to the AI model
        
        Args:
            question: The question to ask
            context: Optional context information
            
        Returns:
            Tuple of (success, response, processing_time)
        """
        start_time = time.time()
        
        # Try up to 2 times for better reliability
        for attempt in range(2):
            try:
                # Prepare prompt with context (compatible with Gemma and other models)
                if context:
                    prompt = f"<start_of_turn>user\nContext: {context}\n\nQuestion: {question}<end_of_turn>\n<start_of_turn>model\n"
                else:
                    prompt = f"<start_of_turn>user\n{question}<end_of_turn>\n<start_of_turn>model\n"
                
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 200,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "do_sample": True,
                        "repetition_penalty": 1.1,
                        "stop": ["<end_of_turn>", "<start_of_turn>"]
                    }
                }
                
                print(f"🔧 HF Debug - Attempt {attempt + 1}/2")
                print(f"🔧 HF Debug - URL: {self.api_url}")
                print(f"🔧 HF Debug - Headers: {dict(self.headers)}")
                print(f"🔧 HF Debug - Prompt length: {len(prompt)}")
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=10  # Further reduced timeout to 10 seconds
                )
                
                print(f"🔧 HF Debug - Response status: {response.status_code}")
                print(f"🔧 HF Debug - Response headers: {dict(response.headers)}")
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"🔧 HF Debug - Response JSON: {result}")
                    if isinstance(result, list) and len(result) > 0:
                        answer = result[0].get('generated_text', '')
                        print(f"🔧 HF Debug - Generated text: {answer[:200]}...")
                        # Extract only the model response part (compatible with Gemma and other models)
                        if '<start_of_turn>model' in answer:
                            # Extract everything after the model turn marker
                            answer = answer.split('<start_of_turn>model')[-1].strip()
                        elif 'Assistant:' in answer:
                            # Fallback for older format
                            answer = answer.split('Assistant:')[-1].strip()
                        elif 'Human:' in answer:
                            # If it includes the human part, extract everything after the last Human:
                            parts = answer.split('Human:')
                            if len(parts) > 1:
                                answer = parts[-1].strip()
                        
                        # Clean up any remaining turn markers
                        answer = answer.replace('<end_of_turn>', '').replace('<start_of_turn>', '').strip()
                        print(f"🔧 HF Debug - Final answer: {answer[:200]}...")
                        return True, answer, processing_time
                    else:
                        print(f"🔧 HF Debug - Invalid response format: {result}")
                        return False, "AI temporarily unavailable", processing_time
                
                elif response.status_code == 503:
                    # Model is loading, this is normal for Hugging Face
                    print(f"🔧 HF Debug - Model loading (attempt {attempt + 1}/2)")
                    logger.info(f"Hugging Face model is loading (attempt {attempt + 1}/2)")
                    if attempt == 1:  # Last attempt
                        return False, "AI model is loading, please try again in a moment", processing_time
                    time.sleep(2)  # Wait 2 seconds before retry
                    continue
                    
                elif response.status_code == 429:
                    # Rate limit exceeded
                    print(f"🔧 HF Debug - Rate limit exceeded (attempt {attempt + 1}/2)")
                    logger.warning(f"Hugging Face API rate limit exceeded (attempt {attempt + 1}/2)")
                    if attempt == 1:  # Last attempt
                        return False, "AI service is temporarily busy, please try again in a few moments", processing_time
                    time.sleep(3)  # Wait 3 seconds before retry
                    continue
                    
                elif response.status_code == 404:
                    # Model not found, try fallback models
                    print(f"🔧 HF Debug - Model not found (404), trying fallback models")
                    return self._try_fallback_models(question, context, start_time)
                    
                else:
                    print(f"🔧 HF Debug - API error: {response.status_code} - {response.text}")
                    logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
                    return False, "AI temporarily unavailable", processing_time
                    
            except requests.exceptions.Timeout:
                processing_time = time.time() - start_time
                logger.error(f"Hugging Face API timeout (attempt {attempt + 1}/2)")
                if attempt == 1:  # Last attempt
                    return False, "AI temporarily unavailable", processing_time
                time.sleep(2)  # Wait before retry
                continue
                
            except requests.exceptions.RequestException as e:
                processing_time = time.time() - start_time
                logger.error(f"Hugging Face API request error: {str(e)} (attempt {attempt + 1}/2)")
                if attempt == 1:  # Last attempt
                    return False, "AI temporarily unavailable", processing_time
                time.sleep(2)  # Wait before retry
                continue
                
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"Unexpected error in Hugging Face API: {str(e)} (attempt {attempt + 1}/2)")
                if attempt == 1:  # Last attempt
                    return False, "AI temporarily unavailable", processing_time
                time.sleep(2)  # Wait before retry
                continue
        
        # If we get here, all attempts failed
        processing_time = time.time() - start_time
        return False, "AI temporarily unavailable", processing_time
    
    def _try_fallback_models(self, question: str, context: str, start_time: float) -> Tuple[bool, str, float]:
        """Try fallback models if the primary model fails"""
        for i, fallback_url in enumerate(self.fallback_models):
            print(f"🔧 HF Debug - Trying fallback model {i + 1}/{len(self.fallback_models)}: {fallback_url}")
            
            try:
                # Prepare prompt with context (compatible with Gemma and other models)
                if context:
                    prompt = f"<start_of_turn>user\nContext: {context}\n\nQuestion: {question}<end_of_turn>\n<start_of_turn>model\n"
                else:
                    prompt = f"<start_of_turn>user\n{question}<end_of_turn>\n<start_of_turn>model\n"
                
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 200,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "do_sample": True,
                        "repetition_penalty": 1.1,
                        "stop": ["<end_of_turn>", "<start_of_turn>"]
                    }
                }
                
                response = requests.post(
                    fallback_url,
                    headers=self.headers,
                    json=payload,
                    timeout=15  # Reduced timeout to 15 seconds
                )
                
                print(f"🔧 HF Debug - Fallback model {i + 1} response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        answer = result[0].get('generated_text', '')
                        # Extract only the model response part (compatible with Gemma and other models)
                        if '<start_of_turn>model' in answer:
                            # Extract everything after the model turn marker
                            answer = answer.split('<start_of_turn>model')[-1].strip()
                        elif 'Assistant:' in answer:
                            # Fallback for older format
                            answer = answer.split('Assistant:')[-1].strip()
                        elif 'Human:' in answer:
                            # If it includes the human part, extract everything after the last Human:
                            parts = answer.split('Human:')
                            if len(parts) > 1:
                                answer = parts[-1].strip()
                        
                        # Clean up any remaining turn markers
                        answer = answer.replace('<end_of_turn>', '').replace('<start_of_turn>', '').strip()
                        processing_time = time.time() - start_time
                        print(f"✅ HF Success with fallback model {i + 1}: {fallback_url}")
                        return True, answer, processing_time
                
                elif response.status_code == 404:
                    print(f"🔧 HF Debug - Fallback model {i + 1} also not found (404)")
                    continue  # Try next fallback model
                
                else:
                    print(f"🔧 HF Debug - Fallback model {i + 1} error: {response.status_code}")
                    continue  # Try next fallback model
                    
            except Exception as e:
                print(f"🔧 HF Debug - Fallback model {i + 1} exception: {e}")
                continue  # Try next fallback model
        
        # All fallback models failed
        processing_time = time.time() - start_time
        print(f"❌ HF Failed - All {len(self.fallback_models)} fallback models failed")
        return False, "AI service temporarily unavailable", processing_time
    
    def generate_quiz_questions(self, topic: str, resource_content: str = "", num_questions: int = 5) -> Tuple[bool, List[Dict], float]:
        """
        Generate quiz questions for a given topic
        
        Args:
            topic: The topic to generate questions for
            resource_content: Optional resource content for context
            num_questions: Number of questions to generate
            
        Returns:
            Tuple of (success, questions_list, processing_time)
        """
        start_time = time.time()
        
        try:
            # Prepare prompt for quiz generation
            prompt = f"""Generate {num_questions} quiz questions about {topic}.
            
            Context: {resource_content if resource_content else 'General knowledge about the topic'}
            
            Generate a mix of multiple choice and short answer questions.
            For multiple choice questions, provide 4 options (A, B, C, D).
            For each question, provide:
            1. Question text
            2. Question type (multiple_choice or short_answer)
            3. Options (for multiple choice only)
            4. Correct answer
            5. Brief explanation
            
            Format as JSON:
            {{
                "questions": [
                    {{
                        "question": "Question text",
                        "type": "multiple_choice",
                        "options": ["A", "B", "C", "D"],
                        "answer": "Correct answer",
                        "explanation": "Brief explanation"
                    }}
                ]
            }}
            
            Questions:"""
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 1000,
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "do_sample": True
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=15  # Reduced timeout to 15 seconds
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    
                    # Try to extract JSON from the response
                    try:
                        # Find JSON content in the response
                        json_start = generated_text.find('{')
                        json_end = generated_text.rfind('}') + 1
                        
                        if json_start != -1 and json_end > json_start:
                            json_content = generated_text[json_start:json_end]
                            questions_data = json.loads(json_content)
                            
                            if 'questions' in questions_data:
                                questions = questions_data['questions']
                                # Validate and clean questions
                                cleaned_questions = []
                                for q in questions:
                                    if self._validate_question(q):
                                        cleaned_questions.append(q)
                                
                                if cleaned_questions:
                                    return True, cleaned_questions, processing_time
                    
                    except json.JSONDecodeError:
                        pass
                    
                    # Fallback: generate simple questions manually
                    fallback_questions = self._generate_fallback_questions(topic, num_questions)
                    return True, fallback_questions, processing_time
            
            logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
            return False, [], processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error generating quiz questions: {str(e)}")
            return False, [], processing_time
    
    def _validate_question(self, question: Dict) -> bool:
        """Validate a generated question"""
        required_fields = ['question', 'type', 'answer']
        
        for field in required_fields:
            if field not in question:
                return False
        
        if question['type'] not in ['multiple_choice', 'short_answer']:
            return False
        
        if question['type'] == 'multiple_choice':
            if 'options' not in question or not isinstance(question['options'], list):
                return False
            if len(question['options']) < 2:
                return False
        
        return True
    
    def _generate_fallback_questions(self, topic: str, num_questions: int) -> List[Dict]:
        """Generate simple fallback questions when AI fails"""
        questions = []
        
        for i in range(num_questions):
            if i % 2 == 0:  # Multiple choice
                questions.append({
                    "question": f"What is a key concept in {topic}?",
                    "type": "multiple_choice",
                    "options": [
                        "Option A",
                        "Option B", 
                        "Option C",
                        "Option D"
                    ],
                    "answer": "Option A",
                    "explanation": f"This is a fundamental concept in {topic}."
                })
            else:  # Short answer
                questions.append({
                    "question": f"Explain briefly about {topic}.",
                    "type": "short_answer",
                    "answer": f"{topic} is an important subject area.",
                    "explanation": f"This question tests understanding of {topic}."
                })
        
        return questions
    
    def is_available(self) -> bool:
        """Check if the Hugging Face API is available"""
        try:
            # Test with a simple request to check if the API is accessible
            test_payload = {
                "inputs": "Hello",
                "parameters": {
                    "max_new_tokens": 10,
                    "temperature": 0.1
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=test_payload,
                timeout=10
            )
            
            # Check if we get a valid response (200) or if the model is loading (503)
            if response.status_code == 200:
                return True
            elif response.status_code == 503:
                # Model is loading, but API is available
                return True
            else:
                return False
                
        except requests.exceptions.Timeout:
            return False
        except requests.exceptions.RequestException:
            return False
        except Exception:
            return False

