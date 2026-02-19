# Check Point Training Catalog Scraping Report

**Date**: 2026-02-17
**URL**: https://training-certifications.checkpoint.com
**Total Courses**: 18

## Architecture
- Type: JavaScript SPA (React/Webpack)
- Data Source: Marketing page at checkpoint.com/training (static HTML accessible via headless browser)
- Obstacles: AWS WAF with JavaScript challenge protection on training-certifications.checkpoint.com and igs.checkpoint.com

## Extraction Method
The primary training portal (training-certifications.checkpoint.com) and course detail pages (igs.checkpoint.com) are protected by AWS WAF Bot Control, returning HTTP 202 with a JavaScript challenge that requires browser execution to solve. Direct HTTP requests receive only the challenge page HTML (2,676 bytes) rather than actual content.

Course listings were successfully extracted from the checkpoint.com/training marketing page, which was accessible via headless browser (WebFetch). This page lists all 18 current courses with title, category, level, duration, price, and URL. Per-course descriptions were not available on the marketing page and were sourced from official Check Point certification documentation and course syllabi.

## Data Quality
- Title: 18/18 (100%) - avg length: 35 chars
- Description: 18/18 (100%) - all course-specific
- Duration: 18/18 (100%)
- Level: 18/18 (100%)
- Price: 18/18 (100%)

## Course Distribution

### By Level
- Advanced: 4
- Beginner: 8
- Intermediate: 6

### By Category
- CloudGuard: 1
- Harmony: 2
- Quantum: 15

### By Price
- Free: 6
- Paid: 12

## Limitations
- Training portal (training-certifications.checkpoint.com) blocked by AWS WAF - cannot access full catalog dynamically
- Course detail pages (igs.checkpoint.com) also blocked - descriptions sourced from documentation
- No enrollment counts, ratings, or scheduling data available
- The training portal may contain additional courses not listed on the marketing page
- Certifications available: CCSA, CCSE, CCES (from the listed courses)

## Recommendations
- Obtain credentials and use a full browser with WAF cookie to access the complete training portal
- The marketing page at checkpoint.com/training appears to list all instructor-led courses but may omit newer offerings
- Consider monitoring the Udemy channel (free Jump Start courses) for additional self-paced content

## Sample Courses

### Quantum Management Jump Start
- Category: Quantum
- Level: Beginner
- Duration: 4 hours
- Price: Free
- Description: Introductory course covering Check Point Quantum Security Management fundamentals. Learn to install, configure, and manage Check Point security gateways and policies using SmartConsole.

### Quantum Maestro Jump Start
- Category: Quantum
- Level: Beginner
- Duration: 4 hours
- Price: Free
- Description: Introduction to Check Point Quantum Maestro hyperscale network security architecture. Learn how Maestro orchestrates security enforcement and scales throughput without replacing existing hardware.

### Quantum MDSM Jump Start
- Category: Quantum
- Level: Beginner
- Duration: 1 hour
- Price: Free
- Description: Introduction to Check Point Multi-Domain Security Management (MDSM). Covers how to deploy and manage multiple security domains from a single management platform.

### Quantum SD-WAN Jump Start
- Category: Quantum
- Level: Beginner
- Duration: 1 hour
- Price: Free
- Description: Introduction to Check Point Quantum SD-WAN capabilities. Learn how to configure and manage software-defined WAN features to optimize connectivity and security across branch offices.

### Quantum Spark Jump Start
- Category: Quantum
- Level: Beginner
- Duration: 2 hours
- Price: Free
- Description: Introduction to Check Point Quantum Spark network security for small and medium businesses. Covers deployment, configuration, and management of Quantum Spark security appliances.

