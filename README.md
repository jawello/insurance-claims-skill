# insurance-claims

A Claude Code skill for preparing MetLife Cyprus health insurance reimbursement claims from scanned documents.

The agent cleans and sorts scans, reconciles amounts, downloads and fills the numbered claim form, builds PDF packages and drafts the email. You scan the documents, review the result and send it yourself.

It works only with the MetLife Cyprus group claim form.

## Install

```bash
git clone https://github.com/jawello/insurance-claims-skill ~/.claude/skills/insurance-claims
pip install -r ~/.claude/skills/insurance-claims/requirements.txt
playwright install chromium
```

Connect Google Drive with [rclone](https://rclone.org/drive/). Run `rclone config` in your own terminal, not through the agent, because it prints the token. Name the remote `gdrive`. rclone's shared client ID is being retired, so [create your own client ID](https://rclone.org/drive/#making-your-own-client-id).

Attaching files to Gmail drafts needs the Gmail connector and Claude in Chrome.

Then ask Claude Code something like: "prepare a claim from the scans in this folder".

## What's inside

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Workflow and rules |
| `scripts/process.py` | Cleans scans and photos |
| `scripts/download_form.py` | Downloads a fresh numbered form from the MetLife site |
| `scripts/fill_form.py` | Fills the form from JSON and rejects values too long for a field |
| `scripts/build_pdfs.py` | Builds PDFs and a full package with bookmarks |
| `references/metlife-cyprus.md` | MetLife Cyprus addresses and form quirks |

## Status

The workflow comes from real claims, but the packaged skill has not yet been run end to end on a new case. Check every form and amount before sending. This is not insurance or legal advice.

## License

MIT
