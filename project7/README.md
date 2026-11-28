# Project 7: Olympic Games Medals & Country Indicators

## 1. Project Overview

## 2. Data Sources

- World Bank population: `SP.POP.TOTL`
- World Bank GDP: `NY.GDP.MKTP.CD`
- Wikipedia Summer Olympics medal tables
- REST Countries API

## 3. Setup and Reproduction

## 4. Pipeline Usage

```powershell
python -m src.pipeline --help
python -m src.pipeline --offline --stage ingest
python -m src.pipeline --download --sample 10 --stage ingest
python -m src.pipeline --offline
```

`--sample N` is a downloader convention: `N` keeps only the first N country rows in interim files; `None` means the full raw download is processed.

## 5. Data Dictionary

## 6. Validation

## 7. Results and Figures

## 8. Team Roles and Contributions
