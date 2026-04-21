# Importing libraries
import urllib.request, fitz, re
import pandas as pd
import json

# Stripping unnecessary words
STRIP_PATTERNS = [
    r"CODING:\s+Words in struck through.*?are additions\.?",
    r"Page \d+ of \d+",
    r"type are deletions from existing law; words",
    r"struck through",
    r"underscored",
    r"are additions",
    r"are deletions from existing law; words in",
    r"The original instrument and the following digest, which constitutes no part of the legislative instrument, were prepared by"
]

# Defining if should be removed
def is_boilerplate(text):
    for pat in STRIP_PATTERNS:
        if re.search(pat, text, re.IGNORECASE | re.DOTALL):
            return True
    return False

# Defining line number
def is_line_number(word, x0, page_width):
    return word.strip().isdigit() and x0 < page_width * 0.15

# Defining a function to parse the bill
def parse_bill(url):
    # Fetching the PDF
    pdf = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    ).read()
    doc = fitz.open(stream=pdf, filetype="pdf")

    past_digest = False
    segments = []

    # Looping through pages in the document
    for page in doc:
        page_width = page.rect.width

        # Collecting horizontal drawn lines
        drawn_lines = []
        for p in page.get_drawings():
            for item in p["items"]:
                if item[0] == "l":
                    p1, p2 = item[1], item[2]
                    if abs(p1.y - p2.y) < 1:
                        drawn_lines.append((p1.x, p1.y, p2.x))
                elif item[0] == "re":
                    r = item[1]
                    if r.width > r.height and r.height <= 2:
                        drawn_lines.append((r.x0, (r.y0 + r.y1) / 2, r.x1))

        # Checking if a word has a line through or under it
        def classify_word(x0, y0, x1, y1):
            mid = y0 + (y1 - y0) * 0.6
            for lx0, ly, lx1 in drawn_lines:
                if lx0 > x1 or lx1 < x0:
                    continue
                if ly < y0 - 2 or ly > y1 + 4:
                    continue
                return "strikethrough" if ly < mid else "underline"
            return None

        words = page.get_text("words", sort=True)
        tagged = []
        for w in words:
            x0, y0, x1, y1, word = w[0], w[1], w[2], w[3], w[4]
            # Stopping at digest section
            if word.strip().upper() == "DIGEST":
                past_digest = True
            if past_digest:
                continue
            # Skipping header area
            if y0 < page.rect.height * 0.10:
                continue
            if is_line_number(word, x0, page_width):
                continue
            tag = classify_word(x0, y0, x1, y1)
            tagged.append((word, tag, y0, y1))

        # Estimating line height to group words into phrases
        heights = [y1 - y0 for _, _, y0, y1 in tagged if y1 - y0 > 0]
        line_height = (sum(heights) / len(heights) * 1.8) if heights else 20

        # Grouping consecutive same-tagged words into phrases
        i = 0
        while i < len(tagged):
            word, tag, y0, y1 = tagged[i]
            phrase = [word]
            prev_y1 = y1
            j = i + 1
            while j < len(tagged):
                nword, ntag, ny0, ny1 = tagged[j]
                if ntag != tag or ny0 - prev_y1 > line_height:
                    break
                phrase.append(nword)
                prev_y1 = ny1
                j += 1
            text = " ".join(phrase)
            # Tagging and appending each segment
            if not is_boilerplate(text):
                if tag == "underline":
                    segments.append({"order": len(segments) + 1, "text": text, "tag": "added"})
                elif tag == "strikethrough":
                    segments.append({"order": len(segments) + 1, "text": text, "tag": "removed"})
                else:
                    segments.append({"order": len(segments) + 1, "text": text, "tag": "present"})
            i = j

    return segments

# # Parsing a bill
bill = parse_bill("https://legis.la.gov/legis/ViewDocument.aspx?d=1448258")
# 
# # Printing all segments
for segment in bill:
  print(f"[{segment['tag'].upper()}] {segment['text']}")
# 
# # Filtering to added/removed/present
# removed = [s["text"] for s in bill if s["tag"] == "added"]
# 

# --------------------------- Looping Through Texts ----------------------------

df = pd.read_csv("documents_text.csv")
urls = df[df.document_desc == "Introduced"].document_url







all_bills = {}

for i, url in enumerate(urls):
    try:
        all_bills[url] = parse_bill(url)
        print(f"{i+1}/{len(urls)} done")
    except Exception as e:
        print(f"{i+1}/{len(urls)} failed: {url} — {e}")
        all_bills[url] = None
    
    # Saving every 50 bills
    if (i + 1) % 50 == 0:
        with open("all_bills.json", "w") as f:
            json.dump(all_bills, f)

# Saving all results
with open("all_bills.json", "w") as f:
    json.dump(all_bills, f)
  

# ------------------------- Reading in Data ------------------------------------
import os

os.makedirs("bill_texts", exist_ok=True)

for url, segments in all_bills.items():
    if segments is None:
        continue
    
    # Make a safe filename from URL
    filename = url.split("d=")[-1]  # grabs document ID
    filepath = f"bill_texts/{filename}.txt"
    
    with open(filepath, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"[{seg['tag'].upper()}] {seg['text']}\n")

print("Done!")
