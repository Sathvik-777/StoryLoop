import json
from typing import cast

from openai import OpenAI
from openai.types.responses import ResponseInputParam


class MediaSelector:
    def __init__(self, client: OpenAI, model="gpt-4.1-mini"):
        self.client = client
        self.model = model

    def select_scene_image(self, scene: dict, ranked_images: list[dict]) -> dict:
        candidates = ranked_images[:3]
        if not candidates:
            return {
                "scene_number": scene["scene_number"],
                "selected_image": None,
                "reason": "No image candidates were available.",
            }

        prompt = f"""
Select the single best stock image for this StoryLoop scene.

Use the scene requirements and the candidate metadata. Inspect the supplied
candidate images. Choose only one candidate from the provided list. Do not
invent an image ID or URL. CLIP has already shortlisted these candidates, so
make the final decision using story context and visual fit.

SCENE:
{json.dumps(scene, indent=2)}

CANDIDATES:
{json.dumps([
    {
        "id": image["id"],
        "rank": image["rank"],
        "clip_score": image["clip_score"],
        "photographer": image.get("photographer"),
        "alt": image.get("alt"),
        "image_url": image["image_url"],
    }
    for image in candidates
], indent=2)}

Return ONLY valid JSON in this format:
{{
  "selected_image_id": 0,
  "reason": "short explanation of why this candidate best fits the scene"
}}
"""

        content = [{"type": "input_text", "text": prompt}]
        for image in candidates:
            content.append(
                {
                    "type": "input_text",
                    "text": f"Candidate image ID: {image['id']}",
                }
            )
            content.append(
                {
                    "type": "input_image",
                    "image_url": image["image_url"],
                }
            )

        response = self.client.responses.create(
            model=self.model,
            input=cast(
                ResponseInputParam,
                [{"role": "user", "content": content}],
            ),
        )
        result = self._parse_json(response.output_text)
        selected_id = result.get("selected_image_id")
        selected_image = next(
            (image for image in candidates if image["id"] == selected_id),
            None,
        )

        if selected_image is None:
            raise ValueError(
                f"LLM selected invalid image ID for scene {scene['scene_number']}"
            )

        return {
            "scene_number": scene["scene_number"],
            "selected_image": selected_image,
            "reason": result.get("reason", ""),
        }

    @staticmethod
    def _parse_json(raw_output: str) -> dict:
        cleaned_output = raw_output.strip()
        cleaned_output = cleaned_output.removeprefix("```json")
        cleaned_output = cleaned_output.removesuffix("```")
        return json.loads(cleaned_output.strip())
