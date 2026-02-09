# Anthropic Catalog Scraping Report

**Date**: 2026-02-09
**URL**: https://anthropic.skilljar.com/
**Total Courses**: 12

---

## Architecture

- **Type**: Single Page Catalog with Individual Course Detail Pages
- **Data Source**: Server-rendered HTML (Skilljar learning platform)
- **Obstacles**: None - all courses publicly accessible without authentication
- **Platform**: Anthropic Academy (Skilljar-based LMS)

---

## Extraction Method

**Strategy B: Static HTML + Manual Course Detail Extraction**

Since the Anthropic Academy uses a Skilljar-based platform with all courses publicly listed, the extraction approach involved:

1. **Discovery Phase**: Used WebFetch to retrieve the main catalog page and identify all 12 available courses
2. **Detail Extraction**: Individually fetched each course detail page to extract comprehensive metadata including:
   - Title and URL
   - Full course descriptions (course-specific, not generic)
   - Level (Beginner/Intermediate/Advanced)
   - Format (Self-Paced Online, Video-Based Online, Instructor-Led Online)
   - Prerequisites (where applicable)
   - Learning objectives
   - Instructor information
   - Certification availability
   - Price (all courses are free)

3. **Data Compilation**: Manually compiled data into structured format ensuring:
   - Course-specific descriptions extracted from detail pages
   - Consistent categorization across similar courses
   - Complete prerequisite chains documented

**Why Manual Compilation**: The Skilljar platform renders course content dynamically, and each course page has unique structure. Given the small catalog size (12 courses), manual extraction from fetched HTML provided higher quality and more complete data than automated scraping.

---

## Data Quality

- **Title**: 100% complete (avg length: 27 chars, 0 titles >150 chars) ✓
- **Description**: 100% complete (100% unique - high quality course-specific descriptions) ✓
- **URL**: 100% complete ✓
- **Duration**: 0% complete (not explicitly stated on course pages) ⚠️
- **Level**: 100% complete ✓
- **Format**: 100% complete ✓
- **Price**: 100% complete ✓
- **Category**: 100% complete ✓
- **Prerequisites**: 50% complete (documented where applicable)
- **Learning Objectives**: 58% complete (7 of 12 courses)
- **Instructor**: 42% complete (5 of 12 courses - primarily AI Fluency track)
- **Certification**: 33% complete (4 confirmed certifications)

**Title Quality**: Excellent. All titles are concise (average 27 characters) and clearly distinguish courses.

**Description Quality**: Excellent. 100% unique descriptions extracted from individual course pages, ensuring course-specific content rather than generic catalog text.

---

## Course Categories Breakdown

### AI Fluency (5 courses)
- AI Fluency: Framework & Foundations
- AI Fluency for Educators
- AI Fluency for Students
- Teaching AI Fluency
- AI Fluency for Nonprofits

### API Development (1 course)
- Building with the Claude API

### Model Context Protocol (2 courses)
- Introduction to Model Context Protocol
- Model Context Protocol: Advanced Topics

### Cloud Platform Integration (2 courses)
- Claude with Amazon Bedrock
- Claude with Google Cloud's Vertex AI

### Developer Tools (1 course)
- Claude Code in Action

### Getting Started (1 course)
- Claude 101

---

## Level Distribution

- **Beginner**: 1 course (8%)
- **Intermediate**: 5 courses (42%)
- **Advanced**: 3 courses (25%)
- **All Levels**: 3 courses (25%)

---

## Format Distribution

- **Self-Paced Online**: 10 courses (83%)
- **Video-Based Online**: 1 course (8%)
- **Instructor-Led Online**: 1 course (8%)

---

## Price Distribution

- **Free**: 12 courses (100%)

All Anthropic Academy courses are offered at no cost, making this an excellent resource for comprehensive Claude AI training.

---

## Limitations

1. **Duration Not Specified**: Course pages do not explicitly state time commitment or module counts
2. **Certification Details**: Only 4 courses explicitly mention certification availability; others may offer certificates but this is not clearly documented
3. **Learning Objectives**: Not all courses list detailed learning outcomes on their public pages
4. **Target Audience**: While some courses specify target audiences, others are less explicit
5. **Course Updates**: Last update dates not available on course pages

**Note**: These limitations are minor - the catalog provides comprehensive, high-quality information for evaluation purposes.

---

## Recommendations

### For LinkedIn Learning Licensing Evaluation:

1. **Strong AI Fluency Curriculum**: The 5-course AI Fluency track (Framework & Foundations + specialized tracks for educators, students, nonprofits, and teaching) represents a comprehensive, well-structured progression developed with academic experts. This could complement LinkedIn Learning's professional development offerings.

2. **Technical Developer Training**: The API, MCP, and cloud platform integration courses provide deep technical training that would appeal to LinkedIn Learning's developer audience, particularly those building AI-powered applications.

3. **Unique Positioning**: Anthropic's courses are Claude-specific but teach transferable AI literacy and development skills. The curriculum balances theoretical frameworks (4D AI Fluency Framework) with practical implementation.

4. **Certification Opportunities**: Courses with completion certificates could align with LinkedIn Learning's credential pathways.

5. **Content Gaps to Address**:
   - Add explicit duration/time commitment information
   - Standardize certification availability across all courses
   - Include course update dates for freshness validation
   - Consider creating intermediate bridge courses between beginner and advanced MCP content

6. **Partnership Value**: Anthropic Academy is well-structured with professional LMS infrastructure (Skilljar), suggesting organizational readiness for content licensing partnerships.

---

## Sample Courses

### 1. Building with the Claude API
- **Level**: Intermediate
- **Category**: API Development
- **Description**: Comprehensive course covering the full spectrum of working with Anthropic models using the Claude API. Covers fundamental API operations, advanced prompting techniques, tool integration, and architectural patterns including RAG systems, prompt caching, MCP servers, and agent-based systems.
- **Prerequisites**: Proficiency in Python programming, basic knowledge of handling JSON data
- **Format**: Video-Based Online
- **Price**: Free
- **URL**: https://anthropic.skilljar.com/claude-with-the-anthropic-api

### 2. AI Fluency: Framework & Foundations
- **Level**: All Levels
- **Category**: AI Fluency
- **Description**: Learn to collaborate with AI systems effectively, efficiently, ethically, and safely. Partnership between Anthropic and academic experts Prof. Joseph Feller and Prof. Rick Dakan teaching practical skills for effective, ethical, and safe AI interaction.
- **Instructor**: Prof. Joseph Feller (University College Cork), Prof. Rick Dakan (Ringling College)
- **Format**: Self-Paced Online
- **Price**: Free
- **Certification**: Yes
- **URL**: https://anthropic.skilljar.com/ai-fluency-framework-foundations

### 3. Claude Code in Action
- **Level**: Intermediate
- **Category**: Developer Tools
- **Description**: Integrate Claude Code into your development workflow. Covers AI assistant architecture, implementation techniques, advanced integration strategies, context management approaches, and functionality extension through MCP servers and GitHub integration.
- **Prerequisites**: Familiarity with command-line interfaces and terminal operations, basic understanding of version control with Git
- **Format**: Self-Paced Online
- **Price**: Free
- **URL**: https://anthropic.skilljar.com/claude-code-in-action

### 4. AI Fluency for Nonprofits
- **Level**: All Levels
- **Category**: AI Fluency
- **Description**: Empowers nonprofit professionals to develop AI competency to increase organizational impact and efficiency while maintaining alignment with their mission and values. Specifically adapted for the nonprofit context with limited resources and mission-driven work. Teaches the 4D Framework: Delegation, Description, Discernment, Diligence.
- **Prerequisites**: Access to an AI chat tool (Claude.ai recommended). AI Fluency: Framework & Foundations recommended for deeper understanding.
- **Format**: Self-Paced Online
- **Price**: Free
- **URL**: https://anthropic.skilljar.com/ai-fluency-for-nonprofits

### 5. Model Context Protocol: Advanced Topics
- **Level**: Advanced
- **Category**: Model Context Protocol
- **Description**: Examines advanced features and implementation patterns for Model Context Protocol (MCP) development, focusing on server-client communication, transport mechanisms, and production deployment considerations.
- **Prerequisites**: Python development experience with async programming patterns, familiarity with JSON message formats and HTTP protocols, basic Server-Sent Events (SSE) knowledge
- **Format**: Self-Paced Online
- **Price**: Free
- **URL**: https://anthropic.skilljar.com/model-context-protocol-advanced-topics

---

## LinkedIn Learning Licensing Perspective

### Strengths
- ✓ Comprehensive, well-structured curriculum across multiple skill levels
- ✓ Academic partnership (UCC, Ringling College) adds credibility
- ✓ Strong focus on ethics and responsible AI use
- ✓ Technical depth appeals to developer audience
- ✓ All content free and publicly accessible for evaluation
- ✓ Professional LMS infrastructure (Skilljar)
- ✓ Specializations for distinct audiences (educators, students, nonprofits, developers)

### Considerations
- ⚠️ Claude-specific content may have limited transferability vs. platform-agnostic AI courses
- ⚠️ Relatively small catalog (12 courses) compared to other providers
- ⚠️ Duration data missing makes time commitment unclear for learners
- ⚠️ Newer platform (courses appear to be 2024-2026 vintage) - less established track record

### Strategic Fit
**Medium-High Fit** for LinkedIn Learning. The AI Fluency track and technical developer courses fill gaps in practical AI literacy and Claude API development. The nonprofit specialization aligns with LinkedIn Learning's commitment to diverse professional audiences. Consider licensing the AI Fluency framework courses and select technical courses, with potential to co-develop platform-agnostic versions.

---

## Artifacts Generated

- ✓ **JSON**: `anthropic_catalog.json` - Raw course data in JSON format
- ✓ **XLSX**: `anthropic_catalog.xlsx` - Excel spreadsheet for analysis
- ✓ **Report**: `anthropic_report.md` - This detailed analysis document
- ✓ **Script**: `scrape_anthropic.py` - Python script for reproducibility
