from __future__ import annotations
from pydantic import BaseModel, Field
from conduit.sync import Conduit, GenerationParams, ConduitOptions, Verbosity, Prompt
from conduit.config import settings


class Dimension(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Probability this dimension exhibits AI-generated writing patterns. 0.0 = clearly human, 1.",
    )
    evidence: str = Field(
        description="A short quoted span from the text that most strongly anchors this score."
    )


class AIWritingScore(BaseModel):
    lexical: Dimension = Field(
        description=(
            "Score for banned or inflated vocabulary: prestige words used for tone rather than meaning "
            "(delve, tapestry, underscore, robust, leverage), em-dash abuse, and promotional adjectives "
            "(vibrant, nestled, rich heritage). High score = these patterns are present and frequent."
        )
    )
    structural: Dimension = Field(
        description=(
            "Score for formulaic sentence and paragraph architecture: rule-of-three lists, "
            "negative parallelism (not just X but also Y), burstiness (unnaturally uniform sentence lengths), "
            "and rigid section templates (Challenges and Future Prospects, etc.). "
            "High score = structure feels templated rather than organic."
        )
    )
    rhetorical: Dimension = Field(
        description=(
            "Score for performative tone: significance-framing (marks a pivotal moment, plays a vital role), "
            "hedged assertiveness (experts say, it is widely believed), and claims that adopt the posture "
            "of authority without committing to specific, verifiable content. "
            "High score = the writing performs depth without delivering it."
        )
    )
    overall: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Aggregate probability this text is AI-generated, weighted across all three dimensions. "
            "Not a simple average — rhetorical and structural patterns should be weighted more heavily "
            "than lexical alone, since lexical tells are easier to suppress."
        ),
    )


prompt_str = """
You are an expert at detecting AI-generated writing. Given a blog post, you will evaluate it across three dimensions — lexical, structural, and rhetorical — and assign a score from 0.0 to 1.0 for each dimension, where 0.0 indicates the text is clearly human-written and 1.0 indicates strong evidence of AI-generated patterns. Additionally, you will provide an overall score that aggregates these dimensions into a single probability that the text is AI-generated.

IMPORTANT: Assume this post contains some AI-generated passages. Your job is not to determine whether AI was involved, but to identify which spans most likely originated from an LLM and explain why.

Here's the post to evaluate:
<POST>
{{ post }}
</POST>
""".strip()


def rate_blog_post(post: str) -> AIWritingScore:
    params = GenerationParams(
        model="gemini3",
        temperature=0.0,
        output_type="structured_response",
        response_model=AIWritingScore,
    )
    options = ConduitOptions(
        project_name="slop",
        cache=settings.default_cache("slop"),
        verbosity=Verbosity.PROGRESS,
    )
    prompt = Prompt(prompt_str)
    conduit = Conduit(prompt=prompt, params=params, options=options)
    response = conduit.run(input_variables={"post": post})
    return response.last.parsed


if __name__ == "__main__":
    from pathlib import Path

    posts_path = Path("~/blog/_posts/").expanduser()
    posts = posts_path.glob("*.md")

    for post in posts:
        text = post.read_text()
        score = rate_blog_post(text)
        print(f"{post}: {score}")
