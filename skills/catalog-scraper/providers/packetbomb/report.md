# PacketBomb Catalog Scraping Report

**Date**: 2026-02-17
**URL**: https://www.packetbomb.com
**Total Courses**: 18

## Architecture
- Type: Navigation-based (category pages)
- Data Source: Server-rendered HTML
- Obstacles: None (all content freely accessible)

## Extraction Method
Navigated category archive pages (/category/tutorial/, /category/case-study/, /category/text/) to enumerate all content items, then fetched individual pages to extract course-specific metadata.

## Data Quality
- Title: 100% complete (avg length: ~57 chars, 0 titles >150 chars)
- Description: 100% complete (100% unique - all course-specific)
- Duration: 6% complete (only 1 item had explicit duration)
- Level: 100% complete (inferred from content complexity)
- Price: 100% complete (all Free)

## Limitations
- PacketBomb is a free tutorial/blog site, not a structured course platform
- No formal course duration metadata - content is video tutorials and text articles
- Level is inferred, not explicitly stated on the site
- Some video content has supplementary newsletter-subscriber-only material
- Site appears to have stopped publishing new content (most recent posts appear to be several years old)
- 18 total items across 3 content categories (6 tutorials, 6 case studies, 6 text articles)

## Recommendations
- Low licensing value: informal blog/tutorial format rather than structured courses
- All content is by a single author (Kary Rogers) - niche packet analysis focus
- Free content with no certification - limited differentiation for LinkedIn Learning
- Small catalog (18 items) with no apparent growth

## Sample Courses

1. **How to Do TCP Sequence Number Analysis**
   - URL: https://packetbomb.com/how-to-do-tcp-sequence-number-analysis/
   - Format: Video | Level: Intermediate | Category: Tutorial
   - Description: Demonstrates practical TCP sequence number analysis techniques in Wireshark, covering sequence numbers, ACK behavior, and interpreting Wireshark expert info.

2. **Troubleshooting a One-Way Performance Issue**
   - URL: https://packetbomb.com/troubleshooting-a-one-way-performance-issue/
   - Format: Video | Level: Advanced | Category: Case Study
   - Description: Case study examining how to diagnose asymmetrical network performance problems using packet analysis.

3. **How Can the Packet Size Be Greater than the MTU?**
   - URL: https://packetbomb.com/how-can-the-packet-size-be-greater-than-the-mtu/
   - Format: Text | Level: Intermediate | Category: Text
   - Description: Explains why Wireshark captures show packets exceeding the 1500-byte MTU, covering TCP Segmentation Offload and Large Receive Offload.

4. **How to Hack a Cisco Router ACL**
   - URL: https://packetbomb.com/how-to-hack-a-cisco-router-acl/
   - Format: Video | Level: Advanced | Duration: 17 min | Category: Tutorial
   - Description: Demonstrates how to bypass Cisco router ACL protections by manipulating TCP flags using divert sockets.

5. **Solving Tomcat Throughput Issues on Windows**
   - URL: https://packetbomb.com/solving-tomcat-throughput-issues-on-windows/
   - Format: Video | Level: Advanced | Category: Case Study
   - Description: Real-world case study examining poor Tomcat file download performance on Windows 2008R2, showing how delayed ACK behavior and small send buffers bottleneck throughput.
