import json

from openai import OpenAI


class ContentStrategist:
    def __init__(self, client: OpenAI):
        self.client = client

    def create_strategy(self, research: dict) -> dict:
        prompt = f"""
You are a content strategist for a short-form storytelling channel.

Use ONLY the YouTube research data below as evidence. Select the single
video that provides the most useful creative direction, then create an
original story strategy inspired by its observable patterns. Do not copy
its title, plot, wording, or characters.

YOUTUBE RESEARCH:
{json.dumps(research, indent=2)}

Return ONLY valid JSON in this format:
{{
  "source_video_id": "string",
  "genre": "string",
  "theme": "string",
  "tone": "string",
  "format": "string",
  "duration_seconds": 45,
  "reason": "string",
  "creative_constraints": ["string"],
  "story_concept": "string"
}}
"""
        response = self.client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        raw_output = response.output_text.strip()
        raw_output = raw_output.removeprefix("```json")
        raw_output = raw_output.removesuffix("```")
        return json.loads(raw_output.strip())
