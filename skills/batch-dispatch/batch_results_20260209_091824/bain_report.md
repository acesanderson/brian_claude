# Bain & Company Catalog Scraping Report

**Date**: 2026-02-09
**URLs**:
- https://www.bain.com/bain-academy/
- https://www.npsx.com/

**Total Courses**: 22

## Architecture

- **Type**: Manual compilation from multiple public sources
- **Data Source**: Web scraping and documentation review
- **Obstacles**:
  - No centralized public course catalog with detailed listings
  - Bain Academy courses are custom/enterprise offerings without public pricing
  - NPSx website was temporarily inaccessible (connection refused)
  - Course details compiled from marketing pages and press releases

## Extraction Method

Due to the lack of a structured public catalog, data was compiled through:

1. **Bain Academy Programs** (15 courses):
   - Masterclass program areas extracted from Ceros interactive brochure
   - Leadership development programs from marketing pages
   - Data represents program areas rather than individual courses
   - Each "Masterclass" is actually a category containing multiple customizable sessions

2. **NPSx Certification Programs** (7 courses):
   - Seven CX certificate programs identified from press releases
   - Course durations obtained from public documentation
   - Individual course URLs unavailable due to site connectivity issues
   - Used general NPSx programs page as primary URL

## Data Quality

**Completeness:**
- Title: 100% (22/22 courses)
- Description: 100% (22/22 - all course-specific)
- Duration: 100% (22/22)
- Level: 100% (22/22)
- Format: 100% (22/22)
- Price: 100% (22/22 - Custom or Subscription model)
- Category: 100% (22/22)
- URL: 100% (22/22 - category pages, not individual course pages)
- Certification: 100% (22/22)

**Quality Metrics:**
- Average title length: 33 characters ✓
- Titles >150 characters: 0 ✓
- Description uniqueness: 100% ✓
- All descriptions are course-specific ✓

## Bain Training Platform Overview

### Bain Academy
Professional consulting and leadership training for corporate clients:
- **Delivery**: Custom, enterprise-focused programs
- **Pricing**: Not publicly listed (requires consultation)
- **Format**: Live, virtual, and blended learning
- **Audience**: C-suite executives, senior leaders, mid-career professionals
- **Scale**: 50,000+ learners trained

### NPSx by Bain
Customer experience certification platform (launched 2022):
- **Delivery**: Self-paced online courses
- **Pricing**: Subscription model (MyCX)
- **Format**: 1-4 hour courses with videos, case studies, interactive exercises
- **Audience**: CX practitioners and teams
- **Certification**: Bain-certified CX practitioner credential

## Limitations

1. **Bain Academy Specificity**: The catalog captures program areas rather than individual course offerings. Each "Masterclass" represents a category containing multiple customizable modules and sessions.

2. **No Individual Course URLs**: Bain Academy does not publish individual course landing pages. All courses link to category pages.

3. **Custom Pricing**: Bain Academy programs are enterprise-focused with custom pricing. No public pricing information available.

4. **NPSx Access Issues**: The NPSx website (npsx.com) experienced connection issues during scraping, limiting access to detailed course metadata.

5. **Dynamic Content**: Bain Academy emphasizes customization, meaning actual course content varies by client engagement.

## Recommendations

### For LinkedIn Learning Licensing Evaluation:

**Bain Academy Programs:**
- **Low licensing potential**: These are high-touch, custom consulting engagements rather than off-the-shelf courses
- Programs require Bain consultant facilitation
- Pricing model is enterprise/custom, not per-learner
- Content is heavily customized per client
- **Recommendation**: Not suitable for LinkedIn Learning licensing

**NPSx Certification Programs:**
- **Moderate licensing potential**: Self-paced, standardized online courses
- Already productized with consistent content
- Clear certification pathway
- Approximately 15-20 hours of total content (7 courses)
- **Challenges**:
  - Small catalog (7 courses)
  - Niche focus (CX/NPS specific)
  - Bain has existing subscription model (MyCX)
- **Recommendation**: Possible licensing opportunity if Bain is interested in broader distribution, but catalog size is limited

### To Improve This Catalog:

1. **Contact Bain Academy directly** (bainacademy@bain.com) to request:
   - Detailed course catalog with specific module/session titles
   - Learning objectives for each program
   - Typical duration breakdowns
   - Prerequisites and target audience details

2. **Access NPSx platform** through subscription or demo:
   - Get individual course landing pages
   - Extract detailed learning objectives
   - Document assessment/quiz structure
   - Review certification requirements

3. **Explore Bain's Ignite platform**: Digital skills training platform mentioned but not publicly accessible

## Sample Courses

### 1. Artificial Intelligence Masterclass
- **Provider**: Bain Academy
- **Level**: Executive
- **Format**: Live/Virtual/Blended
- **Duration**: Multi-day to single module
- **Description**: Grasp AI fundamentals, business impact, and transformation strategies while leveraging AI for productivity and organizational change leadership
- **Price**: Custom (Enterprise)
- **Category**: Technology & Innovation

### 2. Leadership Development Program for C-Suite Executives
- **Provider**: Bain Academy
- **Level**: C-Suite
- **Format**: Live/Virtual Blended
- **Duration**: Multi-day, multi-session
- **Description**: Multi-day, multi-session program focused on developing emerging C-suite talent with emphasis on effective team building, value-driven leadership, and change management
- **Price**: Custom (Enterprise)
- **Category**: Leadership

### 3. Winning on Purpose: CX and NPS Fundamentals
- **Provider**: NPSx by Bain
- **Level**: All Levels
- **Format**: Self-Paced Online
- **Duration**: 3.5-4.5 hours
- **Description**: Learn the fundamentals of customer experience and Net Promoter Score methodology, covering the principles of winning through customer-centric business practices
- **Price**: Subscription (MyCX)
- **Category**: Customer Experience
- **Certification**: Yes

### 4. Customer Experience Design
- **Provider**: NPSx by Bain
- **Level**: All Levels
- **Format**: Self-Paced Online
- **Duration**: 1.5-2.5 hours
- **Description**: Design exceptional customer experiences through journey mapping, touchpoint optimization, and experience innovation methodologies
- **Price**: Subscription (MyCX)
- **Category**: Customer Experience
- **Certification**: Yes

### 5. Strategy & Transformation Masterclass
- **Provider**: Bain Academy
- **Level**: Executive
- **Format**: Live/Virtual/Blended
- **Duration**: Multi-day to single module
- **Description**: Bain's proprietary strategic methodology instruction, including organizational founder principles, tactical micro-battles, adaptive strategy execution, and implementation delivery
- **Price**: Custom (Enterprise)
- **Category**: Strategy

## Content Analysis

### By Category:
- **Customer Experience**: 8 courses (36%)
- **Leadership**: 5 courses (23%)
- **Technology & Innovation**: 2 courses (9%)
- **Strategy**: 2 courses (9%)
- **Other**: 5 courses (23%) - Operations, Sales, PE, Sustainability, etc.

### By Level:
- **Executive/C-Suite**: 13 courses (59%)
- **All Levels**: 7 courses (32%)
- **Mid-Career/Mid-Level**: 2 courses (9%)

### By Format:
- **Live/Virtual/Blended**: 15 courses (68%)
- **Self-Paced Online**: 7 courses (32%)

### By Price Model:
- **Custom (Enterprise)**: 15 courses (68%)
- **Subscription**: 7 courses (32%)

## LinkedIn Learning Licensing Perspective

**Overall Assessment**: Limited licensing potential

**Strengths:**
- Strong brand reputation (Bain & Company)
- Executive-level content
- Proprietary methodologies (NPS, RAPID decision-making)
- NPSx courses are already productized

**Weaknesses:**
- Small standardized course catalog (only 7 self-paced courses)
- Primary business model is custom consulting, not course licensing
- Enterprise-focused with high-touch delivery requirements
- Niche focus (mostly CX and executive leadership)
- Existing distribution channel (MyCX subscription)

**Recommendation**: Not a priority for LinkedIn Learning licensing unless Bain expresses interest in creating standardized versions of their Masterclass content.
