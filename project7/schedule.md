# Scheduled Pipeline Runs

Run the offline pipeline once per week. Network settings and retries are read from `config.yaml`.

## Windows Task Scheduler

```powershell
python -m src.pipeline --offline
```

Use the project root as the working directory, run weekly, and on failure retry five times.

## Cron

```cron
0 9 * * 1 cd /path/to/project7 && python -m src.pipeline --offline
```
