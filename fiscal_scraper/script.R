# Loading libraries
library(tidyverse)
library(pdftools)
library(httr)
library(janitor)
library(curl)

# Defining fiscal note dataframe
fiscal_df <- read_csv("documents.csv") %>%
  filter(document_desc == "Fiscal Note")

# Defining fiscal note URLs
fiscal_notes <- fiscal_df$state_link[1:10]

# Variables
labels <- c("State Gen. Fd.", "Agy. Self-Gen.", "Ded./Other", "Federal Funds", "Local Funds", "Annual Total")

# Years of interest
years <- c("2026-27", "2027-28", "2028-29", "2029-30", "2030-31", "5-YEAR TOTAL")

# Creating a temporary file
tmp <- tempfile(fileext = ".pdf")

# Parsing the text
parse_section <- function(text) {
  lines <- str_split(text, "\n")[[1]] %>%
    keep(~ str_detect(.x, paste(labels, collapse = "|")))
  
  map_dfr(lines, function(line) {
    label <- str_extract(line, paste(labels, collapse = "|"))
    values <- str_extract_all(line, r"(\$[\d,]+|SEE BELOW|INCREASE|DECREASE|INDETERMINATE)")[[1]]
    if (length(values) < length(years)) values <- c(values, rep("", length(years) - length(values)))
    set_names(as.list(c(label, values[seq_len(length(years))])), c("Category", years))
  })
}

# Results list
all_results <- list()

# Loop through all URLs
for (i in seq_along(fiscal_notes)) {
  url <- fiscal_notes[i]
  
  tryCatch({
    message(sprintf("[%d/%d] Processing: %s", i, length(fiscal_notes), url))
    
    # Download PDF
    curl_download(url, tmp, handle = new_handle(useragent = "Mozilla/5.0"))
    
    # Extract text
    text <- pdf_text(tmp) %>% paste(collapse = "\n")
    
    # Getting the expenditure and revenue text
    exp_text <- str_match(text, regex("EXPENDITURES(.+?)REVENUES", dotall = TRUE))[, 2]
    rev_text <- str_match(text, regex("REVENUES(.+?)EXPENDITURE EXPLANATION", dotall = TRUE))[, 2]
    
    # Convert to dataframes
    expenditures <- parse_section(exp_text)
    revenues <- parse_section(rev_text)
    
    print(expenditures)
    print(revenues)
    
    # Store results
    all_results[[url]] <- list(expenditures = expenditures, revenues = revenues)
    
  }, error = function(e) {
    message(sprintf("  ERROR on URL %d (%s): %s", i, url, conditionMessage(e)))
  })
}
