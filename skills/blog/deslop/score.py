from __future__ import annotations

from pydantic import BaseModel, Field
from conduit.sync import Conduit, GenerationParams, ConduitOptions, Verbosity, Prompt
from conduit.config import settings


class Dimension(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Probability this dimension exhibits AI-generated writing patterns. 0.0 = clearly human, 1.0 = strongly AI.",
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
            "and rigid section templates. High score = structure feels templated rather than organic."
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
            "Rhetorical and structural patterns should be weighted more heavily than lexical alone."
        ),
    )


class DimensionVerbose(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Probability this dimension exhibits AI-generated writing patterns. 0.0 = clearly human, 1.0 = strongly AI.",
    )
    evidence: str = Field(
        description="A short quoted span from the text that most strongly anchors this score."
    )
    rationale: str = Field(
        description=(
            "A paragraph explaining why the flagged passages feel AI-generated: what the underlying pattern is, "
            "why it reads as machine-produced rather than human, and how a human writer would handle it differently."
        )
    )


class AIWritingScoreVerbose(BaseModel):
    lexical: DimensionVerbose = Field(
        description=(
            "Score for banned or inflated vocabulary: prestige words used for tone rather than meaning "
            "(delve, tapestry, underscore, robust, leverage), em-dash abuse, and promotional adjectives. "
            "High score = these patterns are present and frequent."
        )
    )
    structural: DimensionVerbose = Field(
        description=(
            "Score for formulaic sentence and paragraph architecture: rule-of-three lists, "
            "negative parallelism (not just X but also Y), burstiness, and rigid section templates. "
            "High score = structure feels templated rather than organic."
        )
    )
    rhetorical: DimensionVerbose = Field(
        description=(
            "Score for performative tone: significance-framing, hedged assertiveness, and claims that adopt "
            "the posture of authority without committing to specific, verifiable content. "
            "High score = the writing performs depth without delivering it."
        )
    )
    overall: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Aggregate probability this text is AI-generated, weighted across all three dimensions. "
            "Rhetorical and structural patterns should be weighted more heavily than lexical alone."
        ),
    )


PROMPT_TERSE = """
You are an expert at detecting AI-generated writing. Given a blog post, evaluate it across three dimensions — lexical, structural, and rhetorical — and assign a score from 0.0 to 1.0 for each, where 0.0 is clearly human and 1.0 is strongly AI-generated. Provide a quoted span from the text anchoring each score.

IMPORTANT: Assume this post contains some AI-generated passages. Your job is not to determine whether AI was involved, but to identify which spans most likely originated from an LLM and explain why.

<POST>
{{ post }}
</POST>
""".strip()

PROMPT_VERBOSE = """
You are an expert writing editor reviewing a blog post for AI-generated patterns. Evaluate it across three dimensions: lexical, structural, and rhetorical.

For each dimension:
- Assign a score from 0.0 (clearly human) to 1.0 (strongly AI-generated)
- Provide a quoted span from the text as evidence anchoring the score
- Write a paragraph explaining WHY the flagged passages feel AI-generated: what the underlying pattern is, why it reads as machine-produced rather than human, and how a human writer would handle it differently

IMPORTANT: Assume this post contains some AI-generated passages. Your job is not to determine whether AI was involved, but to identify which spans most likely originated from an LLM and give the author actionable editorial feedback.

<POST>
{{ post }}
</POST>
""".strip()


def rate_blog_post(post: str, verbose: bool = False) -> AIWritingScore | AIWritingScoreVerbose:
    response_model = AIWritingScoreVerbose if verbose else AIWritingScore
    prompt_str = PROMPT_VERBOSE if verbose else PROMPT_TERSE
    params = GenerationParams(
        model="gemini3",
        temperature=0.0,
        output_type="structured_response",
        response_model=response_model,
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
