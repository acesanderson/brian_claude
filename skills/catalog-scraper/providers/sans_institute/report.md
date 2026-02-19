# SANS Institute Catalog Scraping Report

**Date**: 2026-02-17
**URL**: https://www.sans.org/cyber-security-courses/
**Total Courses**: 85

## Architecture
- Type: Single page with Algolia InstantSearch (paginated)
- Data Source: Algolia API (app ID: M2CVJC95IX, credentials embedded in Next.js RSC payload)
- Obstacles: None - credentials publicly embedded in page JS

## Extraction Method
Used Algolia REST API directly (`/1/indexes/course_single_page_listing_ranking_desc/query`) with the
public API key embedded in the Next.js server-side rendered page. Fetched all
courses in a single API request (100 per page), getting all 85 courses
across 1 API call.

## Data Quality
- Title: 100% complete (avg length: 54 chars, 0 titles >150 chars)
- Description: 100.0% complete (98.8% unique)
- Duration: based on contentHours + days fields
- Level: from facets.skillLevel
- Price: Paid (SANS courses are paid professional training)

## Breakdown by Skill Level
  - Intermediate: 34
  - Advanced: 30
  - Essentials: 17
  - Beginner: 4

## Breakdown by Focus Area
  - Offensive Operations: 18
  - Cyber Defense: 18
  - Cybersecurity Leadership: 17
  - Digital Forensics and Incident Response: 15
  - Cloud Security: 10
  - Artificial Intelligence: 9
  - Industrial Control Systems Security: 7

## Breakdown by Training Format
  - Self-Paced: 77
  - Virtual: 71
  - In-Person: 68

## Limitations
- Price is listed as "Paid" for all courses; actual pricing requires visiting individual course pages
- Some courses may have multiple skill levels listed

## Recommendations
- SANS Institute offers high-quality, advanced cybersecurity training
- Strong alignment with technical/professional development needs
- Courses have clear certifications (GIAC), CPE credits, and hands-on labs
- Good candidate for LinkedIn Learning licensing in cybersecurity domain

## Sample Courses

### SEC504: Hacker Tools, Techniques, and Incident Handling
- URL: https://www.sans.org/cyber-security-courses/hacker-techniques-incident-handling
- Level: Essentials
- Category: Offensive Operations
- Duration: 38 hours / 6 days
- Format: Self-Paced, In-Person, Virtual
- Certification: GIAC Certified Incident Handler Certification (GCIH)
- Description: Master real-world incident response through hands-on labs, AI-powered analysis, and attacker mindset training. AI doesn't change the need for expertise—it raises the bar for what expertise looks like....

### FOR508: Advanced Incident Response, Threat Hunting, and Digital Forensics
- URL: https://www.sans.org/cyber-security-courses/advanced-incident-response-threat-hunting-training
- Level: Intermediate
- Category: Digital Forensics and Incident Response
- Duration: 36 hours / 6 days
- Format: Self-Paced, In-Person, Virtual
- Certification: GIAC Certified Forensic Analyst (GCFA)
- Description: Learn the advanced incident response and threat hunting skills you need to identify, counter, and recover from a wide range of threats within enterprise networks....

### SEC401: Security Essentials - Network, Endpoint, and Cloud
- URL: https://www.sans.org/cyber-security-courses/security-essentials-network-endpoint-cloud
- Level: Essentials
- Category: Cyber Defense
- Duration: 46 hours / 6 days
- Format: Self-Paced, In-Person, Virtual
- Certification: GIAC Security Essentials (GSEC)
- Description: Gain essential cybersecurity skills to quickly detect, respond to, and remediate threats. Learn how to protect critical information and technology assets, whether on-premises or in the cloud....

### SEC275: Foundations: Computers, Technology, & Security
- URL: https://www.sans.org/cyber-security-courses/foundations
- Level: Beginner
- Category: Cyber Defense
- Duration: 38 hours
- Format: Self-Paced
- Certification: GIAC Foundational Cybersecurity Technologies (GFACT)
- Description: Build your cybersecurity confidence from the ground up. This SANS Foundations course gives you the essential skills, tools, and mindset to launch your journey into the world of cyber....

### SEC560: Enterprise Penetration Testing
- URL: https://www.sans.org/cyber-security-courses/enterprise-penetration-testing
- Level: Intermediate
- Category: Offensive Operations
- Duration: 36 hours / 6 days
- Format: Self-Paced, In-Person, Virtual
- Certification: GIAC Penetration Tester (GPEN)
- Description: Learn enterprise-scale penetration testing; identify, exploit, and assess real business risks across on-prem, Azure, and Entra ID environments through hands-on labs and an intensive CTF....

