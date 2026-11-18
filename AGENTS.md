# Rules
- Run the app with: uv run streamlit run app.py
- Run the tests with: uv run pytest
- Do not run git commands. Git is handled in GitHub Desktop.
- Before finishing a task, run the tests and paste the output.
- Never edit files in tests/ unless the task says so.
- Never create or edit .env files or other files with secrets.

# Design
- Before changing any screen, widget or styling, read docs/design.md and follow it.
- All styling goes in design.py (CSS and HTML helpers) and .streamlit/config.toml (theme). Never add <style> blocks in other files.
- Every user-visible text needs English, Portuguese, French and German versions, like the existing screens.
- If you change a design rule, update docs/design.md in the same task.
