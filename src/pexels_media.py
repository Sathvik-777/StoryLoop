import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class PexelsMediaGetter:
    API_URL = "https://api.pexels.com/v1/search"

    def __init__(self, api_key=None):
        api_key = api_key or os.getenv("PEXELS_API_KEY")

        if not isinstance(api_key, str) or not api_key:
            raise ValueError("PEXELS_API_KEY is required")

        self.api_key = api_key

    def search_images(self, query, per_page=5):
        parameters = urlencode(
            {
                "query": query,
                "per_page": per_page,
                "orientation": "portrait",
            }
        )

        request = Request(
            f"{self.API_URL}?{parameters}",
            headers={
                "Authorization": self.api_key,
                "Accept": "application/json",
                "User-Agent": "StoryLoop/0.1",
            },
        )

        with urlopen(request, timeout=30) as response:
            data = json.load(response)

        return [
            {
                "id": photo["id"],
                "width": photo["width"],
                "height": photo["height"],
                "photographer": photo["photographer"],
                "alt": photo.get("alt"),
                "url": photo["url"],
                "image_url": photo["src"]["large2x"],
                "thumbnail_url": photo["src"]["medium"],
            }
            for photo in data.get("photos", [])
        ]

    def get_images_for_scene(self, scene, per_page=5):
        results = []

        for query in scene["search_queries"]:
            images = self.search_images(query, per_page)
            results.extend(images)

        unique_images = {}
        for image in results:
            unique_images[image["id"]] = image

        return {
            "scene_number": scene["scene_number"],
            "queries": scene["search_queries"],
            "images": list(unique_images.values()),
        }
