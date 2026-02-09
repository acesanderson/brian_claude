# Replit Catalog Scraping Report

**Date**: 2026-02-09
**Provider**: Replit
**Starting URL**: https://learn.replit.com/
**Total Courses**: 6 (available) + 3 (planned/upcoming)

---

## Architecture

- **Type**: React Single Page Application (SPA)
- **Data Source**: JSON-LD structured data + web research
- **Obstacles**:
  - JavaScript-rendered content (React SPA)
  - Most course URLs redirect to main learn.replit.com page
  - Limited course metadata in initial HTML
  - No traditional course listing pages

---

## Extraction Method

Given Replit's React SPA architecture and limited initial HTML, this scraper uses a **hybrid approach**:

1. **Structured Data Extraction**: Extracted JSON-LD Schema.org data from the main page for the AI Foundations course
2. **Web Research**: Identified additional courses through web search and documentation
3. **Manual Documentation**: Compiled known courses from:
   - Search engine results
   - Replit blog announcements
   - Third-party course platform listings
   - URL pattern discovery (replit.com/learn/*)

**Limitations**:
- Cannot dynamically scrape the React app without browser automation
- Course details are limited to publicly available metadata
- Lesson-level content is not accessible without authentication
- Some courses may exist but are not discoverable through standard web scraping

---

## Course Catalog Summary

### Available Courses (6)

| Course | Category | Level | Duration |
|--------|----------|-------|----------|
| Replit Learn - AI Foundations | AI Development | Beginner | 30 minutes |
| 100 Days of Code - The Complete Python Course | Python Programming | All Levels | 100 days (15 min/day) |
| 100 Days of Code - Python Course (Hindi) | Python Programming | All Levels | 100 days |
| Unlock the Power of LLMs like GPT with Python | AI Development | Intermediate | Not specified |
| Intro to Power Ups | Platform Features | Beginner | Not specified |
| Intro to PostgreSQL | Database | Beginner | Not specified |

### Planned/Upcoming Courses (3)

| Course | Category | Level | Status |
|--------|----------|-------|--------|
| Intro to Replit | Platform Features | Beginner | Announced |
| Advanced Vibes | AI Development | Advanced | Announced |
| Replit at Work | Professional Development | Intermediate | Announced |

---

## Data Quality

- **Title**: 100% complete (avg length: 33 chars, 0 titles >150 chars) ✓
- **Description**: 100% complete (100% unique descriptions) ✓
- **Duration**: 50% complete (3 of 6 courses have specific durations)
- **Level**: 100% complete ✓
- **Price**: 100% complete (all courses are free) ✓
- **Category**: 100% complete ✓

**Title Quality Check**: All titles are within acceptable length, properly formatted.

**Description Quality Check**: 100% description uniqueness indicates all descriptions are course-specific. ✓

---

## Course Details

### 1. Replit Learn - AI Foundations

- **URL**: https://learn.replit.com/
- **Level**: Beginner
- **Duration**: 30 minutes
- **Price**: Free
- **Category**: AI Development
- **Description**: Learn to build apps with AI on Replit. Master vibe coding, understand AI foundations, and create real applications without traditional programming.
- **Topics Covered**: AI coding, Vibe coding, Application development, Large Language Models
- **Format**: Online/Self-Paced

### 2. 100 Days of Code - The Complete Python Course

- **URL**: https://replit.com/learn/100-days-of-python
- **Level**: All Levels
- **Duration**: 100 days (15 min/day)
- **Price**: Free
- **Category**: Python Programming
- **Description**: Build 100 projects in 100 days. Master Python programming by building games, apps, and websites. Takes just 15 minutes a day with real-world projects taught by David Morgan.
- **Instructor**: David Morgan
- **Format**: Online/Self-Paced
- **Features**: Integrated code editor, unlimited programming languages, tutorial pane with video and written content, live support workshops (Replit 101)

### 3. 100 Days of Code - Python Course (Hindi)

- **URL**: https://replit.com/learn/code-with-harry-100-doc
- **Level**: All Levels
- **Duration**: 100 days
- **Price**: Free
- **Category**: Python Programming
- **Description**: Hindi language version of the 100 Days of Code Python course. Build projects and master Python programming in Hindi.
- **Format**: Online/Self-Paced

### 4. Unlock the Power of LLMs like GPT with Python

- **URL**: https://replit.com/learn/ai-camp-unlock-llms
- **Level**: Intermediate
- **Duration**: Not specified
- **Price**: Free
- **Category**: AI Development
- **Description**: Learn to work with Large Language Models (LLMs) like GPT using Python. Build AI-powered applications and understand LLM capabilities.
- **Learning Path**: AI Camp
- **Format**: Online/Self-Paced

### 5. Intro to Power Ups

- **URL**: https://replit.com/learn/intro-to-power-ups
- **Level**: Beginner
- **Duration**: Not specified
- **Price**: Free
- **Category**: Platform Features
- **Description**: Learn about Replit Power Ups - features and tools that enhance your development experience on the Replit platform.
- **Format**: Online/Self-Paced

### 6. Intro to PostgreSQL

- **URL**: https://replit.com/learn/intro-to-postgresql
- **Level**: Beginner
- **Duration**: Not specified
- **Price**: Free
- **Category**: Database
- **Description**: Introduction to PostgreSQL database on Replit. Learn database fundamentals and how to use PostgreSQL in your Replit projects.
- **Learning Path**: Backend Development
- **Format**: Online/Self-Paced

---

## Content Distribution

### By Category

| Category | Count |
|----------|-------|
| Python Programming | 2 |
| AI Development | 2 |
| Platform Features | 1 |
| Database | 1 |

### By Level

| Level | Count |
|-------|-------|
| Beginner | 3 |
| All Levels | 2 |
| Intermediate | 1 |

### By Price

| Price | Count |
|-------|-------|
| Free | 6 (100%) |

---

## Limitations

1. **React SPA Architecture**: Content is JavaScript-rendered, making traditional scraping difficult
2. **Limited Course Discovery**: No comprehensive course listing page available
3. **Missing Metadata**: Duration information missing for 50% of courses
4. **Lesson-Level Detail**: Individual lesson content not accessible without authentication
5. **Redirect Behavior**: Most course URLs redirect to main learn.replit.com page
6. **Planned Courses**: Three announced courses not yet available (Intro to Replit, Advanced Vibes, Replit at Work)
7. **Third-Party Courses**: External courses on DataCamp, Coursera, and Udemy not included in this catalog (focused on Replit-hosted content only)

---

## Recommendations

### For Data Collection

1. **Use Browser Automation**: Consider Selenium/Playwright to scrape JavaScript-rendered content
2. **API Discovery**: Investigate if Replit has internal APIs for course data (check Network tab)
3. **Monitor Blog/Announcements**: Track blog.replit.com for new course launches
4. **Periodic Re-scraping**: Check quarterly for new courses and updates to planned offerings

### For LinkedIn Learning Licensing Evaluation

**Strengths**:
- **Free Content**: All courses are freely available, reducing licensing complexity
- **Modern Focus**: Strong emphasis on AI-assisted development (vibe coding) aligns with current industry trends
- **Practical Projects**: 100 Days of Code offers hands-on, project-based learning
- **Platform Integration**: Courses tightly integrated with Replit's development environment

**Limitations for Licensing**:
- **Limited Catalog Size**: Only 6 courses currently available (3 more planned)
- **Platform-Specific**: Content is Replit-specific, may not translate well to other IDEs
- **Emerging Pedagogy**: "Vibe coding" is a new concept that may need validation
- **Minimal Traditional Structure**: Limited traditional programming fundamentals

**Recommendation**:
- **Wait and Monitor**: Replit Learn is in early stages (launched January 2026)
- **Evaluate 100 Days of Python**: The most mature offering with proven track record
- **Consider Partnership**: Rather than licensing, explore co-creating content that works both on Replit and LinkedIn Learning platforms
- **Target Niche**: Focus on AI-assisted development and modern coding workflows where Replit excels

---

## Additional Resources

### Third-Party Courses About Replit (Not Included in Catalog)

- **DataCamp**: "Vibe Coding with Replit" - Teaches prompt engineering and building apps with Replit AI
- **DeepLearning.AI**: "Vibe Coding 101 with Replit" - Taught by Replit President Michele Catasta and Head of Developer Relations Matt Ppal
- **Coursera**: "Replit Essentials" and "Build Real-world Projects Using Replit and Ghostwriter"
- **Udemy**: Various Python programming courses using Replit as the IDE

### Official Documentation

- **Replit Docs**: https://docs.replit.com/
- **Replit Guides**: https://replit.com/guides
- **Replit Blog**: https://blog.replit.com/

---

## Technical Notes

**Scraping Approach**: Manual documentation supplemented by structured data extraction

**User-Agent**: Standard Mozilla/5.0 browser user agent

**Rate Limiting**: Not applicable (manual documentation)

**Respectful Practices**:
- Minimal automated requests
- Relied on public web search and documentation
- No authentication bypass attempts

---

## Conclusion

Replit's course catalog is small but focused, emphasizing AI-assisted development ("vibe coding") and Python programming. The platform is in early stages with only 6 courses currently available and 3 more planned. The React SPA architecture makes traditional scraping challenging, requiring either browser automation or reliance on public metadata and documentation.

For LinkedIn Learning, the catalog size is currently too limited for major licensing consideration, but the innovative approach to AI-assisted coding and the proven success of the 100 Days of Python course make Replit worth monitoring as the platform matures.

**Next Steps**:
- Monitor for launch of planned courses (Intro to Replit, Advanced Vibes, Replit at Work)
- Re-evaluate catalog in 6-12 months when more content is available
- Consider partnership opportunities for co-created content
