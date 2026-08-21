from openai import OpenAI
import json


class StoryEvaluator:
    def __init__(self, client: OpenAI):
        self.client = client

    def evaluate_story(self, story: str):

        prompt = f"""
You are a strict editor evaluating a short-form social media story.

Evaluate the following story for a target video length of approximately 45 seconds.

STORY:
{story}

Score each category from 0 to 10:

1. hook
2. story_quality
3. pacing
4. suspense
5. payoff
6. originality
7. voiceover_suitability

Then calculate an overall_score from 0 to 10.

A story should PASS only if:
- overall_score >= 7.5
- hook >= 7.5
- payoff >= 7.5
- pacing >= 6.5

Also provide:
- verdict: "PASS" or "REWRITE"
- strengths: 2-3 short points
- weaknesses: 2-3 short points
- improvement: one concise recommendation

Return ONLY valid JSON in this format:

{{
    "hook": 0,
    "story_quality": 0,
    "pacing": 0,
    "suspense": 0,
    "payoff": 0,
    "originality": 0,
    "voiceover_suitability": 0,
    "overall_score": 0,
    "verdict": "PASS",
    "strengths": [],
    "weaknesses": [],
    "improvement": ""
}}
"""

        response = self.client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )


        raw_output = response.output_text.strip()

        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]

        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]

        return json.loads(raw_output.strip())
        