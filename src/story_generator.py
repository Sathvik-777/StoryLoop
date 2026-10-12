
import random

from openai import OpenAI


class StoryGenerator:
    STORY_DESIGNS = {
        "horror": {
            "engines": [
                "a familiar place develops an impossible rule",
                "a character realizes a threat has been present all along",
                "survival against a threat that cannot be fought directly",
                "a disturbing discovery changes the meaning of ordinary events",
                "a character must decide whether to trust an unreliable perception",
                "an attempt to escape makes the danger worse",
            ],
            "endings": [
                "an unsettling revelation",
                "survival with a disturbing cost",
                "an ambiguous and lingering dread",
                "a failed escape",
                "a quiet final detail that changes the audience's interpretation",
            ],
        },
        "adventure": {
            "engines": [
                "exploration of an unfamiliar and dangerous place",
                "a rescue attempt complicated by unexpected terrain",
                "a race against a natural or physical threat",
                "a journey where the destination differs from expectations",
                "rival explorers forced to cooperate",
                "a discovery that creates a difficult practical choice",
            ],
            "endings": [
                "a hard-won discovery",
                "an unsuccessful expedition with meaningful consequences",
                "a narrow escape",
                "a discovery that changes the original objective",
                "a victory that comes at a cost",
            ],
        },
        "romance": {
            "engines": [
                "two people misinterpret each other's intentions",
                "attraction complicated by incompatible life choices",
                "a relationship tested by an unexpected opportunity",
                "two strangers form a connection under unusual circumstances",
                "a reunion where neither person is who the other remembers",
                "a small act creates an emotional misunderstanding",
            ],
            "endings": [
                "a relationship beginning",
                "a quiet separation",
                "a missed opportunity",
                "a reconciliation with unresolved differences",
                "an unexpected but believable emotional realization",
            ],
        },
        "science fiction": {
            "engines": [
                "a technology behaves differently from its intended design",
                "a scientific discovery creates an ethical dilemma",
                "a mission encounters evidence that challenges accepted reality",
                "a machine and its operator disagree about a decision",
                "a survival problem in an unfamiliar environment",
                "a technological convenience produces an unforeseen consequence",
            ],
            "endings": [
                "a scientific revelation",
                "a costly solution",
                "an ironic consequence of the technology",
                "an unresolved ethical choice",
                "a discovery that changes the mission",
            ],
        },
        "mystery": {
            "engines": [
                "an apparent contradiction must be explained",
                "several witnesses give incompatible accounts",
                "a missing item reveals a hidden relationship",
                "an ordinary event contains one inexplicable detail",
                "an investigation undermines the investigator's assumptions",
                "a character reconstructs what happened from incomplete evidence",
            ],
            "endings": [
                "a coherent explanation",
                "a partial answer that leaves one important question open",
                "a solution with uncomfortable implications",
                "the discovery that the original question was wrong",
                "an unresolved mystery with meaningful evidence",
            ],
        },
        "crime thriller": {
            "engines": [
                "a witness must decide whether to cooperate",
                "a plan begins to fail because of one overlooked detail",
                "an investigator faces conflicting evidence",
                "two adversaries possess leverage over each other",
                "a character discovers they have been used by both sides",
                "a deception becomes impossible to maintain",
            ],
            "endings": [
                "an escape with lasting consequences",
                "a partial victory",
                "a betrayal with a clear cost",
                "an uneasy compromise",
                "a resolution that leaves justice incomplete",
            ],
        },
        "comedy": {
            "engines": [
                "a small lie requires increasingly absurd explanations",
                "a character takes an instruction far too literally",
                "two people confidently misunderstand the same situation",
                "a plan works perfectly for the wrong reason",
                "an attempt to appear competent creates public embarrassment",
                "a minor inconvenience becomes an absurd competition",
            ],
            "endings": [
                "a comic reversal",
                "an embarrassing but harmless consequence",
                "an absurd success",
                "a punchline that reinterprets an earlier detail",
                "a character accidentally getting exactly what they asked for",
            ],
        },
        "tragedy": {
            "engines": [
                "a reasonable decision gradually produces irreversible harm",
                "two people cannot reconcile incompatible obligations",
                "a character recognizes a mistake too late",
                "an attempt to protect someone causes a different loss",
                "a long-standing conflict reaches a point of no return",
                "a character must accept the consequences of a past choice",
            ],
            "endings": [
                "an irreversible loss",
                "a reconciliation that comes too late",
                "a victory rendered meaningless by its cost",
                "a consequence that cannot be undone",
                "a quiet ending shaped by absence",
            ],
        },
        "fantasy": {
            "engines": [
                "a magical rule has an unexpected practical consequence",
                "a journey through a place governed by unfamiliar customs",
                "a bargain with an entity whose intentions are unclear",
                "a character inherits an ability they do not understand",
                "two communities interpret the same magical event differently",
                "a seemingly ordinary task requires an extraordinary solution",
            ],
            "endings": [
                "a magical cost is revealed",
                "a bargain is fulfilled in an unexpected way",
                "a transformation with mixed consequences",
                "a discovery about the world's rules",
                "an unresolved encounter with the extraordinary",
            ],
        },
        "human drama": {
            "engines": [
                "two people remember the same event differently",
                "a private decision affects an entire family",
                "a character conceals a truth for a complicated reason",
                "competing obligations force an uncomfortable compromise",
                "an ordinary conversation exposes a long-standing conflict",
                "a character's attempt to help is misunderstood",
            ],
            "endings": [
                "a difficult compromise",
                "a relationship changed but not repaired",
                "a truth revealed without easy forgiveness",
                "an understated reconciliation",
                "a loss accepted without a neat resolution",
            ],
        },
    }

    def __init__(self, client: OpenAI):
        self.client = client
        self.last_metadata = {}
        self.api_calls = 0

    def generate_story(
        self,
        genre: str | None = None,
        narrative_engine: str | None = None,
        ending_style: str | None = None,
    ) -> str:
        selected_genre = genre or random.choice(list(self.STORY_DESIGNS))

        if selected_genre not in self.STORY_DESIGNS:
            raise ValueError(
                f"Unknown genre: {selected_genre}. "
                f"Choose from: {', '.join(self.STORY_DESIGNS)}"
            )

        design = self.STORY_DESIGNS[selected_genre]

        selected_engine = narrative_engine or random.choice(design["engines"])
        selected_ending = ending_style or random.choice(design["endings"])

        if selected_engine not in design["engines"] and narrative_engine:
            # Custom engines are allowed, but the caller is responsible
            # for ensuring that they fit the selected genre.
            pass

        self.last_metadata = {
            "genre": selected_genre,
            "narrative_engine": selected_engine,
            "ending_style": selected_ending,
        }

        prompt = f"""
Write an original story for a narrated short-form video.

GENRE: {selected_genre}
NARRATIVE ENGINE: {selected_engine}
ENDING DIRECTION: {selected_ending}

LENGTH
Aim for 120–150 words, approximately 45–60 seconds of narration. The length
is flexible: do not add filler or cut a clear, complete story just to hit a number.

MAKE THE STORY EASY TO ENTER AND FOLLOW
- Use simple, familiar English and natural spoken sentences. Prefer concrete
  words over ornate, poetic, abstract, or unusually formal phrasing.
- In the opening 1–2 sentences, orient the listener with the main character (or
  relevant people), the immediate situation, and one specific detail that makes
  us curious. An unusual opening is fine if the listener can quickly understand
  what is happening and why it matters.
- Give important people, places, and circumstances enough context to be clear;
  do not make the listener guess at basic facts needed to follow the story.
- Let the central situation develop through a few connected moments. Show what
  changes, what the character notices or chooses, and the consequence. Do not
  jump from setup to climax or resolve the central tension in a single rushed
  sentence.
- Make cause and effect believable and easy to follow. Important events should
  grow from earlier details, choices, or circumstances, not arbitrary coincidence.
- Make the ending grow from what came before. Give the key choice, discovery,
  emotional shift, or consequence enough space to land; avoid abrupt or confusing
  endings and explain only what the audience needs to understand.
- Use this as flexible guidance, not a fixed beat template. Keep the genre's
  mood and allow quiet, unresolved, or unconventional stories when they remain
  clear and feel complete.

GENRE IS A CREATIVE REQUIREMENT

The story must deliver the experience of its assigned genre.
The genre must influence what happens, what the audience feels, and
what kind of conflict drives the story.

Do not merely decorate an ordinary inspirational story with genre
specific objects, terminology, or scenery.

USE THE NARRATIVE ENGINE

Build the events around the assigned narrative engine. It should
meaningfully drive the story rather than appear as a superficial detail.

The ending direction is a compatible creative suggestion, not a rigid
sequence of beats. Make the ending feel earned and appropriate.

NO UNIVERSAL STORY TEMPLATE

Do not require every protagonist to have a clearly stated goal.
Do not require escalating obstacles, a twist, personal growth, a moral,
a happy ending, or a neatly resolved conflict.

A story can begin with an event, a conversation, an observation,
a strange occurrence, an argument, a discovery, or an action already
in progress.

The protagonist may act deliberately, impulsively, reluctantly, or
react to events beyond their control.

Avoid defaulting to this familiar formula:
setback → adaptation → convenient reward → inspirational lesson.

GENRE-SPECIFIC GUIDANCE

Horror: prioritize dread, vulnerability, disturbing implications, or fear.
Do not automatically explain every strange event.

Adventure: prioritize exploration, action, physical challenges, discovery,
and consequential choices.

Romance: prioritize attraction, emotional risk, incompatibility, intimacy,
or longing. Do not require the couple to end up together.

Science fiction: make the speculative idea matter to the events and
consequences, rather than using technology as decoration.

Mystery: establish a meaningful question, clue, contradiction, or uncertainty.
The resolution may be complete or partial, depending on the story.

Crime thriller: use wrongdoing, conflicting interests, danger, leverage,
investigation, or deception to create tension.

Comedy: create an actual comic situation through behavior, timing,
misunderstanding, absurdity, or consequences. Do not append a moral.

Tragedy: let choices, circumstances, or flaws produce meaningful loss.
Do not turn the ending into a joke or a motivational lesson.

Fantasy: make the extraordinary premise influence the characters and events.

Human drama: focus on believable people, competing needs, relationships,
and consequential situations. Ordinary events are welcome when specific
and emotionally compelling.

ORIGINALITY

Avoid familiar premises and plots unless you bring a genuinely distinctive
execution. Do not reuse the same underlying conflict with different names or props.

Do not add twists merely to surprise the audience. A straightforward
story with strong execution is preferable to an arbitrary twist.

Do not reward every protagonist. Failure, uncertainty, loss, absurdity,
and unresolved conflict are valid outcomes.

VOICEOVER

Use natural spoken language, concrete details, and clear narration.
Use dialogue only when it helps.
Do not include headings, labels, camera directions, or commentary.

Return only the story.
"""

        response = self.client.responses.create(
            model="gpt-5-mini",
            input=prompt,
        )
        self.api_calls += 1
        return response.output_text.strip()

