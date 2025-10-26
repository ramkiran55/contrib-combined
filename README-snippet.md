# Combined GitHub Contributions Heatmap (All-Time)

This repository builds an **all-time combined contributions heatmap** by summing public daily contributions from two accounts and rendering a year-by-year SVG (every day since account creation is included).

### How it works
- A GitHub Action runs on a schedule or on demand.
- It fetches account creation dates for both users, then iterates year-sized windows across their entire history via the GraphQL API.
- Daily counts are merged and rendered into `assets/combined-heatmap.svg` with one calendar block per year.

### Setup
1. Create a new repository under your personal account (e.g., `contrib-combined`).
2. Copy these files into that repo.
3. Commit and push. The workflow uses the default `GITHUB_TOKEN`; no extra secrets needed for public data.

Environment variables (tweak in workflow if desired):
- `USER_1`, `USER_2` — GitHub handles to combine
- `OUTPUT_PATH` — path for the SVG (default `assets/combined-heatmap.svg`)
- `CELL_SIZE`, `CELL_GAP` — adjust square size/gap if you have many years

### Embed in your profile README
```md
### Combined activity from @ramkiran55 + @rdevireddybloom (all-time)

![Combined contributions](https://raw.githubusercontent.com/<YOUR_USERNAME>/<YOUR_REPO>/main/assets/combined-heatmap.svg)
```

> Notes
> - GitHub’s native profile graph only shows ~1 year; this custom SVG renders **all-time**.
> - Only public contributions are included. Private repo activity remains anonymized within GitHub’s native graph if enabled in your settings.
