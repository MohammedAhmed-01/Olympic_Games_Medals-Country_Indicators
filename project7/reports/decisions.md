# Decisions

- The personal twist range is unknown, so `twist.games_range.start` and `.end` remain `null`. `games_index.csv` contains all Summer Games and is generated with all held Games in scope until the range is supplied.
- The scraper contact email is unknown, so `scraper.user_agent` contains an explicit placeholder rather than a fabricated address.
- World Bank official API bulk CSV endpoints were used: `https://api.worldbank.org/v2/country/all/indicator/{indicator}?downloadformat=csv`.
- `--sample N` keeps the first N country rows in interim outputs while the raw ZIP and extracted CSV remain complete.
- The 1906 Games are marked `intercalated`; 1916, 1940, and 1944 are marked `cancelled`.
