---
description: Turn a strategy Google Doc into a Google Slides presentation via HTML and Apps Script
argument-hint: <Google Doc URL> [optional: audience and goal description]
---

You are helping build a polished, data-driven presentation from a strategy document.

## Your task

Given the Google Doc at: $ARGUMENTS

Follow these steps in order:

### 1. Read the document
Use the `read_google_docs_document` Captain MCP tool to read the Google Doc. Confirm you can see the content before proceeding. If you cannot access it, stop and tell the user.

### 2. Plan the presentation
Before building anything, output a brief outline:
- Proposed slide titles and flow
- Any data or charts mentioned that will need special handling
- Any clarifying questions you have

Wait for the user to confirm the outline or suggest changes before proceeding.

### 3. Build the HTML presentation
Create a file called `presentation.html` in the current directory. The presentation should:
- Closely follow Google Slides design conventions (16:9 slides, clean layout)
- Be self-contained in a single HTML file with embedded CSS and JS
- Include slide navigation (arrow keys or buttons)
- Have a consistent visual style throughout
- Include speaker notes where appropriate

### 4. Generate the Apps Script
Once the HTML is created, generate a `presentation.gs` file containing a Google Apps Script that:
- Recreates the presentation structure in Google Slides
- Preserves colors, fonts, and layout as closely as possible
- Outputs a link to the finished Google Slides deck when executed

### 5. Give the user next steps
Print clear instructions:
1. Go to script.google.com
2. Click New Project, name it, save
3. Paste the contents of `presentation.gs`
4. Click Execute
5. Open the output link

## Important rules
- If you encounter images or charts in the doc that you cannot read, stop and ask the user to provide the underlying data or a text description
- Ask clarifying questions rather than guessing about audience, goal, or tone
- Never skip the outline confirmation step
