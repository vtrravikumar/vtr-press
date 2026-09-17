# Table Markdown Policy

Table extraction is intentionally conservative.

1. The original scanned page remains authoritative.
2. Detected grid coordinates are used to create cell regions.
3. Each cell may be OCR'd independently through the existing OCR adapter.
4. OCR text is retained as a reviewable intermediate result.
5. Markdown conversion is gated by completeness and an explicit confidence threshold.
6. The current extractor does not infer merged cells or semantic headers. The first row is treated as a Markdown header only when the caller explicitly permits serialization.
7. If OCR confidence is unavailable, the default policy does **not** publish the table as Markdown; the source image and review marker remain the safe representation.
8. OCR text is escaped for Markdown syntax but is not silently corrected or modernized.

This policy prevents a visually detected table from becoming a misleading semantic table merely because its grid was detected successfully.
