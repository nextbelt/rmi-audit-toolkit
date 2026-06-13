# Code Review Graph

[`code-review-graph`](https://github.com/tirth8205/code-review-graph) builds a
persistent Tree-sitter knowledge graph of this codebase and uses **blast-radius
analysis** to give an AI reviewer only the files a change actually touches —
median context reductions of ~82× tokens. It runs in three places here:

| Where | When | What it does |
|---|---|---|
| **GitHub Action** (`.github/workflows/code-review-graph.yml`) | every PR | Posts a sticky, risk-scored review comment scoped to the change's blast radius. |
| **Scheduled CI** | Mon & Thu 06:00 UTC + on demand | Rebuilds the graph and uploads it as an artifact so it never goes stale. |
| **Local post-commit hook** (`.githooks/post-commit`) | after each commit | Incrementally updates your local graph (`<2s`), detached so it never blocks the commit. |

## One-time setup

> **Install it in isolation with `pipx`, not into the app's virtualenv.**
> `code-review-graph` depends on a newer `fastapi`/`pydantic` than this app pins;
> installing it into `.venv` will break the backend. `pipx` gives it its own
> environment while still putting the `code-review-graph` command on your PATH.

```bash
# Install (Python 3.10+); isolated from the app venv
pipx install code-review-graph
# (no pipx? `python -m pip install --user pipx && pipx ensurepath` first)

# Enable the local post-commit auto-update hook
git config core.hooksPath .githooks

# Build the graph for the first time
code-review-graph build
```

CI installs it in its own job (`.github/workflows/code-review-graph.yml`), so the
app's pinned environment is never touched there either.

The local graph cache lives in `.code-review-graph/` (gitignored). Paths to skip
are in `.code-review-graphignore`.

## Everyday CLI

```bash
code-review-graph update                 # incremental refresh (the hook runs this)
code-review-graph status                 # graph stats + health
code-review-graph detect-changes --brief # risk-scored view of your working changes + token savings
code-review-graph visualize              # interactive D3.js HTML graph of the codebase
```

## Use it from Claude Code (MCP)

The tool exposes 30 MCP tools (impact radius, semantic search, change detection…).
Start the server and point Claude Code at it:

```bash
code-review-graph serve        # starts the MCP server
# or let the tool wire common clients automatically:
code-review-graph install --platform claude-code
```

Then in Claude Code you can ask for an impact-radius-aware review of the current
diff and it will pull just the affected nodes instead of reading the whole repo.

## Making it a hard merge gate (optional)

The PR action is advisory by default. To block merges on high risk, add to the
`Code Review Graph` step in the workflow:

```yaml
with:
  github-token: ${{ secrets.GITHUB_TOKEN }}
  fail-on-risk: high
```
