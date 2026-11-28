# Partial Source Evaluation

## World Bank

The official CSV ZIP endpoints were used for `SP.POP.TOTL` and `NY.GDP.MKTP.CD`. Each ZIP, metadata CSV, and API data CSV was retained under `data/raw/` and registered.

Observed defects:
- The raw CSV begins with four metadata lines, so `skiprows: 4` is required.
- A trailing `Unnamed: 70` column appeared in both downloaded data CSVs and was removed from interim wide tables.
- Both downloaded files contain 266 rows and 70 columns after removing the trailing empty column.
- Regional and global aggregate entities are mixed with countries, including `WLD`.
- Population 1960 is missing for 2 rows.
- GDP 2024 is missing for 18 rows.
- The World Bank series starts at 1960, while the games index includes pre-1960 held Games.

## Wikipedia Medal Tables

TODO after R3 delivers scraped medal tables.

## REST Countries

TODO after R2 delivers country codes and regional metadata.
