# Combined GitHub Contributions Heatmap

This repository builds a **combined contributions heatmap** by summing public activity from two accounts and publishes an SVG that you can embed in your profile README.

### How it works
- A GitHub Action runs daily and calls the GraphQL API for both usernames.
- It merges daily counts and writes `assets/combined-heatmap.svg`.
- The workflow commits the updated SVG back to the repo.

### Quick start
1. Create a new repository under your personal account (e.g., `contrib-combined`).
2. Copy these files into that repo (preserve folders).
3. Commit and push.
4. No secrets needed — it uses the default `GITHUB_TOKEN` for public data.

To customize user handles, edit the `USER_1` and `USER_2` env vars in `.github/workflows/combined-heatmap.yml`.

### Embed in your profile README
Add this snippet to your `ramkiran55/ramkiran55` README:

```md
### Combined activity from @ramkiran55 + @rdevireddybloom

![Combined contributions](https://raw.githubusercontent.com/<YOUR_USERNAME>/<YOUR_REPO>/main/assets/combined-heatmap.svg)
```

> Notes:
> - This is a **visual aid** for your profile. GitHub’s official contribution graph will still show each account separately.
> - Only public activity is included. Private repo activity remains anonymized in GitHub’s native graph if you enable it in settings.
