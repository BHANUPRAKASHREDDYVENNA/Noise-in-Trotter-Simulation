# Security Policy

## Scope

Security reports should cover this repository's Python code, benchmark execution paths, CI configuration and dependency handling.

## Reporting

Do not publish credentials, tokens or exploit details in public issues. Use the repository owner's supported private GitHub security-reporting mechanism.

## Engineering rules

- Validate configuration before numerical execution.
- Avoid dynamic code execution.
- Keep GitHub Actions permissions to the minimum required.
- Treat organizer Challenge Kit files as input data, never as executable content.
- Do not commit secrets or local environment files.
