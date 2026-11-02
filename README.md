# insurance-claims

A Claude Code skill for preparing MetLife Cyprus health insurance reimbursement claims from scanned documents.

The agent cleans and sorts scans, reconciles amounts, fills the claim form, builds PDF packages and drafts the email. You scan the documents, download the numbered form, review the result and send it yourself.

It works only with the MetLife Cyprus group claim form.

## Install

```bash
git clone https://github.com/jawello/insurance-claims-skill ~/.claude/skills/insurance-claims
pip install -r ~/.claude/skills/insurance-claims/requirements.txt
```

Then ask Claude Code something like: "prepare a claim from the scans in this folder".

## What's inside

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Workflow and rules |
| `scripts/process.py` | Cleans scans and photos |
| `scripts/fill_form.py` | Fills the form from JSON and rejects values too long for a field |
| `scripts/build_pdfs.py` | Builds PDFs and a full package with bookmarks |
| `references/metlife-cyprus.md` | MetLife Cyprus addresses and form quirks |

## Status

The workflow comes from real claims, but the packaged skill has not yet been run end to end on a new case. Check every form and amount before sending. This is not insurance or legal advice.

## License

MIT
