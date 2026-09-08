import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import urlopen


class YouTubeResearcher:
    """Collect recent, short YouTube videos ranked by public view count."""

    API_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY is required")

    def research(self, query: str = "short form storytelling") -> dict:
        published_after = datetime.now(timezone.utc) - timedelta(days=30)
        search_data = self._request(
            "search",
            {
                "part": "snippet",
                "type": "video",
                "order": "viewCount",
                "maxResults": 50,
                "q": query,
                "publishedAfter": published_after.isoformat().replace("+00:00", "Z"),
            },
        )

        video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]
        if not video_ids:
            return {"query": query, "videos": [], "retrieved_at": self._now()}

        videos_data = self._request(
            "videos",
            {
                "part": "snippet,contentDetails,statistics",
                "id": ",".join(video_ids),
            },
        )

        videos = []
        for item in videos_data.get("items", []):
            duration_seconds = self._parse_duration(item["contentDetails"]["duration"])
            if duration_seconds >= 120:
                continue

            statistics = item.get("statistics", {})
            view_count = int(statistics.get("viewCount", 0))
            published_at = item["snippet"]["publishedAt"]
            age_days = max(
                (
                    datetime.now(timezone.utc) - self._parse_datetime(published_at)
                ).total_seconds()
                / 86400,
                1,
            )
            like_count = statistics.get("likeCount")

            videos.append(
                {
                    "video_id": item["id"],
                    "channel_id": item["snippet"]["channelId"],
                    "channel_title": item["snippet"]["channelTitle"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"].get("description", ""),
                    "published_at": published_at,
                    "duration_seconds": duration_seconds,
                    "view_count": view_count,
                    "like_count": int(like_count) if like_count is not None else None,
                    "comment_count": (
                        int(statistics["commentCount"])
                        if "commentCount" in statistics
                        else None
                    ),
                    "age_days": round(age_days, 2),
                    "views_per_day": round(view_count / age_days, 2),
                    "like_view_ratio": (
                        round(int(like_count) / view_count, 4)
                        if like_count is not None and view_count
                        else None
                    ),
                    "is_short_candidate": True,
                }
            )

        videos.sort(key=lambda video: video["view_count"], reverse=True)
        return {
            "query": query,
            "retrieved_at": self._now(),
            "published_after": published_after.isoformat(),
            "duration_limit_seconds": 120,
            "videos": videos[:10],
        }

    def _request(self, resource: str, parameters: dict) -> dict:
        parameters["key"] = self.api_key
        url = f"{self.API_URL}/{resource}?{urlencode(parameters)}"
        with urlopen(url, timeout=30) as response:
            return json.load(response)

    @staticmethod
    def _parse_duration(value: str) -> int:
        hours = minutes = seconds = 0
        number = ""
        for character in value[2:]:
            if character.isdigit():
                number += character
                continue
            if character == "H":
                hours = int(number)
            elif character == "M":
                minutes = int(number)
            elif character == "S":
                seconds = int(number)
            number = ""
        return hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
