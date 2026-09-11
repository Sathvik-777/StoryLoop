# StoryLoop — LLM Project Handoff Prompt

Copy everything below into another LLM when asking it to work on this repository.

---

You are working on **StoryLoop**, an early-stage Python 3.11 project that aims to become an autonomous pipeline for researching, generating, evaluating, improving, illustrating, publishing, and eventually learning from short-form social-media stories.

## Your working rules

- Treat the repository contents as the source of truth; inspect relevant files before proposing or making changes.
- Preserve existing behavior and the user's uncommitted work. Never discard or overwrite unrelated changes.
- Never reveal, print, commit, or hard-code secrets from `.env`.
- Keep components small and modular, following the existing class-per-stage design.
- Prefer focused changes over a broad rewrite. Explain assumptions when requirements are ambiguous.
- After changes, run proportionate formatting, linting, and tests. The project currently has no automated test suite, so add targeted tests when appropriate and clearly state what could not be verified because external APIs, model downloads, or credentials are required.
- When changing a dictionary/JSON contract, trace and update every producer and consumer.

## Product intent

StoryLoop is intended to automate this lifecycle:

1. Research recent successful short YouTube videos.
2. Derive an original creative strategy from observable patterns without copying a source.
3. Generate a short narrated story.
4. Evaluate it and iteratively rewrite it until it meets quality thresholds.
5. Break an accepted story into stock-media-friendly visual scenes.
6. Retrieve portrait stock images for each scene.
7. Rank candidates by semantic image/text similarity.
8. Make a final context-aware choice for each scene.
9. Save revision history as memory and the accepted story as a published artifact.
10. Future goals include similarity detection, audio/video assembly, automatic social publishing, analytics, and a performance feedback loop.

The project is currently a sequential proof of concept, not a production service or packaged application.

## Current end-to-end flow

`src/init.py` is the orchestration script. On import/execution it:

1. Loads `.env` with `python-dotenv` and creates an OpenAI client.
2. Instantiates all pipeline components, including the heavyweight Hugging Face CLIP model.
3. Calls `YouTubeResearcher.research()` using `YOUTUBE_SEARCH_QUERY` or the default `"short form storytelling"`.
4. Sends research to `ContentStrategist.create_strategy()`.
5. Sends the strategy to `StoryGenerator.generate_story()`.
6. Evaluates the story with `StoryEvaluator.evaluate_story()`.
7. Accepts a story only when `overall_score >= 7`, `hook >= 7`, `payoff >= 7`, and `pacing >= 6`.
8. If it fails, calls `StoryRewriter.rewrite_story()` and retries, allowing at most three rewrites (four evaluated versions total).
9. For an accepted story, calls `SceneDesigner.design_scenes()` to create 4–8 visual beats.
10. Uses `PexelsMediaGetter.get_images_for_scene()` for every scene/search query.
11. Uses `ClipRanker.rank_scene_images()` to score downloaded images against combined scene text.
12. In the current uncommitted work, uses `MediaSelector.select_scene_image()` to show the top three candidates to a multimodal OpenAI model and select one valid candidate ID.
13. Calls `save_story_record()` to write the revision record and final accepted story.

If the story never passes, no scene/media work or publishing occurs.

## Module map and contracts

- `src/init.py`: procedural composition root and quality gate. It currently has no `main()` guard, CLI, dependency injection, or centralized error handling.
- `src/youtube_researcher.py`: calls YouTube Data API v3. It searches the last 30 days, requests up to 50 results ordered by view count, discards videos at least 120 seconds long, calculates age/views-per-day/like ratio, sorts by raw views, and returns the top 10.
- `src/content_strategist.py`: asks `gpt-4.1-mini` to select one researched source and return JSON containing `source_video_id`, `genre`, `theme`, `tone`, `format`, `duration_seconds`, `reason`, `creative_constraints`, and `story_concept`.
- `src/story_generator.py`: consumes that strategy dictionary and returns story text from `gpt-4.1-mini`.
- `src/story_evaluator.py`: returns JSON scores for hook, quality, pacing, suspense, payoff, originality, voiceover suitability, and overall score, plus verdict, strengths, weaknesses, and improvement advice.
- `src/story_rewriter.py`: preserves the premise, characters, strongest material, genre, and tone while revising according to the evaluation.
- `src/scene_designer.py`: returns JSON with `visual_style`, `media_preference`, and `scenes`. Each scene includes its number, story beat, visual requirement, subject, action, environment, mood, shot type, media type, primary and fallback queries, and stock feasibility.
- `src/pexels_media.py`: queries Pexels image search with portrait orientation and normalizes image metadata. It searches `search_queries`; currently `fallback_queries` are generated but not used.
- `src/clip_ranker.py`: loads `openai/clip-vit-base-patch32`, downloads each candidate URL, builds scene text from visual requirement/subject/action/environment/mood, computes normalized cosine-like CLIP scores, and assigns ranks.
- `src/media_selector.py`: **untracked work in progress**. It sends the top three ranked candidates and actual images to `gpt-4.1-mini`, validates the returned ID, and returns the chosen image and reason.
- `src/story_storage.py`: writes timestamped plain-text files. `memory/` contains all evaluated versions and feedback; `output/published/` contains only the accepted story. Media plans and research/strategy provenance are not persisted yet.

## Runtime and configuration

Dependencies are declared in `requirements.txt`: OpenAI Python SDK, python-dotenv, PyTorch, Transformers, Pillow, Black, and Ruff. The dev container uses Python 3.11 and installs that file automatically.

Required environment variables:

- `OPENAI_API_KEY`
- `YOUTUBE_API_KEY`
- `PEXELS_API_KEY`

Optional environment variable:

- `YOUTUBE_SEARCH_QUERY`

Do not read or reproduce their values. `.env` is gitignored.

The simplest current invocation is from the repository root with `python src/init.py`. It requires network access and valid credentials, can incur OpenAI/YouTube/Pexels usage, and may download a large CLIP model on first run. CPU is supported but slower; CUDA is selected automatically when available.

## Persistence and generated artifacts

- `memory/story_<timestamp>.txt`: accepted run's full revision/evaluation history plus final story.
- `output/published/story_<timestamp>.txt`: final accepted story only.
- One representative memory/published pair from 2026-08-21 is committed.
- Several 2026-09-08 story artifacts are currently untracked generated files. Do not assume they are source code or delete/add them without confirming the intended artifact policy.

## Git evolution and current worktree state

The `main` branch currently ends at `1d82633` and has five commits:

1. `c859d9b` — initial README and Python `.gitignore`.
2. `a25cd28` — expanded the vision and roadmap in README.
3. `a378375` — introduced OpenAI story generation and evaluation.
4. `160b568` — added iterative rewriting, the pass gate, persistent memory, publishing storage, and one example output.
5. `1d82633` — added the YouTube research → strategy → scene design → Pexels retrieval → CLIP ranking pipeline, dependencies, and dev-container setup.

Current uncommitted changes must be preserved:

- Modified `src/init.py`: imports/instantiates `MediaSelector` and runs final selection after CLIP ranking.
- Untracked `src/media_selector.py`: multimodal final selection implementation.
- Untracked generated files under `memory/` and `output/published/` dated 2026-09-08.

Always run `git status --short` and inspect the relevant diff before editing.

## Known limitations and likely engineering priorities

- No automated tests, CI, packaging metadata, CLI, or application entry-point guard.
- README architecture/status/roadmap lag behind the implementation.
- LLM JSON handling strips only simple Markdown fences and otherwise trusts schema/types; malformed or semantically invalid outputs can crash the run.
- API and image-download calls have limited resilience: no retries, backoff, caching, rate-limit handling, or per-scene failure isolation.
- Constructors and top-level orchestration eagerly require credentials and load CLIP, which makes imports, tests, and partial execution difficult.
- Research ranks primarily by raw view count even though richer performance metrics are calculated.
- YouTube evidence is metadata only; the system does not retrieve transcripts or analyze actual video content.
- Pexels searches primary queries only, despite the scene designer producing fallback queries.
- CLIP processes images one at a time and one failed download can abort the pipeline.
- The scene plan requests stock images or video and declares video preference, but the implemented retrieval/ranking path handles images only.
- Final media selection exists only in uncommitted work and is not persisted or used to assemble a video.
- Story memory is archival text; it is not yet used for semantic similarity, retrieval, or learning.
- Quality control relies on the same model family for generation, evaluation, rewriting, strategy, scene design, and final selection.
- There is no cost accounting, observability, structured logging, reproducibility metadata, or run manifest.
- Timestamp filenames have one-second resolution and naive local time, so collisions are possible.

## Architecture expectations for future work

Unless the user's task says otherwise:

- Retain the stage boundaries and explicit dictionary contracts.
- Move toward a callable `main()`/pipeline object with injected clients so modules can be imported and tested without external side effects.
- Validate structured model outputs and external API responses at boundaries.
- Make partial failures visible and recoverable rather than silently publishing incomplete work.
- Preserve creative originality: research should inform strategy, not copy titles, plots, wording, or characters.
- Treat generated output, cached/downloaded media, and committed fixtures as separate categories with an explicit repository policy.
- Do not claim roadmap items are complete merely because a small proof-of-concept piece exists.

## How to respond to the next task

First summarize your understanding of the requested change and identify the files/contracts it affects. Inspect those files and the current Git diff. Then implement or advise narrowly within scope. In your handoff, state what changed, how it was verified, remaining risks, and any external-service verification that was not run.

The user's next request is:

> [REPLACE THIS WITH THE SPECIFIC TASK]

---
