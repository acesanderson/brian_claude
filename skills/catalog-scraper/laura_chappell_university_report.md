# Laura Chappell University Catalog Scraping Report

**Date**: 2026-02-17
**URL**: https://www.chappell-university.com
**Total Courses/Products**: 14

## Architecture
- Type: Wix Thunderbolt (JavaScript-rendered SPA)
- Data Source: og:title / og:description meta tags from known pages
- Obstacles: All course content rendered via JavaScript; static HTML contains only page skeleton

## Extraction Method
1. Explored sitemap.xml to enumerate all site pages (92 pages discovered from Wix page registry embedded in JS)
2. Identified course/product-relevant pages from page titles and URIs
3. Fetched each relevant page and extracted og:title + og:description meta tags
4. Supplemented with known catalog structure from public web search data

## Data Quality
- Title: 100% complete (avg length: 29 chars)
- Description: 57% complete (100% unique)
- Duration: 0% complete (requires JS rendering or authenticated access)
- Level: ~50% complete (manually assigned based on page context)
- Price: ~60% complete (subscription/paid noted where visible)

## Limitations
- Wix JavaScript rendering: The full course video library within "All Access Pass" subscription
  is not accessible without a headless browser and authenticated session
- The online-classes page (https://www.chappell-university.com/online-classes) showed no og:description,
  suggesting it may require login to view course listings
- Individual video/lesson count inside subscription plans is unknown without browser rendering
- Books vs. courses distinction: Some products are physical/digital books, not video courses

## Provider Summary
Laura Chappell University is the training platform of Laura Chappell, founder of Protocol Analysis
Institute and renowned Wireshark trainer. The platform focuses on:
- Wireshark network analysis (primary focus)
- Packet capture and protocol analysis
- Network troubleshooting
- WCNA (Wireshark Certified Network Analyst) exam preparation
Primary offering is an "All Access Pass" subscription giving access to all video courses,
supplemented by books/study guides sold individually.

## Categories
- Subscription / All Courses: 1
- Online Courses: 1
- Wireshark / Network Analysis: 4
- Network Troubleshooting: 1
- WCNA Certification: 3
- Live Training: 1
- Lab / Practice: 2
- Virtual Events: 1

## Recommendations
- Use Playwright/Selenium to render the All Access Pass course catalog page with authentication
- Obtain trial subscription to enumerate full video library
- Primary LinkedIn Learning relevance: Wireshark, network analysis, packet capture (niche but high-quality)

## Sample Courses

### Chappell University | All Access Pass
- URL: https://www.chappell-university.com/all-access-pass
- Category: Subscription / All Courses
- Format: On-Demand
- Price: Subscription
- Description: Sign up for the All Access Pass to get all of Laura's classes. Earn badges in Key Skills, Forensics, and Troubleshooting.

### Online Classes
- URL: https://www.chappell-university.com/online-classes
- Category: Online Courses
- Format: On-Demand
- Price: 
- Description: N/A

### Chappell University | Wireshark 101 Book
- URL: https://www.chappell-university.com/wireshark101-2ndedition
- Category: Wireshark / Network Analysis
- Format: Book
- Price: Paid
- Description: This book is based on the most common Wireshark questions and over 20 years of experience analyzing networks and teaching analysis skills. 

### Chappell University | Troubleshooting With Wireshark Book
- URL: https://www.chappell-university.com/troubleshooting
- Category: Network Troubleshooting
- Format: Book
- Price: Paid
- Description: This book focuses techniques used to identify symptoms and determine causes of lousy network performance using Wireshark.

### Chappell University | WCNA Study Guide
- URL: https://www.chappell-university.com/studyguide
- Category: WCNA Certification
- Format: Book
- Price: Paid
- Description: This book is the Official Study Guide for the Wireshark Certified Network Analyst (WCNA) program. This Second Edition includes an introduction to IPv6, ICMPv6 and DHCPv6 analysis, updated Wireshark fu

