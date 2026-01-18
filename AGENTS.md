# Repository Guidelines

## Project Structure & Module Organization
- `frd.md` contains the core requirements specification for the RMS project.
- This repository currently holds documentation only; there are no source, test, or asset directories yet.
- If code is added later, keep it in a clear top-level folder such as `src/` with supporting docs in `docs/`.

## Build, Test, and Development Commands
- No build, test, or run commands are defined at this time.
- If you introduce tooling, document the exact commands here (for example: `npm test`, `make build`) and what they do.

## Coding Style & Naming Conventions
- Documentation edits should be plain Markdown with consistent heading levels and short paragraphs.
- Use English headings and keep section titles descriptive (for example: "Traceability" or "Workflow Statuses").
- Prefer UTF-8 encoding for all text files to avoid character corruption.

## Testing Guidelines
- There is no test suite in this repository.
- If you add tests later, document the framework, naming pattern (for example: `*_test.ext`), and how to run them.

## Commit & Pull Request Guidelines
- No Git repository or commit history is present here, so no conventions can be inferred.
- If this repository is initialized with Git, use clear, imperative commit messages (for example: "Add traceability matrix section").
- For pull requests, include a short summary, list of changes, and links to related requirements.

## Documentation Maintenance Tips
- Keep requirements numbered and stable; if you renumber, note the change in a short changelog section.
- When adding diagrams, store images alongside the document and reference them with relative paths.