# Louisiana Legislative Tools
Scripts for scraping and analyzing Louisiana Legislative session documents.

## Scripts

### `bill_scraper/script.py`
Downloads Louisiana bill PDFs and parses them into tagged text segments, marking language as `added` (underlined), `removed` (strikethrough), or `present`. Outputs individual files in `bill_texts/`. Requires a `documents_text.csv` with bill URLs.

### `fiscal_scraper/script.R`
Downloads fiscal note PDFs and extracts expenditure and revenue tables by fund category. Requires a `documents.csv` with fiscal note URLs.

### `llm_extraction/script.py`
Uses GPT-4.1-nano to classify bills by whether they increase, extend, or create criminal penalties (jail time, fines, mandatory minimums, new crimes, etc.). Reads from `bill_texts/`, outputs flagged bills to `increase_bills.csv`.
