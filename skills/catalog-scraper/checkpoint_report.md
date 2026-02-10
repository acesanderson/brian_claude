# Check Point Catalog Scraping Report

**Date**: 2026-02-10
**URL**: https://www.checkpoint.com/services/training/
**Total Courses**: 18

## Architecture
- **Type**: Single page with tabbed sections (navigation-based by product line)
- **Data Source**: Server-rendered HTML tables embedded in tab panes
- **Obstacles**: None - fully accessible without authentication

## Extraction Method

The Check Point training page uses a tabbed interface organizing courses by product line (Quantum, CloudGuard, Harmony). Each tab contains an HTML table with course metadata.

**Strategy**: Static HTML scraping with BeautifulSoup
- Parse tab panes by ID to identify product categories
- Extract course data from table rows (`<tr>` with 6 `<td>` cells)
- Map table columns to metadata fields:
  - Column 0: Title with link to course URL
  - Column 1: Duration (e.g., "4H", "2D")
  - Column 2: Price (Free/Paid)
  - Column 3: Language
  - Column 4: Skill level (Beginner/Intermediate/Advanced)

## Data Quality

| Field | Completeness | Notes |
|-------|-------------|-------|
| Title | 100% | Average length: 35 characters - appropriately concise |
| URL | 100% | Mix of Udemy, YouTube, and Check Point IGS portal links |
| Description | 0% | Not available on landing page - would require visiting individual course pages |
| Duration | 100% | Format: "XH" (hours) or "XD" (days) |
| Level | 100% | Beginner or Intermediate |
| Price | 100% | Free or Paid (no specific pricing shown for paid courses) |
| Category | 100% | Derived from tab pane: Quantum (15), CloudGuard (1), Harmony (2) |
| Language | 100% | All courses are in English |
| Format | 100% | Inferred: Self-Paced (free courses) vs Instructor-Led (paid) |

**Title Quality**: ✓ Excellent - all titles are concise (avg 35 chars, none >150)

**Description Quality**: ℹ️  Not available on landing page - acceptable limitation for this catalog type

## Course Distribution

### By Category
- **Quantum**: 15 courses (83%)
  - Focus on firewall, security gateway, and network security
  - Mix of Jump Start (beginner) and certification courses
- **CloudGuard**: 1 course (6%)
  - Cloud security specialist certification
- **Harmony**: 2 courses (11%)
  - Endpoint security focused

### By Price
- **Free**: 6 courses (33%)
  - All "Jump Start" courses on Udemy/YouTube
- **Paid**: 12 courses (67%)
  - Certification and specialist training via IGS portal

### By Level
- **Beginner**: 6 courses (33%)
  - All Jump Start courses
- **Intermediate**: 12 courses (67%)
  - Certification and specialist tracks

## Limitations

1. **No course descriptions**: The landing page displays only metadata in table format. Individual course descriptions would require:
   - Following links to Udemy/YouTube/IGS portal
   - Scraping individual course detail pages
   - This was not attempted to respect rate limits and avoid overwhelming external platforms

2. **Limited metadata on paid courses**: Paid courses show "Paid" but not specific pricing

3. **External hosting**: Courses are hosted across multiple platforms (Udemy, YouTube, Check Point IGS), making comprehensive scraping more complex

## Recommendations

1. **Accept current data**: The landing page provides sufficient metadata for catalog purposes (title, duration, level, price status, category)

2. **Enhance with descriptions (optional)**: If course-specific descriptions are needed:
   - For Udemy courses: Use Udemy API or scrape individual course pages
   - For IGS portal: Would likely require authentication to Check Point's training portal
   - For YouTube: Extract video descriptions from playlist links

3. **LinkedIn Learning licensing perspective**:
   - **Strong cybersecurity focus**: Check Point offers specialized training in network security, cloud security, and endpoint protection
   - **Certification pathways**: Multiple Check Point certification programs (CCSA, CCSE, CCES, etc.)
   - **Target audience**: IT security professionals, network administrators, security operations teams
   - **Competitive positioning**: Vendor-specific technical training (complements rather than competes with LinkedIn Learning's broader business/tech skills)
   - **Licensing potential**: Low - this is vendor certification training tied to Check Point products, not general skills training

## Sample Courses

### Quantum Management Jump Start
- **Duration**: 4H
- **Level**: Beginner
- **Price**: Free
- **Category**: Quantum
- **URL**: https://www.udemy.com/course/check-point-jump-start-quantum-management/

### Check Point Certified Admin (CCSA)
- **Duration**: 3D
- **Level**: Intermediate
- **Price**: Paid
- **Category**: Quantum
- **URL**: https://igs.checkpoint.com/courses/3001

### Check Point Certified Cloud Specialist
- **Duration**: 2D
- **Level**: Intermediate
- **Price**: Paid
- **Category**: CloudGuard
- **URL**: https://igs.checkpoint.com/courses/3110

### Harmony Endpoint Jump Start
- **Duration**: 2H
- **Level**: Beginner
- **Price**: Free
- **Category**: Harmony
- **URL**: https://www.udemy.com/course/check-point-jump-start-harmony-endpoint-security/

### Check Point Certified Expert (CCSE)
- **Duration**: 3D
- **Level**: Intermediate
- **Price**: Paid
- **Category**: Quantum
- **URL**: https://igs.checkpoint.com/courses/3002

## Conclusion

Successfully scraped 18 Check Point training courses from their public training landing page. The catalog is small but well-structured, focusing primarily on Quantum network security products. Data quality is high for available fields (100% completeness for title, URL, duration, level, price status, category, and language). Course descriptions are not available without visiting individual course pages across multiple hosting platforms (Udemy, YouTube, IGS).

From a LinkedIn Learning licensing perspective, this is vendor-specific certification training with low licensing potential, as it serves a specialized technical audience learning Check Point-specific tools rather than transferable business/tech skills.
