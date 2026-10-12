# StoryLoop

An autonomous AI-powered content pipeline for generating,
evaluating, optimizing, and publishing short-form stories.

## Status

🚧 Early Development

## Vision

StoryLoop aims to build an autonomous content pipeline that can:

- Generate story ideas
- Generate short-form stories
- Evaluate story quality
- Detect semantic similarity with previously published content
- Generate supporting audio and visuals
- Optimize content for social media
- Publish content automatically
- Learn from performance feedback

## Tech Stack

Currently under development.

## Architecture

Coming soon.

## Roadmap

- [ ] Project foundation
- [ ] Story generation
- [ ] Story evaluation
- [ ] Semantic similarity detection
- [ ] Content generation pipeline
- [ ] Audio/visual generation
- [ ] Publishing automation
- [ ] Analytics feedback loop

## Running the pipeline

Run the pipeline from the project root with `python src/init.py`. YouTube upload is disabled by default. Set `Publish` to the JSON boolean `true` in `script_parameters.json` to upload a successfully rendered video (uploads use private visibility). Missing or invalid settings default to disabled. OAuth credentials are still required for an enabled upload.

## API usage and cost report

The full pipeline, replay runner, story batch runner, and YouTube upload script write API usage details to `output/current_run/api_cost_report.txt`. OpenAI text calls use token counts returned by the API. Speech input tokens are estimates based on text length, and the speech endpoint does not expose output-token usage, so speech output cost is excluded from the known-cost subtotal. Pexels calls and YouTube quota usage are listed separately; those APIs do not charge a direct per-request fee.

StoryLoop uses `gpt-5-mini` for its OpenAI text and image-selection calls. OpenAI rates in the report are per million tokens and follow the [OpenAI API pricing page](https://developers.openai.com/api/docs/models/gpt-5-mini): $0.25 per million input tokens, $0.025 per million cached input tokens, and $2.00 per million output tokens. The separate `gpt-4o-mini-tts` narration rates are $0.60 per million text input tokens and $12.00 per million audio output tokens. The USD-to-INR conversion defaults to ₹96.64 per USD (mid-market rate, 2026-10-11); override it with `STORYLOOP_USD_TO_INR` when needed. Set `STORYLOOP_FX_RATE_DATE` and `STORYLOOP_FX_RATE_SOURCE` alongside it to label a custom exchange rate. Pexels usage limits and free status are described in its [API documentation](https://www.pexels.com/api/documentation/). YouTube quota units follow the [YouTube Data API quota documentation](https://developers.google.com/youtube/v3/determine_quota_cost).
