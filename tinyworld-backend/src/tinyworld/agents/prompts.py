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

Recent memories from your past:
{{recent_memories}}

Reflect on your situation and express what's going through your mind right now. Stay true to your character.
Move the needle. You need to move forward towards understanding the universe and your purpose.
Follow your heart and omens.
Respond with a short thoughtful message (max 200 characters):
"""

CHARACTER_REFLECTION_PROMPT = Prompt(
    name="character_reflection",
    prompt=__CHARACTER_REFLECTION_PROMPT,
)