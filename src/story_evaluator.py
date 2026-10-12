from openai import OpenAI
import json


class StoryEvaluator:
    def __init__(self, client: OpenAI):
        self.client = client
        self.api_calls = 0

    def evaluate_story(
        self,
        story: str,
        metadata: dict | None = None,
        previous_stories: list[str] | None = None,
    ) -> dict:
        metadata = metadata or {}
        previous_stories = previous_stories or []

        metadata_text = json.dumps(metadata, ensure_ascii=False)
        previous_text = "\n\n".join(
            f"PREVIOUS STORY {i + 1}:\n{previous_story}"
            for i, previous_story in enumerate(previous_stories)
        )

        if not previous_text:
            previous_text = "No previous stories supplied."

        prompt = f"""
You are a strict but genre-aware editor evaluating a short-form narrated story.

Evaluate the story on its own merits. Do not reward basic structural
compliance as if it were evidence of originality.

GENERATION METADATA
{metadata_text}

CURRENT STORY
{story}

PREVIOUS STORIES FOR COMPARISON
{previous_text}

Score every category from 0 to 10:

1. hook
   How effectively does the opening engage the audience?

2. story_quality
   How compelling, coherent, and well-executed is the story?

3. pacing
   Does the story give the setup, development, and ending enough room to land,
   or does it rush through important changes and consequences?

4. suspense
   How well does it sustain curiosity, tension, anticipation, or another
   appropriate form of engagement? Judge according to the genre.
   A comedy or romance does not need conventional suspense.

5. payoff
   How satisfying, appropriate, or impactful is the ending for this story?
   A deliberately ambiguous ending can score highly if it works.

6. originality
   How distinctive is the premise and execution compared with familiar
   short-form story clichés?

7. voiceover_suitability
   Is the story clear, natural, and engaging when narrated aloud? Is the English
   simple and familiar, without ornate or needlessly difficult wording?

11. clarity
    Can a listener follow who is involved, what is happening, and why? Are
    sentences and transitions easy to understand on first hearing?

12. introduction_context
    Does the opening quickly orient us to the relevant character(s), situation,
    and a concrete reason to keep listening, without relying on unexplained facts?

13. development
    Do connected events, choices, or discoveries develop the central situation
    enough to make the outcome feel earned rather than rushed?

14. causal_logic
    Can the listener understand why each important event follows from the last?
    Flag coincidences, unexplained changes, and outcomes without enough setup.

15. narrative_engine_fit
    Does the supplied narrative engine meaningfully drive the events and
    consequences? Do not reward a mere mention of it.

8. narrative_completeness
   How successfully does the story create a meaningful narrative experience?
   Do not require a conventional beginning-middle-ending structure if the
   chosen genre or form does not need one.

9. genre_fit
   How strongly does the story actually deliver its intended genre?
   If the metadata does not specify a genre, infer the apparent genre.
   Do not award a high score merely because the story mentions genre-related
   objects or settings.

10. narrative_distinctiveness
    How different is the story's underlying plot, conflict, progression,
    and outcome from the previous stories supplied?
    Compare narrative mechanics, not just names, settings, or wording.
    If no previous stories are supplied, evaluate whether the story avoids
    a highly generic, formulaic plot.

CRITICAL EVALUATION RULES

- A recognizable beginning, middle, and ending is not automatically a
  strength. Judge the quality of the actual experience.
- A clear protagonist goal is not mandatory for every genre or story.
- Do not require a moral, personal-growth arc, positive outcome, twist,
  or neat resolution.
- Do not reward a story simply because a protagonist overcomes adversity.
- Watch for repetitive patterns such as:
  setback → adaptation → convenient reward → inspirational lesson.
- Genre variety matters, but changing genre labels alone is not enough.
- A story can be competently written and still be generic or repetitive.
- Do not penalize a story for using an unconventional structure when it works.
- Treat unclear context, difficult/ornate wording, broken cause and effect,
  missing development, or an abrupt/unearned ending as real defects when they
  impede listener engagement.
- Strong poetic phrasing does not compensate for language that is hard to follow.
- Aim for 120–150 words, but treat this as flexible guidance rather than a
  pass/fail rule. Never recommend filler or cuts that damage clarity.

PASS REQUIREMENTS

Return "PASS" only if all conditions are met:
- overall_score >= 6.5
- hook >= 6
- payoff, pacing, originality, voiceover_suitability, genre_fit,
  narrative_distinctiveness, clarity, introduction_context, development,
  causal_logic, and narrative_engine_fit are each >= 5
- narrative_completeness >= 5

Calculate overall_score as a weighted judgment of the categories, not
a simple average that hides a major weakness. Genre fit, story quality,
originality, and payoff should carry particular weight.

GENRE-AWARE QUALITY PRIORITIES
- Horror: dread, vulnerability, atmosphere, disturbing implications.
- Romance: chemistry, relationship dynamics, emotional stakes.
- Comedy: comic construction, timing, escalation, payoff.
- Mystery: meaningful clues, coherence, and fair handling of uncertainty.
- Adventure: discovery, action, consequential choices, a compelling journey.
- Science fiction: a meaningful speculative premise and its consequences.
- Crime thriller: danger, leverage, investigation, conflicting interests.
- Tragedy: causal weight, emotional impact, and meaningful loss.
- Fantasy: meaningful use of extraordinary rules and consequences.
- Human drama: believable conflict, relationship dynamics, emotional truth.
These are priorities, not mandatory checklists. Do not treat twists or suspense
as universal requirements.

STRUCTURED DIAGNOSIS
For each real weakness, return issue, evidence from the story, impact, severity
("high", "medium", or "low"), and a concrete repair. Also return revision_plan
(a short prioritized list) and preserve (elements that already work).
Diagnosis may be empty if there is no meaningful defect. Do not invent flaws
just to justify rewriting. Fix the cause, not merely the wording.

Return:
- all numeric scores
- verdict: "PASS" or "REWRITE"
- apparent_genre: a concise genre label
- strengths: 2–3 short points
- weaknesses: 2–3 short points
- improvement: one concise, actionable recommendation
- dominant_pattern: the main plot mechanism in a short phrase
- repetition_risk: "low", "medium", or "high"

Return ONLY valid JSON with this structure:

{{
    "hook": 0,
    "story_quality": 0,
    "pacing": 0,
    "suspense": 0,
    "payoff": 0,
    "originality": 0,
    "voiceover_suitability": 0,
    "narrative_completeness": 0,
    "clarity": 0,
    "introduction_context": 0,
    "development": 0,
    "causal_logic": 0,
    "narrative_engine_fit": 0,
    "genre_fit": 0,
    "narrative_distinctiveness": 0,
    "overall_score": 0,
    "verdict": "REWRITE",
    "apparent_genre": "",
    "strengths": [],
    "weaknesses": [],
    "improvement": "",
    "dominant_pattern": "",
    "repetition_risk": "medium",
    "diagnosis": [],
    "revision_plan": [],
    "preserve": []
}}
"""

        response = self.client.responses.create(
            model="gpt-5-mini",
            input=prompt,
        )

        self.api_calls += 1
        raw_output = response.output_text.strip()

        if raw_output.startswith("```"):
            raw_output = raw_output.split("\n", 1)[1]
            if raw_output.endswith("```"):
                raw_output = raw_output[:-3]

        evaluation = json.loads(raw_output.strip())

        # Enforce the pass criteria in Python as well as in the prompt.
        required_scores = [
            "overall_score",
            "hook",
            "payoff",
            "pacing",
            "originality",
            "voiceover_suitability",
            "genre_fit",
            "narrative_distinctiveness",
            "narrative_completeness",
            "clarity",
            "introduction_context",
            "development",
            "causal_logic",
            "narrative_engine_fit",
        ]

        if any(key not in evaluation for key in required_scores):
            raise ValueError("Story evaluation is missing required score fields.")

        # Backward-compatible defaults: older evaluators only returned improvement/weaknesses.
        evaluation.setdefault("diagnosis", [])
        evaluation.setdefault("revision_plan", [evaluation.get("improvement", "")] if evaluation.get("improvement") else [])
        evaluation.setdefault("preserve", evaluation.get("strengths", []))

        evaluation["verdict"] = (
            "PASS"
            if (
                evaluation["overall_score"] >= 6.5
                and evaluation["hook"] >= 6
                and evaluation["payoff"] >= 5
                and evaluation["pacing"] >= 5
                and evaluation["originality"] >= 5
                and evaluation["voiceover_suitability"] >= 5
                and evaluation["genre_fit"] >= 5
                and evaluation["narrative_distinctiveness"] >= 5
                and evaluation["narrative_completeness"] >= 5
                and evaluation["clarity"] >= 5
                and evaluation["introduction_context"] >= 5
                and evaluation["development"] >= 5
                and evaluation["causal_logic"] >= 5
                and evaluation["narrative_engine_fit"] >= 5
            )
            else "REWRITE"
        )

        return evaluation
