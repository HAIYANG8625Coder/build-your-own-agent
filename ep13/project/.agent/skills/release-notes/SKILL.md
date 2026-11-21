---
name: release-notes
description: Write release notes for a new shop version. Use when asked for release notes, a changelog entry, or what changed in a version.
---
Release notes follow one fixed format, so the support team can parse them.

1. Read the commit list (CHANGES.txt). The first line says "Release date: YYYY-MM-DD" and the version.
2. Skip every commit that starts with "chore:". They are not shown to customers.
3. Turn each remaining commit into one item:
   - "fix:" becomes the tag FIX, "feat:" becomes NEW, "change:", "refactor:" and "perf:" become CHG.
   - The item text is the commit message after the colon, starting with a capital letter, with no full stop at the end.
   - Keep the issue number in brackets at the end, as written in the commit, for example (#41).
4. Write the file RELEASE_NOTES.md exactly like this:
   - first line: RELEASE <version> (<release date>)
   - then a blank line
   - then the items, one per line, each as: * [TAG] text (#number)
   - items sorted by tag in this order: FIX first, then NEW, then CHG; inside a tag keep the order of CHANGES.txt
   - then a blank line and the last line: -- end of release --
5. Do not add headings, bold text or any other lines.
6. After writing the file, read it back and check each line against these rules. Say how many items it has.

Example for version 0.9:
RELEASE 0.9 (2026-03-02)

* [FIX] Round the total to two decimals (#7)
* [NEW] Add a coupon field (#9)
* [CHG] Move the tax table to its own file (#8)

-- end of release --
