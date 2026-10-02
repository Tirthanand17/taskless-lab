# Privacy Guardrails

These are release-blocking rules.

## Never publish or embed

- personal legal name;
- personal email address;
- personal phone number;
- home/work/school address or precise location;
- photos or voice samples of the account owner;
- education or employment history;
- account IDs, payment details, API keys, tokens or credentials;
- private files, private conversations, resumes, applications or client data;
- metadata that identifies the account owner.

## Brand-only public identity

Public assets may use only the neutral brand identity **TaskLess Lab** and generic contact placeholders until a separate brand contact channel is explicitly authorized.

## Automated checks

Every release manifest is scanned for:
- email-like strings;
- phone-number patterns;
- likely credentials/secrets;
- banned personal identifiers configured in `config/privacy.json`.

A failed privacy scan blocks release.

## Human-account boundary

GitHub project automation may be built and run.

YouTube/Google account creation, OAuth authorization, payment setup, tax/AdSense setup, identity verification, and other personal-account steps stay disabled until explicit permission is given for that exact account action.
