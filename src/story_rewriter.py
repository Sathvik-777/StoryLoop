from openai import OpenAI


class StoryRewriter:
    def __init__(self, client: OpenAI):
        self.client = client

    def rewrite_story(self, story: str, evaluation: dict):

        prompt = f"""
You are an expert short-form story editor.

An existing story was evaluated by another AI editor.
Your job is to improve the existing story based on that evaluation.

Do NOT completely replace the story with an unrelated story.

PRESERVE:
- The core premise
- The main characters
- The strongest parts of the original story
- The overall genre and tone

IMPROVE:
- The weaknesses identified by the evaluator
- The areas with low scores
- The overall emotional impact
- The ending/payoff when necessary

Keep the story under two minutes, approximately 75 to 110 seconds of voiceover.
Preserve a complete narrative arc with connected events, escalation, a turning point,
consequences, and a meaningful ending. Do not reduce it to a short incident or summary.

ORIGINAL STORY:
{story}

EVALUATION:
{evaluation}

Return ONLY the improved story.
Do not explain what you changed.
Do not include scores or commentary.
"""

        response = self.client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )

        return response.output_text