# Obsidian CLI Reference

Requires: `obsidian` CLI on PATH and the Obsidian desktop app open.

Verify: `obsidian --version`

## Syntax conventions

Parameters use `=` assignment:
```
obsidian create name="My Note" content="Hello world"
```

Flags are boolean switches:
```
obsidian create name="My Note" silent overwrite
```

Multiline content: use `\n` for newlines, `\t` for tabs.

## File targeting

- `file=<name>` — resolves like a wikilink (name only, active file if omitted)
- `path=<path>` — exact path from vault root (e.g. `folder/note.md`)

## Vault targeting

```
obsidian vault="My Vault" search query="test"
```

Defaults to the most recently focused vault.

## Common operations

```bash
obsidian read file="My Note"
obsidian create name="New Note" content="# Hello" template="Template" silent
obsidian append file="My Note" content="New line"
obsidian search query="search term" limit=10
obsidian daily:read
obsidian daily:append content="- [ ] New task"
obsidian property:set name="status" value="done" file="My Note"
obsidian tasks daily todo
obsidian tags sort=count counts
obsidian backlinks file="My Note"
```

`--copy` flag copies output to clipboard. `silent` prevents files from opening in the app. `total` on list commands returns count.

## Plugin / theme development

```bash
obsidian plugin:reload id=my-plugin     # reload after code changes
obsidian dev:errors                      # check for errors
obsidian dev:screenshot path=out.png    # visual verification
obsidian dev:dom selector=".workspace-leaf" text
obsidian dev:console level=error        # inspect console
obsidian dev:css selector=".workspace-leaf" prop=background-color
obsidian dev:mobile on                  # toggle mobile emulation
```

## Eval (run JS in app context)

```bash
obsidian eval code="app.vault.getFiles().length"
```

## Full help

```bash
obsidian help
```
