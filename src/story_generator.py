from openai import OpenAI


class StoryGenerator:
    def __init__(self, client: OpenAI):
        self.client = client

    def generate_story(self):
        prompt = """
Write an original narrated short story for social media.

TARGET LENGTH
- Approximately 75–110 seconds of narration.
- Approximately 190–280 words.
- Prioritize story quality over hitting an exact word count.

WHAT A STORY MEANS

A story is not simply a sequence of interesting events.

A strong story follows a character through a meaningful problem:

    desire/problem
        ↓
    difficult situation
        ↓
    decision
        ↓
    consequence
        ↓
    escalating problem
        ↓
    another decision
        ↓
    turning point
        ↓
    consequence / resolution

The events should be causally connected.

A character's choices should influence what happens next.
What happens next should create new pressure, consequences, or choices.

The protagonist should actively participate in the story rather than
simply observing strange or interesting events.

IMPORTANT:
The story does NOT need a twist, mystery, supernatural element, secret,
or shocking revelation.

Ordinary human situations are encouraged when they contain meaningful
conflict and difficult choices.

Possible story foundations include:
- someone trying to save a failing business
- a parent trying to repair a broken relationship with their child
- two friends competing for the same opportunity
- someone hiding a mistake that may soon be discovered
- a person deciding whether to return something valuable they found
- an employee wrongly blamed for a serious mistake
- an elderly person trying to complete something their partner started
- someone choosing between financial security and doing what they believe is right
- someone trying to make amends before it is too late

These are examples of conflict types, not plots to copy.

STORY PROGRESSION

Before writing, silently determine:

- Who is the protagonist?
- What does the protagonist want or need?
- Why does it matter?
- What prevents them from getting it?
- What difficult choice must they make?
- What happens because of that choice?
- How does the situation become more difficult?
- What decisive moment changes the direction of the story?
- What consequence follows?
- How has the protagonist or their situation changed?

Do not output this planning.
Use it only to construct the story.

CAUSALITY

Major events should be connected.

Prefer:

    Event → decision → consequence → new problem → decision

Avoid:

    Event → unrelated event → discovery → reaction → ending

If an important event could be removed without changing what happens
afterward, reconsider whether that event belongs in the story.

CHARACTER AGENCY

The protagonist should make meaningful choices.

Do not let the protagonist simply:
- discover something strange
- react emotionally
- receive information
- follow someone else
- watch events happen

Their choices should create consequences.

When another character appears, give that character a purpose.
Their actions, desires, conflict, or decisions should affect the story.

DIALOGUE

Use dialogue sparingly.

Dialogue should reveal character, create conflict, force a decision,
or move the story forward.

Avoid robotic conversations where characters simply explain the plot
or tell each other information they would naturally already know.

Prefer natural, imperfect human dialogue.

PACING

Do not rush important emotional or dramatic moments.

When the protagonist faces an important decision, allow enough narrative
space for the audience to understand:
- what the protagonist stands to lose
- why the decision is difficult
- what choice they make

Do not immediately jump from the decision to the final consequence.

ENDING

The ending must pay off the central conflict.

The final outcome should be caused by, or meaningfully connected to,
the choices and events that came before it.

A turning point does not have to be a twist.

It can be:
- a difficult decision
- a confrontation
- a failure
- a sacrifice
- a realization
- an unexpected consequence
- a change in a relationship
- a meaningful success or loss

Do not introduce a completely new mystery, character, objective, or
major plot thread in the final lines simply to create suspense.

Do not end with an artificial cliffhanger unless the story genuinely
calls for one.

The audience should feel that the story has reached a meaningful
conclusion, even if some details remain open.

FEW-SHOT EXAMPLES

The following examples demonstrate the type of storytelling desired.
Do not copy their characters, settings, wording, or specific plots.

EXAMPLE 1:

Every morning, Meera opened her father's bakery at six.

Every morning, she wondered if she should close it.

The bakery had been losing money for months, and that afternoon a
supermarket offered to buy the shop.

Her father had built the bakery from nothing, but he had been gone
for two years.

Meera decided to accept.

That evening, an old customer came in and ordered the same bread her
father used to make.

While preparing it, Meera noticed something strange. The recipe card
had dozens of names written on the back.

Customers.

Beside each name was a date and a note about what they had needed
when her father had quietly given them bread for free.

She found herself remembering them.

The next morning, instead of opening the shop, she walked through
the neighborhood and knocked on their doors.

Most couldn't afford much.

But one offered to paint the bakery sign.

Another offered to repair the oven.

A retired accountant offered to help with the books.

By noon, Meera realized something.

Her father hadn't built a bakery.

He had built a community.

She called the supermarket.

"I changed my mind."

EXAMPLE 2:

For six months, Ravi had been trying to convince his daughter to speak
to him.

She answered every message with one word.

On her eighteenth birthday, he left a present outside her door.

She returned it unopened.

The next morning, Ravi finally asked why.

"You promised you'd come to my school performance," she said.
"You never came."

Ravi wanted to explain that his boss had threatened to fire him that night.

Instead, he admitted the truth.

"I chose work."

She stared at him.

"Then why should I believe you'll choose me now?"

Ravi had no answer.

Three days later, he received an offer for a promotion.

It meant more money.

It also meant moving to another city.

For years, he would have accepted immediately.

This time, he turned it down.

He didn't tell his daughter.

Instead, he showed up outside her school every afternoon for a week.

On Friday, she finally came outside.

"You're still here?"

Ravi smiled.

"I said I'd be."

She didn't forgive him.

Not yet.

But she sat beside him on the steps.

For the first time in six months, they went home together.

EXAMPLE 3:

Priya accidentally sent the wrong financial report to the company's
biggest client.

Nobody noticed.

Yet.

She could quietly replace the file before anyone found out.

But the numbers in the report had already been used in a decision that
could cost the client millions.

She told her manager.

He stared at her.

"Do you understand what you've done?"

"Yes."

"You could lose your job."

"I know."

They spent the night fixing the damage.

The next morning, the client called.

Priya expected anger.

Instead, the client asked:

"Who found the mistake?"

Priya hesitated.

"I did."

"Good," he said. "Because if you hadn't told us, we'd never have known."

She kept her job.

But more importantly, she learned something she hadn't understood before:

being trustworthy wasn't the same as never making mistakes.

It meant taking responsibility when you did.

END OF EXAMPLES


ORIGINALITY

Create a new story.

Do not combine the examples mechanically.

Do not reproduce their structure with different names.

Do not default to the same emotional lesson.

Explore different:
- occupations
- relationships
- settings
- conflicts
- stakes
- emotional outcomes
- endings

Avoid repeatedly generating supernatural mysteries, mysterious objects,
hidden identities, rescues, reunions, or sentimental "everything became
happy" endings.

The story should feel like something that happened to real people,
unless the chosen premise naturally requires something else.

VOICEOVER

- Write naturally for narration.
- Use concrete details and sensory moments.
- Keep sentences easy to follow when spoken aloud.
- Use paragraphs to create natural pacing.
- Do not include camera directions.
- Do not include visual instructions.
- Do not include headings.
- Write only the story.

FINAL SILENT CHECK

Before returning the story, silently check:

1. Does the protagonist want or need something?
2. Is there a meaningful obstacle or conflict?
3. Does the protagonist make consequential decisions?
4. Do those decisions affect what happens next?
5. Does the conflict escalate or become more difficult?
6. Are the major events causally connected?
7. Is there a meaningful turning point?
8. Does the ending pay off the central conflict?
9. Does the protagonist or their situation change?
10. Does the story feel like a complete narrative rather than an incident?

If any answer is no, revise the story before returning it.

Write only the final story.
"""

        response = self.client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )

        return response.output_text