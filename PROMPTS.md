# AI Prompt Log — TrustVault

This file records how AI assistance was used during development. The entries describe the actual development process, corrections, and verification status.

## Entry 1 — 2026-10-23 — Project setup

- **Prompt:** I need help setting up a Flask project in VS Code on Windows for my TrustVault application.
- **AI output:** Guidance for installing Flask, creating a project folder, and organizing application files.
- **What was wrong or unclear:** Installing Flask alone did not create a project folder or populate the VS Code Explorer.
- **What I did:** I created/opened the TrustVault folder and organized the application files.
- **Related commit:** Add the actual commit URL after committing this log.

## Entry 2 — 2026-10-23 — Document authorization

- **Prompt:** Help me implement document downloads so only an administrator, the document owner, or a user with explicit sharing permission can download a document.
- **AI output:** Guidance for checking the current user's role, ownership, and permission before serving a file.
- **What I verified or changed:** Record the exact code changes you made and whether you tested an unauthorized download. Do not claim a test passed unless you ran it.
- **Related commit:** Add the actual commit URL after committing this log.

## Entry 3 — 2026-10-23 — Audit trail

- **Prompt:** Help me record document access and denied-access events in an audit log.
- **AI output:** Guidance for storing audit events and displaying them in an administrator-only audit page.
- **What I verified or changed:** I manually checked the audit history page. I still need to verify which events are recorded and whether unauthorized users are blocked from the page.
- **Related commit:** Add the actual commit URL after committing this log.

## Entry 4 — 2026-10-23 — Deployment

- **Prompt:** Help me deploy my Flask application to Render using Gunicorn and environment variables.
- **AI output:** Guidance for configuring the start command, dependencies, and secret key.
- **What was wrong or needed correction:** I needed to distinguish local configuration from Render environment settings and avoid exposing the secret key.
- **What I did:** I configured the Render service and replaced the exposed secret key with a newly generated one.
- **Related commit:** Add the actual commit URL after committing this log.

## Entry 5 — 2026-10-23 — Documentation and limitations

- **Prompt:** Help me document how to run TrustVault locally and identify its security risks and unfinished tests.
- **AI output:** Drafts for the README and threat model.
- **What I reviewed or changed:** I saved the documentation and recorded authorization tests and deployment persistence as limitations requiring attention.
- **Related commit:** Add the actual commit URL after committing this log.

