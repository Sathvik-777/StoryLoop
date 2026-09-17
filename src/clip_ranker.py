from io import BytesIO
from urllib.request import Request, urlopen

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


class ClipRanker:
    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = CLIPProcessor.from_pretrained(model_name,use_fast=True)
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def rank_scene_images(self, scene, images):
        if not images:
            return {
                "scene_number": scene["scene_number"],
                "ranked_images": [],
            }

        scene_text = self._scene_text(scene)
        text_inputs = self.processor(
            text=[scene_text],
            return_tensors="pt",
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            text_features = self.model.get_text_features(**text_inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        ranked_images = []
        for image in images:
            image_data = self._load_image(image["image_url"])
            image_inputs = self.processor(
                images=image_data,
                return_tensors="pt",
            ).to(self.device)

            with torch.no_grad():
                image_features = self.model.get_image_features(**image_inputs)
                image_features = image_features / image_features.norm(
                    dim=-1, keepdim=True
                )
                score = (text_features @ image_features.T).item()

            ranked_images.append(
                {
                    **image,
                    "clip_score": round(score, 4),
                }
            )

        ranked_images.sort(key=lambda item: item["clip_score"], reverse=True)
        for rank, image in enumerate(ranked_images, start=1):
            image["rank"] = rank

        return {
            "scene_number": scene["scene_number"],
            "scene_text": scene_text,
            "ranked_images": ranked_images,
        }

    @staticmethod
    def _scene_text(scene):
        return ", ".join(
            value
            for value in (
                scene.get("visual_requirement"),
                scene.get("subject"),
                scene.get("action"),
                scene.get("environment"),
                scene.get("mood"),
            )
            if value
        )

    @staticmethod
    def _load_image(image_url):
        request = Request(
            image_url,
            headers={"User-Agent": "StoryLoop/0.1"},
        )
        with urlopen(request, timeout=30) as response:
            return Image.open(BytesIO(response.read())).convert("RGB")
