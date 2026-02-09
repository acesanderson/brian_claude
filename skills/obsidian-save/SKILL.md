---
name: obsidian-save
description: Save content to Obsidian vault as markdown notes. Use when the user asks to save, create, or capture content as an Obsidian note, including meeting notes, code snippets, research findings, web content, or any text/files from conversations. Trigger phrases include "save this to Obsidian", "create a note", "add this to my vault", or similar requests to persist content.
---

# Obsidian Save

Save content to the user's Obsidian vault at `/Users/bianders/morphy` as markdown notes.

## Quick Start

When the user asks to save content, use the Write tool to create a markdown file at `/Users/bianders/morphy/filename.md`.

**Examples:**

```
User: "Save this as a note about Python logging"
→ Write to `/Users/bianders/morphy/Python logging.md`

User: "Create a note called 'API ideas'"
→ Write to `/Users/bianders/morphy/API ideas.md`

User: "Capture this meeting summary"
→ Ask for filename, then write to `/Users/bianders/morphy/[filename].md`
```

## Filename Guidelines

- Use the user's specified filename if provided
- Otherwise, derive a clear, descriptive filename from the content
- Use natural naming: spaces are fine, keep it readable
- Add `.md` extension
- Examples: `Meeting notes 2026-01-28.md`, `Python best practices.md`, `Bug fix ideas.md`

## Creating Notes

Use the Write tool with these practices:

**For new notes:**
- Always use full absolute path: `/Users/bianders/morphy/filename.md`
- Use clean markdown formatting
- Include headings, code blocks, lists as appropriate

**For appending to existing notes:**
- First Read the existing note
- Then Write with the original content + new content appended

## Wikilink Support

When creating notes that reference other content:
- Use Obsidian wikilink format: `[[Page Name]]`
- Link to related notes: `See also [[Related Topic]]`
- No need to check if linked notes exist - Obsidian handles broken links gracefully

**Example:**
```markdown
# API Design Notes

Key concepts from [[REST API Patterns]] and [[Authentication Methods]].

## Related
- [[Database Schema]]
- [[Frontend Integration]]
```

## Content Types

Handle all content types appropriately:

**Meeting notes/summaries**: Use headings, bullet points, clear structure
**Code snippets**: Use code blocks with language tags
**Research/web content**: Preserve formatting, add source links
**Quick captures**: Simple, direct - just save the content

## Workflow

1. Determine filename (use provided name or derive from content)
2. Check if appending to existing note or creating new
3. Format content appropriately in markdown
4. Write to `/Users/bianders/morphy/filename.md`
5. Confirm to user what was saved and where
