import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from story_evaluator import StoryEvaluator
from story_generator import StoryGenerator
from story_rewriter import StoryRewriter


def response(text):
    return SimpleNamespace(output_text=text)


def evaluation_payload(**overrides):
    scores = {
        "hook": 8,
        "story_quality": 8,
        "pacing": 8,
        "suspense": 7,
        "payoff": 8,
        "originality": 8,
        "voiceover_suitability": 8,
        "narrative_completeness": 8,
        "clarity": 8,
        "introduction_context": 8,
        "development": 8,
        "genre_fit": 8,
        "narrative_distinctiveness": 8,
        "causal_logic": 8,
        "narrative_engine_fit": 8,
        "overall_score": 8,
    }
    scores.update(overrides)
    return scores


class StoryPromptContractTests(TestCase):
    def test_generator_prompt_uses_approved_story_priorities(self):
        client = Mock()
        client.responses.create.return_value = response("A clear story.")

        generator = StoryGenerator(client)
        generator.generate_story(
            genre="science fiction",
            narrative_engine="a machine rejects its operator's order",
            ending_style="an unresolved ethical choice",
        )

        prompt = client.responses.create.call_args.kwargs["input"]
        self.assertIn("simple, familiar English", prompt)
        self.assertIn("Build the events around the assigned narrative engine", prompt)
        self.assertIn("The length", prompt)
        self.assertIn("flexible", prompt)
        self.assertIn("Do not add twists merely to surprise", prompt)
        self.assertIn("Science fiction: make the speculative idea matter", prompt)

    def test_evaluator_checks_causality_and_engine_without_hard_word_gate(self):
        client = Mock()
        client.responses.create.return_value = response(json.dumps(evaluation_payload()))
        evaluator = StoryEvaluator(client)

        result = evaluator.evaluate_story("A short story with few words.", {
            "genre": "mystery", "narrative_engine": "an apparent contradiction",
        })

        prompt = client.responses.create.call_args.kwargs["input"]
        self.assertIn("causal_logic", prompt)
        self.assertIn("narrative_engine_fit", prompt)
        self.assertIn("first hearing", prompt)
        self.assertEqual(result["verdict"], "PASS")

    def test_evaluator_passes_story_with_moderate_originality_scores(self):
        client = Mock()
        client.responses.create.return_value = response(json.dumps(evaluation_payload(
            hook=8,
            payoff=7,
            pacing=7,
            originality=6,
            narrative_distinctiveness=6,
            overall_score=7.3,
        )))

        result = StoryEvaluator(client).evaluate_story("A story that clears the new gates.")

        self.assertEqual(result["verdict"], "PASS")

    def test_evaluator_passes_the_recent_6_7_score_profile(self):
        client = Mock()
        client.responses.create.return_value = response(json.dumps(evaluation_payload(
            hook=7,
            story_quality=6,
            pacing=6,
            payoff=7,
            originality=5,
            voiceover_suitability=8,
            narrative_completeness=6,
            clarity=8,
            introduction_context=7,
            development=6,
            causal_logic=7,
            narrative_engine_fit=7,
            genre_fit=7,
            narrative_distinctiveness=5,
            overall_score=6.7,
        )))

        result = StoryEvaluator(client).evaluate_story("A short horror story.")

        self.assertEqual(result["verdict"], "PASS")

    def test_rewriter_prioritizes_diagnosis_and_simple_english(self):
        client = Mock()
        client.responses.create.return_value = response("A revised story.")
        rewriter = StoryRewriter(client)
        rewriter.rewrite_story(
            "Original story.",
            {
                "diagnosis": [{"issue": "unclear cause", "evidence": "The door opens."}],
                "revision_plan": ["Show who opened the door."],
                "preserve": ["the tense setting"],
            },
            metadata={"genre": "horror"},
        )

        prompt = client.responses.create.call_args.kwargs["input"]
        self.assertIn("Fix the highest-severity evidence-backed defect first", prompt)
        self.assertIn("simple, familiar English", prompt)
        self.assertIn("Do not automatically introduce", prompt)
        self.assertIn("twist", prompt)

    def test_acceptance_does_not_force_word_count_over_quality_judgment(self):
        client = Mock()
        client.responses.create.return_value = response(json.dumps({"winner": "B"}))
        rewriter = StoryRewriter(client)

        decision = rewriter.choose_better("Original.", "A much shorter revision.")

        self.assertEqual(decision["winner"], "B")
        self.assertEqual(decision["selected_story"], "A much shorter revision.")
