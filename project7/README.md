# Project 7: Olympic Games Medals & Country Indicators

## Question

## Sources

- Wikipedia Summer Olympics medal tables
- World Bank population (`SP.POP.TOTL`) and GDP (`NY.GDP.MKTP.CD`)
- REST Countries API

## How to run

Install the pinned dependencies, then run from the `project7` directory:

```powershell
python -m pip install -r requirements.txt
python -m src.pipeline --help
python -m src.pipeline --offline --stage ingest
python -m src.pipeline --download --sample 10 --stage ingest
```

`--sample N` means each downloader processes the first N country rows in its interim output; None means the full dataset. Raw downloads remain complete.

## Row counts

## Key cleaning decisions

## Figures

## Limitations

## Team roles
