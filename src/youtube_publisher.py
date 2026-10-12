
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from api_cost_tracker import get_cost_tracker


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"

CLIENT_SECRET_FILE = (
    CREDENTIALS_DIR
    / "client_secret_1049505599115-tikb4p4nuonlvt5lgbni9tcs4t4r1s8k.apps.googleusercontent.com.json"
)

TOKEN_FILE = CREDENTIALS_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubePublisher:
    def __init__(self):
        self.youtube = self._authenticate()

    @staticmethod
    def _authenticate():
        if not CLIENT_SECRET_FILE.exists():
            raise FileNotFoundError(
                f"OAuth client JSON not found: {CLIENT_SECRET_FILE}"
            )

        credentials = None

        if TOKEN_FILE.exists():
            credentials = Credentials.from_authorized_user_file(
                str(TOKEN_FILE),
                SCOPES,
            )

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        if not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_FILE),
                SCOPES,
            )
            credentials = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

        return build("youtube", "v3", credentials=credentials)

    def upload_video(
        self,
        video_path: str | Path,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        category_id: str = "22",
        privacy_status: str = "public",
    ) -> dict:
        video_path = Path(video_path).resolve()

        if not video_path.is_file():
            raise FileNotFoundError(f"Video not found: {video_path}")

        if privacy_status not in {"private", "unlisted", "public"}:
            raise ValueError(
                "privacy_status must be private, unlisted, or public"
            )

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            chunksize=8 * 1024 * 1024,
            resumable=True,
        )

        request = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        get_cost_tracker().record_external_api(
            "YouTube Data API",
            "videos.insert",
            quota_units=1,
            note="No direct USD charge; 1 upload quota unit tracked",
        )
        response = None

        while response is None:
            _, response = request.next_chunk()
            if response:
                print("Upload completed. Processing response...")

        video_id = response["id"]

        return {
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": response["snippet"]["title"],
            "privacy_status": response["status"]["privacyStatus"],
        }
