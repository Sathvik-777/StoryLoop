from openai import OpenAI


class StoryGenerator:
    def __init__(self, client: OpenAI):
        self.client = client

    def generate_story(self, strategy: dict):
        genre = strategy["genre"]
        theme = strategy["theme"]
        duration_seconds = strategy["duration_seconds"]
        tone = strategy["tone"]
        format_name = strategy["format"]
        story_concept = strategy["story_concept"]
        creative_constraints = strategy["creative_constraints"]
        prompt = f"""
Create a short-form narrated story for social media.

Requirements:
- Genre: {genre}
- Theme: {theme}
- Target duration: approximately {duration_seconds} seconds
- Tone: {tone}
- Format: {format_name}
- Story concept: {story_concept}
- Creative constraints: {creative_constraints}
- Strong hook within the first 3 seconds
- Clear and easy-to-follow narrative
- Build curiosity and tension
- Deliver a satisfying payoff or twist
- No unnecessary exposition
- Suitable for voiceover
- Do not include camera directions or visual instructions
- Write only the story

The story should feel original and emotionally engaging.
"""

        response = self.client.responses.create(model="gpt-4.1-mini", input=prompt)

        return response.output_text
