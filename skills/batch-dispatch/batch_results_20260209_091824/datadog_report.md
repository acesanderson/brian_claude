# DataDog Catalog Scraping Report

**Date**: 2026-02-09
**URL**: https://learn.datadoghq.com/collections
**Total Courses**: 82

## Architecture
- **Type**: Single Page (all courses on one page)
- **Data Source**: Server-rendered HTML
- **Platform**: Thinkific LMS
- **Obstacles**: None (publicly accessible)

## Extraction Method

DataDog's Learning Center uses the Thinkific platform with a straightforward single-page course catalog. Courses are rendered as `<a>` elements with class `card card--published`, each containing:

- **Title**: Extracted from `h3.card__name`
- **URL**: From the card's `href` attribute
- **Description**: From `p.card__description`

The scraping strategy used:
1. HTTP GET request to the collections page
2. BeautifulSoup HTML parsing
3. Find all `a.card.card--published` elements
4. Extract metadata from each card's child elements
5. No pagination required (all 82 courses on one page)

## Data Quality

| Field | Completeness | Notes |
|-------|-------------|-------|
| **Title** | 100% | Avg length: 43 chars, all within acceptable range |
| **Description** | 100% | 100% unique - high quality course-specific descriptions |
| **URL** | 100% | All URLs follow pattern: `/courses/{slug}` |
| **Duration** | 0% | Not displayed on catalog page |
| **Level** | 0% | Not displayed on catalog page |
| **Price** | 100% | All courses are free (inferred) |
| **Format** | 100% | All on-demand (inferred) |
| **Category** | 0% | Not displayed on catalog page |

**Title Quality Check**: PASSED - Average title length of 43 characters is well within acceptable range. No titles exceed 150 characters.

**Description Quality Check**: PASSED - 100% unique descriptions. Each course has a specific, meaningful description explaining what the course covers.

## Course Distribution

### Topic Areas (based on titles)

- **Cloud Platforms**: AWS, Google Cloud, Kubernetes (15+ courses)
- **Security**: Application Security, Workload Protection, Threat Detection (8+ courses)
- **Observability**: APM, Logs, Metrics, Monitoring (20+ courses)
- **AI/ML**: LLM Observability, Tracing LLM Applications (3+ courses)
- **Automation**: Workflow Automation, CI/CD (5+ courses)
- **Platform Features**: Dashboards, Notebooks, SLOs (10+ courses)
- **Integrations**: AWS, GCP, Kubernetes, Serverless (15+ courses)

### Key Strengths

1. **Comprehensive cloud coverage**: Strong focus on AWS, GCP, and Kubernetes
2. **Modern tech**: Multiple courses on LLM/AI observability
3. **Security focus**: Robust security monitoring and protection courses
4. **Hands-on approach**: Many "Getting Started" courses for quick onboarding
5. **Free access**: All courses available at no cost

## Limitations

1. **Metadata gaps**: Duration, level, and category not available on catalog page
2. **Supplementary data**: Would require visiting individual course pages to get:
   - Lesson count
   - Estimated completion time
   - Prerequisites
   - Learning objectives
   - Certification information

## Recommendations

### For LinkedIn Learning Licensing Evaluation

**Strengths for LinkedIn Learning**:
- High-quality, vendor-specific training on a leading observability platform
- Strong alignment with DevOps, SRE, and cloud engineering roles
- Modern content covering AI/ML observability trends
- Well-structured "Getting Started" courses for different personas
- Free access reduces licensing complexity

**Considerations**:
- Vendor-specific (DataDog only) - not general observability training
- Limited metadata makes it harder to match to LinkedIn's taxonomy
- Would need to assess if DataDog's brand aligns with LinkedIn's content strategy
- May compete with existing observability/monitoring courses

**Suggested Next Steps**:
1. Sample 5-10 individual course pages to extract full metadata
2. Evaluate course quality and production value
3. Assess overlap with existing LinkedIn Learning observability content
4. Determine if partnership/licensing with DataDog is strategically aligned

## Sample Courses

### 1. Getting Started with Test Optimization
- **URL**: https://learn.datadoghq.com/courses/getting-started-test-optimization
- **Description**: NEW! Accelerate your CI pipelines by implementing Datadog Test Optimization. Set up test monitoring, identify flaky tests, and leverage Test Impact Analysis to run only the tests that matter.
- **Format**: On-Demand
- **Price**: Free

### 2. Tracing LLM Applications
- **URL**: https://learn.datadoghq.com/courses/llm-obs-tracing-llm-applications
- **Description**: Trace key operations for end-to-end-visibility in multi-step pipelines. Visualize execution flows in complex LLM chains. Debug failures and understand model behavior using detailed traces, contextual annotations, and performance metrics.
- **Format**: On-Demand
- **Price**: Free

### 3. Getting Started with Kubernetes Observability
- **URL**: https://learn.datadoghq.com/courses/getting-started-k8s
- **Description**: Simplify Kubernetes observability with Datadog. Navigate the Kubernetes Explorer, analyze pod details, and diagnose cluster issues using metrics and events.
- **Format**: On-Demand
- **Price**: Free

### 4. Detect Web Application Attacks with App & API Protection
- **URL**: https://learn.datadoghq.com/courses/detect-app-attacks
- **Description**: Detect and investigate attacks on web apps and APIs. Configure Application Threat Management, analyze attack patterns in the Trace & Attack Explorer, identify vulnerabilities, and review security signals and trends.
- **Format**: On-Demand
- **Price**: Free

### 5. Getting Started with Infrastructure and Cloud Network Monitoring
- **URL**: https://learn.datadoghq.com/courses/getting-started-infra-cnm
- **Description**: Monitor cloud infrastructure and network traffic with Datadog. Configure the Datadog Agent, create host maps, filter using tags, set up monitors, analyze network flows, and troubleshoot cloud connectivity issues.
- **Format**: On-Demand
- **Price**: Free

## Technical Notes

- Scraper completed successfully without authentication
- All 82 courses extracted in single HTTP request
- No rate limiting or anti-scraping measures encountered
- Thinkific platform uses clean, semantic HTML - easy to parse
- Course descriptions are well-written and course-specific (not generic marketing text)
