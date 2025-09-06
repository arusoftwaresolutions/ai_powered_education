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
        
        try:
            # Prepare prompt with context
            if context:
                prompt = f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"
            else:
                prompt = f"Question: {question}\n\nAnswer:"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    answer = result[0].get('generated_text', '')
                    # Extract only the answer part
                    if 'Answer:' in answer:
                        answer = answer.split('Answer:')[-1].strip()
                    return True, answer, processing_time
                else:
                    return False, "AI temporarily unavailable", processing_time
            
            elif response.status_code == 503:
                # Model is loading, this is normal for Hugging Face
                logger.info("Hugging Face model is loading, this is normal")
                return False, "AI model is loading, please try again in a moment", processing_time
            else:
                logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
                return False, "AI temporarily unavailable", processing_time
                
        except requests.exceptions.Timeout:
            processing_time = time.time() - start_time
            logger.error("Hugging Face API timeout")
            return False, "AI temporarily unavailable", processing_time
            
        except requests.exceptions.RequestException as e:
            processing_time = time.time() - start_time
            logger.error(f"Hugging Face API request error: {str(e)}")
            return False, "AI temporarily unavailable", processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Unexpected error in Hugging Face API: {str(e)}")
            return False, "AI temporarily unavailable", processing_time
    
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
                timeout=45
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

