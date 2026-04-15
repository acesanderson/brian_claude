# CYMBII Links

CYMBII = "Courses You May Be Interested In" — the LinkedIn Feed card that surfaces LiL courses.

## URL format

```
https://www.linkedin.com/feed/update/urn:li:lyndaCourse:{COURSE_ID}/
```

Replace `{COURSE_ID}` with the numeric course ID. Example:

```
https://www.linkedin.com/feed/update/urn:li:lyndaCourse:779751/
```

The LiL Buddy browser extension generates these links automatically from any course page.

## Golden path — given a course title

**Step 1 — get the course ID:**
```bash
uv run --project /Users/bianders/Brian_Code/kramer-project linkedin-catalog search --title "<title>" --json
```
Take the `course_admin_id` from the exact-match result.

**Step 2 — compose the URL:**
```
https://www.linkedin.com/feed/update/urn:li:lyndaCourse:{course_admin_id}/
```

Example for "Python Essential Training" (ID: 4314028):
```
https://www.linkedin.com/feed/update/urn:li:lyndaCourse:4314028/
```
