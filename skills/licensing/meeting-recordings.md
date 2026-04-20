# Meeting Recordings

Workflow for transcribing and summarizing meeting recordings (all-hands, team meetings, 1:1s, etc.).

**Privacy rule:** Recordings contain proprietary content. Always use `gpt-oss:latest` via Headwater. Never use cloud models.

## Golden Path

**Step 1 — Transcribe** (siphon CLI):
```bash
siphon extract <recording.mp3>
```
Output is a plain-text transcript (speaker-labeled if diarization is available).

**Step 2 — Write summary prompt** (Write tool → `/tmp/<slug>_summary_prompt.txt`):
```
You are summarizing a meeting transcript. Extract:
- Key decisions made
- Action items (owner, what, by when if stated)
- Main topics discussed (3–7 bullets per topic)
- Notable quotes or data points

Transcript:
<paste transcript>
```

**Step 3 — Summarize via HeadwaterClient** (Python, using pre-existing headwater-client venv):
```python
from __future__ import annotations
import asyncio
from pathlib import Path
from headwater_client.client.headwater_client_async import HeadwaterAsyncClient
from headwater_api.classes import BatchRequest
from conduit.domain.request.generation_params import GenerationParams
from conduit.domain.config.conduit_options import ConduitOptions

async def main() -> None:
    prompt = Path("/tmp/<slug>_summary_prompt.txt").read_text()
    params = GenerationParams(model="gpt-oss:latest", temperature=0.3)
    options = ConduitOptions(project_name="siphon-summary", include_history=False)
    batch_req = BatchRequest(prompt_strings_list=[prompt], params=params, options=options)
    async with HeadwaterAsyncClient() as client:
        response = await client.conduit.query_batch(batch_req)
    msg = response.results[0].last
    content = msg.content
    if isinstance(content, str):
        print(content)
    elif isinstance(content, list):
        print("".join(c if isinstance(c, str) else c.text for c in content))
    else:
        print(str(content))

asyncio.run(main())
```
Run with: `/Users/bianders/Brian_Code/headwater/headwater-client/.venv/bin/python /tmp/summarize.py`

**Step 4 — Save to Obsidian** (Write tool):
- Path: `$MORPHY/MEET-YYYY-MM-DD-<slug>.md`
- Use the summary output directly as the note body
- Slug: lowercase, hyphen-separated, descriptive (e.g., `company-connect`, `cm-ai-research-tools`)
