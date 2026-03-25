import os
import json
import httpx
from openai import OpenAI
from dotenv import load_dotenv
from vector_store import query_material

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

_client = None

def _get_client():
    global _client
    if _client is None:
        # Create a custom httpx client to avoid potential 'proxies' argument errors
        # caused by version mismatches between libraries using httpx
        # backend note: Increase timeout for long generation tasks
        http_client = httpx.Client(timeout=60.0)
        _client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            http_client=http_client
        )
    return _client


def build_cognitive_description(profile) -> str:
    if not profile:
        return "No cognitive profile available. Assume intermediate level across all domains."
    level = profile.level
    strengths, weaknesses = [], []
    scores = {
        "Logical Reasoning": profile.logical_score,
        "Working Memory": profile.memory_score,
        "Pattern Recognition": profile.pattern_score,
        "Problem Solving": profile.problem_solving_score,
    }
    for skill, score in scores.items():
        if score >= 70:
            strengths.append(skill)
        elif score < 50:
            weaknesses.append(skill)

    desc = f"Overall IQ Level: {profile.overall_iq:.1f} (Category: {level}).\n"
    if strengths:
        desc += f"Student's cognitive STRENGTHS: {', '.join(strengths)}. Lean into these with complex tasks.\n"
    if weaknesses:
        desc += f"Student's cognitive AREAS FOR GROWTH: {', '.join(weaknesses)}. Provide scaffolding, step-by-step guidance, and visual cues for these areas.\n"
    if hasattr(profile, 'interests') and profile.interests:
        desc += f"Student's PERSONAL INTERESTS: {profile.interests}. Integrate these themes into the assignment to boost engagement.\n"
    return desc


def generate_assignment(
    student_name: str,
    topic: str,
    cognitive_profile,
    material_id: int | None = None,
    difficulty_level: str = "intermediate"
) -> dict:
    """Call the Groq API (Llama 3.3 70B) with a RAG-enhanced prompt to generate a personalized assignment."""

    # 1. Retrieve context from the vector store
    retrieved_chunks = query_material(query=topic, material_id=material_id, n_results=5)
    context_text = "\n\n".join(retrieved_chunks) if retrieved_chunks else "No specific course material uploaded. Generate a general assignment on the topic."

    # 2. Build cognitive description
    cognitive_desc = build_cognitive_description(cognitive_profile)

    # 3. Build the full prompt
    system_prompt = """You are an expert instructional designer and cognitive psychologist specializing in Cognitive Learning Theory (CLT). 
Your role is to create highly personalized, game-based assignments for individual students.
All assignments must adhere to CLT principles: active processing, schema building, metacognitive reflection, and cognitive load management.
IMPORTANT: Always respond with valid JSON only. No markdown fences, no extra commentary."""

    user_prompt = f"""Create a personalized game-based IQ assignment for the following student.

STUDENT NAME: {student_name}
TOPIC: {topic}
DIFFICULTY LEVEL: {difficulty_level}

STUDENT COGNITIVE PROFILE:
{cognitive_desc}

COURSE MATERIAL CONTEXT (Use this as the knowledge base for your assignment):
---
{context_text}
---

TASK: Generate a complete, personalized assignment in the EXACT JSON format below. Tailor the tasks and difficulty to the student's specific cognitive strengths and weaknesses.

{{
  "title": "Assignment title",
  "introduction": "A brief, engaging introduction to the assignment (2-3 sentences, connect to prior knowledge per schema theory)",
  "learning_objectives": ["objective 1", "objective 2", "objective 3"],
  "zones": [
    {{
      "zone_number": 1,
      "zone_name": "Zone name (e.g. Pattern Labyrinth)",
      "cognitive_focus": "Which cognitive skill this zone targets",
      "description": "Detailed description of the game-based task",
      "instructions": ["step 1", "step 2", "step 3"],
      "expected_output": "What the student must submit for this zone"
    }},
    {{
      "zone_number": 2,
      "zone_name": "Zone name",
      "cognitive_focus": "Which cognitive skill this zone targets",
      "description": "Detailed description of the task",
      "instructions": ["step 1", "step 2"],
      "expected_output": "What the student must submit"
    }},
    {{
      "zone_number": 3,
      "zone_name": "Zone name",
      "cognitive_focus": "Which cognitive skill",
      "description": "Task description",
      "instructions": ["step 1", "step 2"],
      "expected_output": "Student output"
    }}
  ],
  "reflection_questions": ["question 1", "question 2"],
  "scoring_rubric": {{
    "criteria_1": {{"max_points": 10, "criteria": "Description"}},
    "criteria_2": {{"max_points": 10, "criteria": "Description"}}
  }},
  "teacher_note": "Confidential note for the teacher on how to support this specific student"
}}
"""

    try:
        client = _get_client()
        # Using Llama 3.1 8b instant for speed
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2500,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content or "{}")
    except Exception as e:
        print(f"Error generating assignment: {e}")
        # Fallback if API fails
        return {
            "title": f"Assignment: {topic}",
            "introduction": "We encountered an error generating the personalized content. Please try again.",
            "learning_objectives": [],
            "zones": [],
            "reflection_questions": [],
            "scoring_rubric": {},
            "teacher_note": "Error: " + str(e)
        }


def chat_with_agent(
    student_name: str,
    profile,
    message: str,
    history: list[dict] = [],
    context: str = "",
    assignment_context: str = ""
):
    """
    Chat with an AI agent. Now includes conversation history to maintain context.
    """
    client = _get_client()

    cognitive_desc = build_cognitive_description(profile)

    system_prompt = f"""You are a personalized AI tutor for a student named {student_name}.
You are helpful, encouraging, and use the Socratic method.
Maintain the persona of a dedicated tutor who knows this student well.
Do not give answers directly.

STUDENT PROFILE:
{cognitive_desc}

CURRENT CONTEXT:
{assignment_context}
{context}
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Add history (last 10 messages max to save context window)
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": message})

    try:
        # Explicit type cast for messages to satisfy strict type checkers
        final_messages: list[dict[str, str]] = messages # type: ignore
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=final_messages,
            temperature=0.7,
            max_tokens=800
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"I'm having trouble connecting right now. Please try again. (Error: {str(e)})"
