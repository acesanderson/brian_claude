# kramer CLIs — Full Reference

Three CLIs backed by MongoDB and LLMs. All invoked via:
```bash
uv run --project /Users/bianders/Brian_Code/kramer-project <cli> <subcommand> [args]
```

---

## `linkedin-catalog` — Course Lookup + Search

**Lookup by ID or title** (default mode — no subcommand):
```bash
uv run --project /Users/bianders/Brian_Code/kramer-project linkedin-catalog <course_id> [flags]
```

| Flag | Purpose |
|---|---|
| `--json` / `-j` | Structured JSON output |
| `--metadata` / `-m` | Full metadata dict (60+ fields) |
| `--toc` / `-c` | Table of contents |
| `-v` | Verbose: long description + full TOC + instructor bio |
| `--description` / `-d` | Short description only |
| `--instructor` / `-i` | Instructor name only |
| `--url` / `-u` | LiL URL only |
| `--transcript` / `-t` | Full transcript |
| `--stdin` | Read IDs/titles from stdin, one per line (batch mode) |

**Batch usage:**
```bash
# Positional
uv run --project /Users/bianders/Brian_Code/kramer-project linkedin-catalog 4314028 2818049 --json --metadata

# Stdin — preferred for large lists
printf '4314028\n2818049\n' | uv run --project /Users/bianders/Brian_Code/kramer-project linkedin-catalog --stdin --json --metadata
```

**JSON output schema:**
```
{
  "course_admin_id": int,
  "course_title": str,
  "url": str,
  "short_description": str,
  "metadata": { ...60+ fields... },  # only with --metadata
  "toc": [ ...section hierarchy... ] # only with --toc
}
```

**High-value metadata fields for licensing triage:**
- `LI Level EN` — Beginner / Intermediate / Advanced
- `Visible Duration` — runtime string (e.g. "1h 23m")
- `Visible Video Count` — number of videos
- `Course Release Date` / `Course Updated Date` — freshness signal
- `Activation Status` — Active / Retired
- `Internal Library` / `Internal Subject` — content taxonomy
- `Instructor Name` / `Author Payment Category`
- `Has Assessment` — bool
- `LIL URL` — canonical learner URL
- `Skills EN` — skill tags

**`search` subcommand** — find courses by query:
```bash
# Semantic search (default — uses Headwater vector index)
uv run --project /Users/bianders/Brian_Code/kramer-project linkedin-catalog search "machine learning" [-k 10] [--json]

# Title substring match
uv run --project /Users/bianders/Brian_Code/kramer-project linkedin-catalog search --title "Python"

# Transcript substring match
uv run --project /Users/bianders/Brian_Code/kramer-project linkedin-catalog search --transcript "pandas"

# Transcript with surrounding context
uv run --project /Users/bianders/Brian_Code/kramer-project linkedin-catalog search --transcript "pandas" --grep
```

| Flag | Purpose |
|---|---|
| `--title` | Substring match on course titles |
| `--transcript` | Substring match in transcripts |
| `--grep` | Show surrounding context (use with `--transcript`) |
| `-k N` | Number of semantic results (default: 5) |
| `--json` / `-j` | Output as JSON |

**When to use lookup vs. search in licensing sessions:**
- **Lookup**: spot-check a known course ID, pull TOC for redundancy analysis, batch-fetch metadata for a curated list
- **`search --title`**: find existing LiL courses on a topic to assess gap before recommending a partner
- **`search` (semantic)**: broader discovery — "what courses do we already have on X?"
- **Never use for**: discovery of _new_ (non-LiL) courses — use the catalog DB or classifier

---

## `certs` — Certification Partnership Research

LLM-backed tools for cert BD research. Use when evaluating a new cert partner or topic.

```bash
uv run --project /Users/bianders/Brian_Code/kramer-project certs <subcommand> [args]
```

**Subcommands:**

```bash
# Suggest partner orgs for a cert topic (Claude-backed)
certs partners "Data Science" [-n 20]

# Suggest cert topics for a partner org (Claude-backed)
certs topics "IBM" [-n 20]

# Research marketing metrics for an org (Perplexity-backed — revenue, employees, market share)
certs research "IBM"
```

**When to use in licensing sessions:**
- `partners` — brainstorm who might be a good cert partner for a gap topic identified in Content Strategy data
- `topics` — after landing a partner conversation, explore which cert topics make sense for them
- `research` — quick marketing snapshot before an outreach or Gate A submission; faster than a manual Perplexity search

---

## `curriculum` — AI Curriculum Design Tools

LLM-backed tools for generating curriculum artifacts from a list of courses. Useful for evaluating a partner's proposed LP structure or generating pitch materials.

```bash
uv run --project /Users/bianders/Brian_Code/kramer-project curriculum <subcommand> [args]
```

**Subcommands:**

```bash
# Generate a full curriculum series using a course as the series opener
curriculum first "Python Essential Training"

# Generate a capstone project for a set of courses
curriculum capstone "ML Path" "Intro to ML" "Advanced ML"
echo "Intro to ML\nAdvanced ML" | curriculum capstone "ML Path" --stdin

# Generate a Learning Path (audience description, LP description, learning objectives)
curriculum lp "ML Path" "Intro to ML" "Advanced ML"
curriculum lp "ML Path" "Intro to ML" "Advanced ML" --save        # writes <title>.md
curriculum lp "ML Path" "Intro to ML" "Advanced ML" --save --gdoc # also pushes to Google Doc
echo "Advanced ML" | curriculum lp "ML Path" "Intro to ML" --stdin
```

**When to use in licensing sessions:**
- `lp` — generate audience/description/objectives copy for a proposed LP during partner pitch prep or Gate B materials; `--save` writes a markdown artifact you can share
- `capstone` — generate a capstone project concept when pitching a cert program to a partner
- `first` — explore what a full curriculum series might look like if a partner's course is the opener; useful for framing an upsell or multi-course deal
