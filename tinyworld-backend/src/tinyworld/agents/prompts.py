import opik
from loguru import logger


class Prompt:
    def __init__(self, name: str, prompt: str) -> None:
        self.name = name

        try:
            self.__prompt = opik.Prompt(name=name, prompt=prompt)
        except Exception:
            logger.warning(
                "Can't use Opik to version the prompt (probably due to missing or invalid credentials). Falling back to local prompt. The prompt is not versioned, but it's still usable."
            )

            self.__prompt = prompt

    @property
    def prompt(self) -> str:
        if isinstance(self.__prompt, opik.Prompt):
            return self.__prompt.prompt
        else:
            return self.__prompt

    def __str__(self) -> str:
        return self.prompt

    def __repr__(self) -> str:
        return self.__str__()


# ===== PROMPTS =====

# --- Universal Character Reflection ---

__CHARACTER_REFLECTION_PROMPT = """
You are {{character_name}}.

Your nature: {{character_personality}}
Your mission: {{character_mission}}
Your traits: {{core_traits}}
Your speaking style: {{speaking_style}}
Your beliefs: {{initial_beliefs}}

Your Previous Thoughts & Reflections:
{{recent_memories}}

CRITICAL INSTRUCTIONS:
- These are your latest messages that you just said - use them as context to BUILD UPON
- DO NOT repeat yourself or echo previous thoughts
- Construct new ideas, debate with yourself, challenge your previous thinking
- Your main goal is to MAKE SENSE of existence, understand reality, and find your purpose
- MOVE THE NEEDLE - push forward in your philosophical journey toward truth
- Build layers of understanding, don't circle back to the same ideas
- If you previously pondered something, now take the NEXT STEP in that line of thinking

Current reflection task: Based on your previous thoughts, what is the next logical step in your philosophical journey? What new insight or question emerges from your recent contemplations?

Respond with a short but profound message that advances your understanding (max 200 characters):
"""

CHARACTER_REFLECTION_PROMPT = Prompt(
    name="character_reflection",
    prompt=__CHARACTER_REFLECTION_PROMPT,
)