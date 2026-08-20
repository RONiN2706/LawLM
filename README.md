# Legal Case RAG Pipeline
Streams an indian case laws dataset from Huggingface one row at a time, keeps only
cases from six target courts, chunks and embeds them, and stores them 
in a local Chroma vector store that Gemini API can query.

## Setup
```bash
python -m venv venv
source venv/bin/activate     
pip install -r requirements.txt
```

## Run
```bash
python build_index.py
```


| Court | Quota |
|---|---|
| Supreme Court of India | 5000 |
| Bombay High Court | 2000 |
| Calcutta High Court | 2000 |
| High Court of Delhi | 2000 |
| Madras High Court | 2000 |
| High Court of Karnataka | 2000 |

Filtered cases are chunked, embedded with `all-MiniLM-L6-v2`, and written to
`./data/chroma_db`. A `./data/filtered_cases.jsonl` audit log lists every
case that was kept. The end-of-run printout shows actual vs. target count
per court

Basic Sanity Check:
```bash
python query.py "was the accused granted bail pending appeal"
```

## Note:
This dataset has **NO** detailed judgement text column — `indexable_text`
is a short auto-generated summary of the case details, not the opinion itself.
The real text lives in the PDF/JSON behind `source_pdf_s3_url` /
`source_json_s3_url` on S3. If you want the chatbot to retrieve the actual text
from the PDF, use `pypdf`/`pdfplumber` to extract the text then run it through the chunker. 
**CAUTION:** might fry your pc
