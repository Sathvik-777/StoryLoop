import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audio_narrator import NarrationEngine
from video_assembler import VideoAssembler
from video_pipeline import StoryVideoPipeline


def test_story_segments_are_split_into_scene_chunks():
    story = "First sentence is long enough. Second sentence is also meaningful. Third sentence closes it."
    segments = NarrationEngine._split_story_into_segments(story, 3)

    assert len(segments) == 3
    assert all(segment.strip() for segment in segments)
    assert "First sentence" in segments[0]


def test_concat_plan_is_created_for_multiple_clips():
    assembler = VideoAssembler(output_dir=Path("/tmp/storyloop-test"))
    clip_paths = [Path("/tmp/clip_1.mp4"), Path("/tmp/clip_2.mp4")]

    concat_path = assembler._build_concat_file(clip_paths)

    contents = concat_path.read_text(encoding="utf-8")
    assert concat_path.exists()
    assert "/tmp/clip_1.mp4" in contents
    assert "/tmp/clip_2.mp4" in contents


def test_audio_duration_is_reasonable_for_short_story_segments():
    text = " ".join(["word"] * 120)
    duration = NarrationEngine._estimate_duration_seconds(text)

    assert 1.0 <= duration <= 20.0


def test_image_download_uses_browser_headers():
    cache_dir = Path("/tmp/storyloop-image-cache")
    if cache_dir.exists():
        for file in cache_dir.iterdir():
            file.unlink()

    mock_response = Mock()
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)
    mock_response.read.return_value = b"fake-image-bytes"

    with patch("video_pipeline.urlopen") as mock_urlopen:
        mock_urlopen.return_value = mock_response

        output_path = StoryVideoPipeline._download_image_to_local(
            "https://example.com/image.jpg",
            cache_dir=cache_dir,
            scene_number=3,
        )

    assert output_path.endswith("scene_3_selected_image.jpg")
    assert Path(output_path).read_bytes() == b"fake-image-bytes"
    request_obj = mock_urlopen.call_args.args[0]
    assert request_obj.headers.get("User-agent")


def test_render_cache_is_cleared_before_new_run(tmp_path):
    target_dir = tmp_path / "rendered"
    images_dir = target_dir / "images"
    audio_dir = target_dir / "audio"
    images_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    stale_image = images_dir / "scene_1_selected_image.jpg"
    stale_audio = audio_dir / "scene_1_narration.wav"
    stale_video = target_dir / "scene_1.mp4"
    stale_image.write_bytes(b"old")
    stale_audio.write_bytes(b"old")
    stale_video.write_bytes(b"old")

    pipeline = StoryVideoPipeline(output_dir=target_dir)
    pipeline._reset_render_cache(target_dir)

    assert not stale_image.exists()
    assert not stale_audio.exists()
    assert not stale_video.exists()
