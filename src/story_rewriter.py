from openai import OpenAI
import json


class StoryRewriter:
    def __init__(self, client: OpenAI):
        self.client = client
        self.api_calls = 0

    def rewrite_story(
        self,
        story: str,
        evaluation: dict,
        metadata: dict | None = None,
    ) -> str:
        metadata = metadata or {}

        metadata_text = json.dumps(metadata, ensure_ascii=False)
        evaluation_text = json.dumps(evaluation, ensure_ascii=False)
        diagnosis_text = json.dumps(evaluation.get("diagnosis", []), ensure_ascii=False)
        revision_plan_text = json.dumps(evaluation.get("revision_plan", []), ensure_ascii=False)
        preserve_text = json.dumps(evaluation.get("preserve", evaluation.get("strengths", [])), ensure_ascii=False)

        prompt = f"""
You are an expert short-form story editor.

Your task is to improve the supplied story based on its evaluation.

GENERATION METADATA
{metadata_text}

ORIGINAL STORY
{story}

EVALUATION
{evaluation_text}

STRUCTURED DIAGNOSIS (prioritize this over generic score optimization)
{diagnosis_text}

PRIORITIZED REVISION PLAN
{revision_plan_text}

ELEMENTS THAT ALREADY WORK AND MUST BE PRESERVED
{preserve_text}

PRIMARY OBJECTIVE

Improve the story's actual creative quality. Do not simply make it more
conventional, sentimental, or neatly structured.

PRESERVE
- The core premise when it is worth preserving.
- The intended genre and its characteristic audience experience.
- The strongest original details and character dynamics.
- An approximate 120–150 word voiceover length when it fits naturally. Do not
  add filler or damage a clear story to hit a number.

IMPROVE
- The specific weaknesses identified by the evaluator.
- Orient the listener in the first 1–2 sentences: establish who is present,
  the immediate situation, and a concrete detail that creates interest.
- Use simple, familiar English and natural spoken sentences. Replace ornate,
  poetic, abstract, or difficult wording with clear concrete language.
- Develop the central situation through connected moments, choices, or
  discoveries. Give important changes and consequences enough space; do not
  rush from introduction to climax or skip the cause of an outcome.
- Let the ending follow from the developed story and give its emotional or
  narrative payoff room to register.
- Repair weak cause and effect, implausible coincidences, or convenient
  outcomes only when the diagnosis identifies them.
- Repair a weak or unearned ending by improving its setup or consequence.
- Address generic or repetitive plotting only when the diagnosis gives
  evidence; preserve distinctive elements that already work.

GENRE PRESERVATION

A horror story should remain horror.
A romance should remain romance.
A tragedy should not be converted into an uplifting lesson.
A comedy should not become sentimental drama.
A mystery should not lose its central uncertainty without a meaningful payoff.

If the metadata specifies a genre or narrative engine, use it as guidance.
Do not force genre elements into the story unnaturally.

NO MANDATORY STORY TEMPLATE

Do not automatically introduce:
- A clearly stated goal.
- Multiple escalating obstacles.
- A dramatic twist.
- A personal-growth arc.
- A moral or inspirational message.
- A happy ending.
- A tidy resolution.

Use whichever narrative structure best serves this particular story.

ORIGINALITY

If the evaluation identifies a repetitive or generic plot, change the
underlying narrative mechanism rather than merely changing names, objects,
locations, or wording.

Avoid the familiar pattern:
setback → adaptation → convenient reward → inspirational lesson.

Do not add random events merely to make the story unpredictable.
New developments should fit the story's premise and create meaningful
consequences.

ENDING

Keep the ending direction if it works. Change it if the evaluation identifies
a weak payoff or if the ending feels forced.

The ending can be joyful, tragic, unsettling, ironic, ambiguous, comic,
or bittersweet. It does not need to teach the audience anything.

LENGTH AND FORMAT

- Aim for 120–150 words, suitable for approximately 45–60 seconds, when it
  fits naturally. Length is flexible; do not add filler.
- Remove filler rather than rushing through important moments.
- Use simple, familiar English and natural spoken language; avoid ornate or
  difficult phrasing that makes a listener work to understand the story.
- Return only the rewritten story.
- Do not include headings, scores, explanations, or commentary.

REPAIR THE CAUSE, NOT JUST THE SYMPTOM
- Fix the highest-severity evidence-backed defect first.
- If the premise itself is generic, change the premise/mechanism rather than polishing wording.
- If causality is weak, repair the sequence of causes and consequences.
- If character dynamics are weak, make wants, incompatibilities, and choices more specific.
- If the ending is unearned, repair its setup or consequence; do not automatically add a twist.
- Keep sentences concrete, natural, and easy to understand on first hearing.
- Do not blindly implement low-confidence or contradictory suggestions.
- If diagnosis is empty or does not identify a real defect, make only minimal edits.
Make the smallest changes necessary when the story already works. Make deeper changes
when its premise, progression, or ending is fundamentally weak.
"""

        response = self.client.responses.create(
            model="gpt-5-mini",
            input=prompt,
        )

        self.api_calls += 1
        return response.output_text.strip()

    def choose_better(self, original: str, revision: str, metadata: dict | None = None) -> dict:
        """Pairwise acceptance judge; keeps original unless revision is clearly better."""
        metadata = metadata or {}
        prompt = f"""
Compare two versions of the same intended short-form story. Judge both using the same
genre-aware criteria. Do not prefer a version just because it is more dramatic, longer,
more twist-heavy, or more polished on the surface. Check genre preservation, clarity,
a well-contextualized introduction, pacing and story development, causality, specificity,
originality, payoff, and whether the diagnosed defect is repaired. Favor simple,
natural English that is easy to follow.
Call them A and B; do not assume B is better because it is a revision.

DESIGN METADATA:
{json.dumps(metadata, ensure_ascii=False)}

VERSION A:
{original}

VERSION B:
{revision}

Return ONLY valid JSON:
{{
  "winner": "A or B",
  "reason": "brief evidence-based comparison",
  "defect_repaired": "yes, partly, no, or not applicable",
  "new_problems": [],
  "comparison": {{
    "genre_fit": "A, B, or tie",
    "causality": "A, B, or tie",
    "specificity": "A, B, or tie",
    "originality": "A, B, or tie",
    "ending": "A, B, or tie"
  }}
}}
A revision must materially improve the diagnosed weakness without adding a new
clarity, causal, genre-fit, or payoff problem. If it is not clearly better overall, choose A.
"""
        response = self.client.responses.create(model="gpt-5-mini", input=prompt)
        self.api_calls += 1
        raw = response.output_text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.rstrip().endswith("```"):
                raw = raw.rstrip()[:-3]
        start, end = raw.find("{"), raw.rfind("}")
        if start < 0 or end < start:
            raise ValueError("Acceptance judge returned invalid JSON.")
        decision = json.loads(raw[start:end + 1])
        winner = str(decision.get("winner", "A")).upper()
        if winner not in {"A", "B"}:
            winner = "A"
        decision["winner"] = winner
        decision["selected_story"] = original if decision["winner"] == "A" else revision
        return decision
