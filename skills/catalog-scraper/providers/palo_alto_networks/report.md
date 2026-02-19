# Palo Alto Networks Catalog Scraping Report

**Date**: 2026-02-17
**URL**: https://learn.paloaltonetworks.com/
**Total Courses/Certifications**: 27

## Architecture

- **LMS Platform**: Docebo (learn.paloaltonetworks.com / dcbstatic.com CDN)
- **Type**: JavaScript Single-Page Application (Angular/Docebo framework)
- **Data Source**: Public course listing pages on paloaltonetworks.com
- **Obstacles**: Docebo REST API returns 403 Forbidden without authentication token. All `/learn/v1/` endpoints require a valid session. The frontend loads via JavaScript after initial page load, making direct HTML scraping of the LMS catalog impossible without a browser.

## Extraction Method

Strategy E (Partial Manual Documentation with automated HTML scraping of public marketing pages):

1. Discovered the LMS is Docebo-based via `dcbstatic.com` CDN references in page source
2. Probed Docebo REST API (`/learn/v1/catalog`, `/learn/v1/courses`) - all return HTTP 403
3. Fell back to scraping public course listing pages on `www.paloaltonetworks.com`:
   - `/services/education/ilt` - Instructor-Led Training courses
   - `/services/education/certification` - Certification programs
4. Compiled 12 ILT courses and 15 certification programs

## Data Quality

- **Title**: 100% complete (avg length ~51 chars, 0 titles >150 chars)
- **Description**: 100% complete, 27/27 unique (100%)
- **Duration**: 0% (not publicly available without authentication)
- **Level**: 55% complete
- **Price**: 100% complete (ILT=Paid, Certifications=Paid)
- **Category**: 100% complete

## Limitations

1. **Auth wall**: Full course catalog on `learn.paloaltonetworks.com` requires user account login. The Docebo API returns 403 on all catalog endpoints without a valid session token.
2. **Free digital learning modules** are advertised but accessible only after login - not captured here.
3. **Course durations** are not available from public pages.
4. **Course codes**: EDU-210 and EDU-330 were captured; others are not publicly listed.
5. **Total course count unknown**: The LMS may contain hundreds more e-learning modules.

## Recommendations

- Obtain a Palo Alto Networks learning account (free registration available) to access the full Docebo catalog via authenticated API calls
- The Docebo API endpoint `/learn/v1/catalog` with a Bearer token would return the complete course catalog in JSON format

## Breakdown by Category

- Network Security: 15 courses
- Security Operations: 11 courses
- Cloud Security: 1 courses

## Format Breakdown

- Instructor-Led Training: 12
- Certification Programs: 15

## Sample Courses

### Firewall Essentials: Configuration and Management
- **Category**: Network Security
- **Format**: Instructor-Led
- **Level**: 
- **Price**: Paid
- **Description**: Designed to help students configure and manage the essential features of Palo Alto Networks next-generation firewalls.

### Firewall: Troubleshooting
- **Category**: Network Security
- **Format**: Instructor-Led
- **Level**: 
- **Price**: Paid
- **Description**: Designed to help students understand how to troubleshoot the full line of Palo Alto Networks next-generation firewalls.

### Panorama: NGFW Management
- **Category**: Network Security
- **Format**: Instructor-Led
- **Level**: 
- **Price**: Paid
- **Description**: Designed to help students gain in-depth knowledge about configuring and managing Next-Generation Firewalls using the Palo Alto Networks Panorama management server.

### Panorama: Centralized Network Security Administration
- **Category**: Network Security
- **Format**: Instructor-Led
- **Level**: 
- **Price**: Paid
- **Description**: Designed to help students gain an introduction to configuring and managing Next-Generation Firewalls and Prisma Access using the Palo Alto Networks Panorama management server.

### Prisma SD-WAN: Design and Operation
- **Category**: Network Security
- **Format**: Instructor-Led
- **Level**: 
- **Price**: Paid
- **Description**: Designed to help students learn how to design, implement, and effectively operate a Prisma SD-WAN solution.

