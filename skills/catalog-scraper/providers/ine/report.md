# INE (InterNetwork Expert) Catalog Scraping Report

**Date**: 2026-02-17
**URL**: https://ine.com/pages/training
**Total Items**: 833 (764 courses + 69 learning paths)

## Architecture
- Type: JavaScript SPA (Vue.js) on my.ine.com
- Data Source: Algolia search API (credentials embedded in app.js bundle)
- Obstacles: None
- Algolia App ID: 6D0ROPGFEB
- Courses Index: prod_ine-content-api-courses
- Learning Paths Index: prod_ine-content-api-learning-paths

## Extraction Method
Extracted public Algolia API credentials from the my.ine.com Vue.js SPA bundle
(app.277068a0ba8260ef.js). Used Algolia browse API to retrieve all records from
the courses and learning paths indexes without pagination limits.

## Data Quality
- Description: 99% complete
- Duration: 99% complete
- Level: 100% complete

## Content by Category
- Networking: 370
- Cyber Security: 223
- Cloud: 152
- Data Science: 47
- IT Essentials: 37
- Development: 2
- Unknown: 2

## Sample Courses

### Intelligence in Threat Hunting
- **URL**: https://my.ine.com/course/intelligence-in-threat-hunting-new/0a7ea767-0848-4906-baf5-e08c9c710f07
- **Category**: Cyber Security
- **Level**: Advanced
- **Duration**: 5.1h
- **Format**: On-Demand
- **Description**: Start your journey with Intelligence in Threat Hunting, an engaging and practical course designed to deepen your understanding of cyber threat intelligence in modern defense strategies. This course ex

### SOC Ticketing & Reporting
- **URL**: https://my.ine.com/course/soc-ticketing-reporting/7f70e83f-52fe-4234-a19d-e4acb30c5c43
- **Category**: Cyber Security
- **Level**: Beginner
- **Duration**: 3.6h
- **Format**: On-Demand
- **Description**: SOC Ticketing & Reporting introduces you to the essential processes used to track, manage, and communicate security incidents within a Security Operations Center. You'll learn how to document findings

### SOC Tools & Technology
- **URL**: https://my.ine.com/course/soc-tools-technology/f17b01e7-3479-4080-bc33-bb0ae70039e9
- **Category**: Cyber Security
- **Level**: Beginner
- **Duration**: 10.5h
- **Format**: On-Demand
- **Description**: SOC Tools & Technology provides a hands-on introduction to the key platforms and systems used in today’s Security Operations Centers. You’ll explore the core functions of SIEMs, endpoint detection too

### Critical Thinking for IT & Cybersecurity
- **URL**: https://my.ine.com/course/critical-thinking-for-it-cybersecurity/5759db4e-6830-4003-acb6-a20d810eb348
- **Category**: Cloud
- **Level**: Beginner
- **Duration**: 3.0h
- **Format**: On-Demand
- **Description**: Start your journey with Critical Thinking for IT & Cybersecurity, an engaging course designed to build foundational thinking skills for new professionals. You’ll explore why critical thinking is essen

### Offensive AI: Generative AI for Pentesters
- **URL**: https://my.ine.com/course/offensive-ai-leveraging-artificial-intelligence-in-penetration-testing/562f35fb-a7df-4abb-a57b-cece5ba2ae6a
- **Category**: Cyber Security
- **Level**: Beginner
- **Duration**: 4.7h
- **Format**: On-Demand
- **Description**: Generative AI for Pentesters is designed for penetration testers, red teamers, and security practitioners looking to integrate generative AI safely and effectively into real-world offensive security w

## Limitations
- Course content (videos) requires active INE subscription
- Some courses may require specific subscription tiers (starter vs premium)
- Learning path membership details not included

## Recommendations
- Strong cybersecurity and networking content; consider for LinkedIn Learning licensing
- Rich hands-on lab catalog (separate labs index not scraped here)
- Content aligns well with technical/IT professional audience
