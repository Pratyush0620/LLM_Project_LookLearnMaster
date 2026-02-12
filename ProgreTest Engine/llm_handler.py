"""
LLM Handler Module
Handles all Cohere Command R+ API interactions for question generation and evaluation.
"""

import cohere
import json
import re
from typing import Dict, List, Optional


class AdaptiveLLM:
    """
    Handles LLM interactions for adaptive assessment.
    """
    
    DIFFICULTY_LEVELS = {
        1: "easy",
        2: "medium", 
        3: "hard"
    }
    
    def __init__(self, api_key: str):
        """
        Initialize the Cohere client.
        
        Args:
            api_key: Cohere API key
        """
        self.api_key = api_key
        try:
            # Try the newer ClientV2 first
            self.client = cohere.ClientV2(api_key=api_key)
            self.use_v2 = True
        except AttributeError:
            # Fall back to older Client
            self.client = cohere.Client(api_key=api_key)
            self.use_v2 = False
        # Use the latest available Command R+ model
        self.model = "command-r-plus-08-2024"
    
    def _call_chat(self, prompt: str) -> str:
        """
        Call the Cohere chat API with the appropriate method.
        """
        if self.use_v2:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.message.content[0].text
        else:
            response = self.client.chat(
                model=self.model,
                message=prompt
            )
            return response.text
    
    def generate_question(
        self, 
        content: str, 
        difficulty: int,
        asked_questions: List[str] = None,
        topic_focus: Optional[str] = None
    ) -> Dict:
        """
        Generate a question based on the content and difficulty level.
        
        Args:
            content: The PDF content to generate questions from
            difficulty: Difficulty level (1=easy, 2=medium, 3=hard)
            asked_questions: List of previously asked questions to avoid repetition
            topic_focus: Optional specific topic to focus on
            
        Returns:
            Dict with question, options, correct_answer, explanation, topic
        """
        difficulty_name = self.DIFFICULTY_LEVELS.get(difficulty, "medium")
        
        asked_list = ""
        if asked_questions:
            asked_list = "\n".join([f"- {q}" for q in asked_questions[-10:]])
            asked_list = f"\n\nAVOID THESE PREVIOUSLY ASKED QUESTIONS:\n{asked_list}"
        
        topic_instruction = ""
        if topic_focus:
            topic_instruction = f"\n\nFOCUS ON THIS TOPIC: {topic_focus}"
        
        prompt = f"""You are an expert educational assessment creator. Based on the following learning content, generate ONE {difficulty_name.upper()} difficulty multiple-choice question.

CONTENT:
{content[:6000]}

DIFFICULTY LEVEL: {difficulty_name.upper()}
- EASY: Basic recall and understanding questions. Test fundamental concepts.
- MEDIUM: Application and analysis questions. Require connecting ideas.
- HARD: Synthesis and evaluation questions. Require deep understanding and critical thinking.
{asked_list}{topic_instruction}

IMPORTANT: Generate a completely NEW question that tests understanding of the content.

Respond ONLY with a valid JSON object in this exact format (no markdown, no extra text):
{{
    "question": "The question text here?",
    "options": {{
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
    }},
    "correct_answer": "A",
    "explanation": "Explanation of why this is the correct answer.",
    "topic": "The main topic this question tests"
}}"""

        try:
            response_text = self._call_chat(prompt)
            
            # Extract JSON from response
            question_data = self._parse_json_response(response_text)
            question_data["difficulty"] = difficulty
            question_data["difficulty_name"] = difficulty_name
            
            return question_data
            
        except Exception as e:
            error_msg = str(e)
            return {
                "question": f"Error: {error_msg}",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": f"Error details: {error_msg}",
                "topic": "Unknown",
                "difficulty": difficulty,
                "difficulty_name": difficulty_name,
                "error": True,
                "error_message": error_msg
            }

    

    def evaluate_answer(
        self, 
        question: str, 
        user_answer: str, 
        correct_answer: str,
        options: Dict[str, str],
        content: str
    ) -> Dict:
        """
        Evaluate the user's answer and provide detailed feedback.
        
        Args:
            question: The question that was asked
            user_answer: The user's selected answer (A, B, C, or D)
            correct_answer: The correct answer letter
            options: Dict of all options
            content: Original content for context
            
        Returns:
            Dict with is_correct, feedback, suggestion
        """
        is_correct = user_answer.upper() == correct_answer.upper()
        
        if is_correct:
            return {
                "is_correct": True,
                "feedback": "Correct! Well done! 🎉",
                "suggestion": None
            }
        
        # Generate helpful feedback for incorrect answers
        prompt = f"""The student answered a question incorrectly. Provide helpful, encouraging feedback.

QUESTION: {question}

STUDENT'S ANSWER: {user_answer} - {options.get(user_answer, 'Unknown')}
CORRECT ANSWER: {correct_answer} - {options.get(correct_answer, 'Unknown')}

Provide a brief, encouraging explanation (2-3 sentences) of:
1. Why the correct answer is right
2. A tip to remember this concept

Keep it supportive and educational. Do not be discouraging."""

        try:
            feedback = self._call_chat(prompt)
            
            return {
                "is_correct": False,
                "feedback": feedback,
                "suggestion": f"Review the topic related to: {options.get(correct_answer, 'this concept')}"
            }
            
        except Exception as e:
            return {
                "is_correct": False,
                "feedback": f"The correct answer was {correct_answer}: {options.get(correct_answer, '')}",
                "suggestion": "Review this topic for better understanding."
            }
    
    def generate_improvement_suggestions(
        self,
        performance_data: Dict,
        weak_topics: List[str],
        content: str
    ) -> str:
        """
        Generate personalized improvement suggestions based on performance.
        
        Args:
            performance_data: Dict with performance metrics
            weak_topics: List of topics where user struggled
            content: Original content for context
            
        Returns:
            str: Formatted improvement suggestions
        """
        prompt = f"""Based on a student's assessment performance, provide personalized study recommendations.

PERFORMANCE SUMMARY:
- Total Questions: {performance_data.get('total_questions', 0)}
- Correct Answers: {performance_data.get('correct_answers', 0)}
- Accuracy: {performance_data.get('accuracy', 0):.1f}%
- Average Difficulty Reached: {performance_data.get('avg_difficulty', 1):.1f}/3

TOPICS NEEDING IMPROVEMENT:
{chr(10).join(['- ' + topic for topic in weak_topics]) if weak_topics else '- No specific weak areas identified'}

Provide 3-5 specific, actionable study recommendations. Include:
1. Which concepts to review
2. Study strategies for improvement
3. Practice suggestions

Keep it encouraging and constructive. Format with bullet points."""

        try:
            return self._call_chat(prompt)
            
        except Exception as e:
            return f"""
Based on your assessment, here are some general recommendations:

• Review the topics where you had incorrect answers
• Practice more questions at medium difficulty level
• Focus on understanding concepts rather than memorizing
• Consider revisiting the source material for weak areas
"""
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON from LLM response, handling potential formatting issues.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Dict: Parsed question data
        """
        # Try to find JSON in the response
        try:
            # First, try direct parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object pattern
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Return default structure if parsing fails
        raise ValueError("Could not parse JSON from response")
