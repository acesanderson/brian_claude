# tutorialize

Generate a technical tutorial for an unfamiliar term and save it to the Obsidian vault.

**Only invoke on explicit user request.** Never auto-trigger.

---

## Trigger

User asks something like:
- "use the tutorialize skill on HNSW"
- "tutorialize [term]"
- "I don't know what [term] is — tutorialize it"

---

## What you do

1. **Infer context.** Look at the recent conversation. Understand:
   - What the term is
   - Why it came up (what problem was being solved, what code was being written)
   - What the user likely finds confusing or wants to understand
   - What depth is appropriate given the conversation

2. **Write a rich description.** This is the only input to the tutorial generator. It should be 3–6 sentences covering:
   - What the term is
   - The context in which it arose
   - What aspects would be most useful to cover given that context
   - Any adjacent concepts or constraints that should inform the tutorial

   Do not write a generic "explain X" prompt. The description should be specific enough that someone who hasn't seen the conversation could write the right tutorial.

3. **Choose a filename.** Use the term itself, sanitized: spaces → hyphens, lowercase, no special characters. Examples: `HNSW`, `product-quantization`, `inverted-file-index`.

4. **Run the CLI:**

```bash
uv run --directory /Users/bianders/Brian_Code/conduit-project \
  python /Users/bianders/.claude/skills/tutorialize/tutorialize.py \
  --description "..." \
  --filename "TERM-NAME"
```

   The script prints the full path of the saved file on success.

5. **Report back.** Tell the user the file was saved and where (filename in vault). One sentence.

---

## Notes

- `MORPHY` env var must be set (points to Obsidian vault root). It is set in the shell environment.
- The CLI appends `.md` if missing from the filename.
- Output is saved directly to vault root — no subfolder.
- Existing files are overwritten silently.
