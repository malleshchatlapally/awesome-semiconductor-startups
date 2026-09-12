# KTR X messages agent

Small CLI agent that fetches and prints recent posts from K. T. Rama Rao’s X accounts using the **official X API v2** (reliable; scraping X from cloud/datacenter IPs is usually blocked).

## Default accounts

| Handle | Role |
|--------|------|
| [@KTRBRS](https://x.com/KTRBRS) | Personal account |
| [@KTRoffice](https://x.com/KTRoffice) | Office account |

Override with `--handle` or the `KTR_HANDLES` environment variable (comma-separated).

## Setup

1. Create a [developer app](https://developer.x.com/) and copy the **Bearer Token** (app-only auth is enough for public timelines).
2. Install dependencies:

   ```bash
   cd ktr-x-agent
   pip install -r requirements.txt
   ```

3. Export your token:

   ```bash
   export X_BEARER_TOKEN='your_token_here'
   ```

## Usage

Human-readable feed (both default accounts, 10 posts each):

```bash
python -m ktr_x_agent
```

JSON for automations or dashboards:

```bash
python -m ktr_x_agent --json --limit 5
```

Single account:

```bash
python -m ktr_x_agent --handle KTRBRS --limit 20
```

## Cursor Cloud Agent / scheduled checks

Run this script on a schedule (cron, GitHub Action, or a Cursor timer subscription) and post the JSON output wherever you need it (Slack, email, internal dashboard). This repo does not store your API token; keep `X_BEARER_TOKEN` in your environment secrets.

## Note on this repository

The parent project is a semiconductor startups list. This folder is a standalone utility; consider moving it to its own repository if you use it long term.
