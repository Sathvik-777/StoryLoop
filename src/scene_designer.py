import json

from openai import OpenAI


class SceneDesigner:
    def __init__(self, client: OpenAI):
        self.client = client

    def design_scenes(self, story: str) -> dict:
        prompt = f"""
You are a visual scene designer for a short-form narrated story.

Convert the story below into a sequence of visual scene requirements for
Pexels stock images or stock video. Design scenes that can realistically be
found through ordinary Pexels searches. Prefer concrete subjects, actions,
places, and emotions over abstract ideas, symbolism, or impossible events.

Rules:
- Cover the full story in chronological order.
- Create 4 to 8 scenes.
- Each scene should represent one clear visual beat.
- Keep the same characters and setting consistent where possible.
- Do not require custom illustration, animation, celebrity likenesses, or
  specific copyrighted characters.
- Search queries should be short, concrete English phrases suitable for Pexels.
- Include fallback queries using simpler or broader visual terms.
- Describe what the viewer should see, not narration or camera directions.

STORY:
{story}

Return ONLY valid JSON in this format:
{{
  "visual_style": "realistic stock footage",
  "media_preference": "video",
  "scenes": [
    {{
      "scene_number": 1,
      "story_beat": "string",
      "visual_requirement": "string",
      "subject": "string",
      "action": "string",
      "environment": "string",
      "mood": "string",
      "shot_type": "string",
      "media_type": "video",
      "search_queries": ["string", "string"],
      "fallback_queries": ["string", "string"],
      "stock_feasibility": "high"
    }}
  ]
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
