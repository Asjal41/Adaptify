import json
import os
from openai import OpenAI
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class BaseAgent:
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            http_client=httpx.Client(timeout=60.0)
        )
        self.model = model

    def _generate_json(self, system_prompt: str, user_prompt: str):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt + "\n\nIMPORTANT: Return ONLY valid JSON."},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content or "{}")
        except Exception as e:
            print(f"Agent JSON Error: {e}")
            return {}

    def _generate_text(self, messages: list):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,
                max_tokens=1024
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Agent Text Error: {e}")
            return "I'm having trouble connecting right now. Please try again."


class DesignerAgent(BaseAgent):
    """
    Role: Instructional Designer
    Goal: Create personalized assignment structures (JSON) based on CLT.
    """
    def generate_assignment(self, student_name, topic, cognitive_profile, context_text, difficulty):
        # Build cognitive strengths description
        desc = f"IQ Level: {cognitive_profile.overall_iq}. Level: {cognitive_profile.level}."
        if cognitive_profile.interests:
            desc += f" Interests: {cognitive_profile.interests}."
        
        system_prompt = """You are an expert Instructional Designer Agent.
        Create a game-based assignment structure (JSON) tailored to the student's cognitive profile.
        Follow Cognitive Learning Theory principles."""
        
        user_prompt = f"""
        Student: {student_name}
        Profile: {desc}
        Topic: {topic}
        Difficulty: {difficulty}
        Material: {context_text[:2000]}...
        
        Generate JSON with keys: title, introduction, learning_objectives (list of strings), zones (list of objects with zone_name, cognitive_focus, description, instructions (list of strings), expected_output), reflection_questions (list of strings), teacher_note.
        Ensure "instructions" is always a list of step-by-step strings.
        """
        return self._generate_json(system_prompt, user_prompt)


class TutorAgent(BaseAgent):
    """
    Role: Personal Tutor
    Goal: Socratic guidance and answering questions using context.
    """
    def __init__(self):
        super().__init__(model="llama-3.1-8b-instant") # Faster for chat

    def chat(self, student_name, profile, message, history, context, assignment_context):
        system_prompt = f"""You are a Personal Tutor Agent for {student_name}.
        Style: Encouraging, Socratic (ask guiding questions), Adaptive.
        Profile: {profile.level} learner. Interests: {profile.interests}.
        Current Task: {assignment_context}
        Context: {context}
        """
        
        msgs = [{"role": "system", "content": system_prompt}]
        msgs.extend(history) # structured as [{"role": "user", "content": "..."}, ...]
        msgs.append({"role": "user", "content": message})
        
        return self._generate_text(msgs)


class GraderAgent(BaseAgent):
    """
    Role: Evaluator & Feedback Specialist
    Goal: Grade submissions and provide constructive feedback.
    """
    def evaluate_submission(self, assignment_topic, assignment_content, student_submission):
        system_prompt = """You are a Grader Agent. 
        Evaluate the student's submission against the assignment requirements.
        Provide a grade (0-100) and constructive feedback text."""
        
        user_prompt = f"""
        Topic: {assignment_topic}
        Assignment Requirements: {str(assignment_content)[:1000]}...
        Student Submission: {student_submission}
        
        Return JSON with keys: "grade" (number), "feedback" (string).
        """
        return self._generate_json(system_prompt, user_prompt)
