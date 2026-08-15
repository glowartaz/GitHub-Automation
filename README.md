# GitHub Trending Video Researcher

An autonomous, security-conscious Python pipeline that turns never-before-featured GitHub
Trending repositories into a daily faceless-YouTube research package.

## What it produces

Every daily run creates:

- A researched JSON record for each repository
- Plain-English explanations, setup steps, requirements, costs, and creator highlights
- Downloaded README/demo images with source and attribution records
- A countdown video script and narration file
- Title, description, chapter, visual, and thumbnail suggestions
- A machine-readable manifest and daily summary

The application **never executes code from a researched repository**.

## Permanent duplicate prevention

`data/featured-repos.json` is the permanent append-only history. A repository is blocked when
either its permanent GitHub `node_id` or the source repository ID of its fork has appeared
before. Names are checked as an additional fallback. This catches renames, ownership transfers,
and forks of previously featured projects.

If ten new repositories are unavailable, the system produces fewer than ten. It never fills a
slot with a duplicate.

Do not delete or rewrite the history file after production begins. Back it up with the Git
repository.

## Quick start

Requirements: Python 3.11 or newer, a GitHub account, and an OpenAI API key.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
export OPENAI_API_KEY="your-key"
github-trending-video --dry-run
```

Use `--no-llm` for a limited, no-cost deterministic report. This mode is intended for testing;
it cannot reliably explain complex repositories.

```bash
github-trending-video --no-llm --dry-run
```

Other options:

```text
--config config.json   Load configuration
--run-id YYYY-MM-DD    Choose the output folder identifier
--skip-images          Disable media downloads
--verbose              Enable detailed logs
```

Copy `config.example.json` to `config.json` to customize limits or Trending language pages. The
overall daily page is ranked first; common language pages expand the pool when previously
featured projects would otherwise leave fewer than ten unique candidates.

## GitHub setup

1. Create a private GitHub repository and add this project.
2. Open **Settings → Secrets and variables → Actions**.
3. Create the repository secret `OPENAI_API_KEY`.
4. Optionally create the repository variable `OPENAI_MODEL`.
5. Open **Actions**, select the daily workflow, and run it manually once.

The workflow runs at 6:00 AM Arizona time, uploads the complete video package as a 30-day
artifact, and commits only the permanent duplicate-history file. Change the cron expression in
`.github/workflows/daily.yml` if desired.

If branch protection prevents the workflow from pushing history, allow GitHub Actions to push
to the branch or change the workflow to open a pull request. Persistent history is required for
the no-duplicates guarantee.

## Output layout

```text
output/YYYY-MM-DD/
├── daily-summary.json
├── manifest.json
├── video-script.md
├── narration.txt
├── title-options.txt
├── description.md
├── chapters.txt
├── thumbnail-ideas.md
└── repos/
    └── 01-owner--repository/
        ├── research.json
        ├── segment-script.txt
        └── images/
```

## Cost behavior

The software itself is open source. GitHub Actions is normally covered by the included allowance
for a small daily job. LLM cost depends on the selected model and README sizes. Use provider
spending limits and usage alerts. Exact external API prices are not invented: the report marks
unverified costs for manual review.

## Security controls

- Repository code is never cloned, installed, imported, or executed.
- README text is treated as untrusted input and cannot override the analysis instructions.
- Image downloads default to an explicit GitHub-owned hostname allowlist.
- Redirect destinations, MIME types, and maximum byte sizes are validated.
- README and supporting-file sizes are capped before LLM submission.
- GitHub and OpenAI tokens come only from environment variables or encrypted Actions secrets.
- Logs do not print credentials or full request headers.
- A concurrency lock prevents overlapping local or scheduled runs.
- History is written atomically only after successful package generation.

README images and creator avatars may have separate copyright or trademark restrictions. Every
asset is marked `review-required`; review commercial-use rights before publishing a video.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
```

The Trending page has no official public API and its HTML can change. Parser tests use a saved
minimal fixture so markup changes can be diagnosed without consuming API calls.
