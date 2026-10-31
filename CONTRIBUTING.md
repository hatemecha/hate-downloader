# Contributing to Hate Downloader

Thanks for helping improve the project. Keep changes focused: one problem, one understandable
patch, and evidence that existing users still work.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Before submitting a change, run:

```bash
ruff check .
pytest -q
python run.py --self-test
```

Packaging changes should also pass `python scripts/build_exe.py` on the affected OS. PyInstaller
cannot cross-compile. Use Python 3.10.11 or newer for packaging; 3.10.0 hits a bytecode bug in
PyInstaller.

## Patch expectations

- Explain the user-visible problem and how to reproduce it.
- Add or update tests for behavior changes.
- Preserve current settings, database migrations, command entry points, and download workflows.
- Avoid unrelated formatting, speculative abstractions, and new dependencies without a concrete
  benefit.
- Never commit cookies, downloaded media, databases, logs, API tokens, or personal data.
- Keep third-party license notices when adding code or assets.

The project is maintainer-led. Discussion and patches are welcome, but the maintainer makes final
scope, design, and release decisions. Support and review time are best-effort.

## Security reports

Do not put credentials, cookies, private URLs, or exploit details in a public issue. The project
does not yet publish a private security-reporting address; non-sensitive hardening bugs can use the
normal issue tracker.
