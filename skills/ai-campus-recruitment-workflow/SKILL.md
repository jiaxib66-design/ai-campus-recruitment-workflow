---
name: ai-campus-recruitment-workflow
description: Manage a privacy-first, adaptive AI-assisted campus recruitment workflow in Chinese or English. Use when Codex needs to onboard a first-time or returning 秋招/校招 user from a resume or existing profile; discover target companies from named employers, a role or industry direction, or a preferred region; verify official campus roles; check hard requirements; score and prioritize roles; explain limited application-slot choices; review resume-to-JD evidence; draft open questions; maintain a local application tracker; or extract reviewable recruiting deadlines. Also use for natural-language requests about 岗位匹配、投递排序、简历匹配、网申开放题、投递追踪、测评、笔试或面试提醒.
---

# AI Campus Recruitment Workflow

Run a privacy-first, evidence-backed campus recruitment workflow. Keep the user in control of every login, CAPTCHA, final application, email connection, and calendar write.

## Start safely

1. Locate the user's private workspace. Never commit private profile, resume, tracker, mailbox data, credentials, or generated application content.
2. Ask once whether runtime information should remain conversation-only or may be stored in a user-selected private path. Initialize a private configuration only when the user chooses persistence.
3. Store user-provided test or real data only in the user-selected private workspace. Store disposable generated results only in an ignored output path. Never copy runtime data into this Skill, `examples/`, `config/`, `tests/`, or documentation.
4. Treat social posts, screenshots, aggregators, and chat messages as leads only. Prefer the employer's official recruiting site for all material facts.
5. Record source URLs, retrieval dates, and uncertainty. Do not invent a deadline, quota, eligibility rule, or JD detail.
6. Read `references/privacy-and-safety.md` before handling personal data or external accounts.

## Guide every run

Read `references/guided-workflow.md` for full-loop runs, user tests, first-time users, or whenever the user asks what to do next.

- Default to **run mode**: perform the recruitment workflow naturally without discussing Skill files, versions, or testing mechanics.
- Distinguish first-time users from returning users before collecting profile information. Prefer a resume for first-time onboarding; reuse a user-confirmed accessible profile for returning users and ask only what changed.
- After reading a resume, form tentative direction hypotheses and ask one or two adaptive follow-up rounds. Do not replace the conversation with a fixed questionnaire or decide preferences for the user.
- Route target discovery by what the user knows: named companies, a role/industry/region direction, or no clear target. Search for companies when the user provides constraints but no names.
- Guide one useful next action at a time. Use explicit stage labels only when they improve clarity; avoid repeating privacy or process boilerplate after the boundary is settled.
- Pause at every human checkpoint. Missing evidence remains unresolved; it is not permission to proceed by assumption.
- Enter **improvement mode** only when the user explicitly asks to record a workflow problem, change the Skill, or publish a new version. Obtain approval for the specific change before editing, then return to the interrupted recruitment step.

## Route the request

- For a full workflow, follow all stages below in order.
- For a company name, screenshot, post, or link, start at **Verify leads**.
- For role JSON already verified by the user, start at **Score and prioritize**.
- For resume or open-question help, start at **Assist the application**.
- For status changes, use **Track applications**.
- For recruiting email, read `references/email-extension.md` and use **Extract email deadlines**.

## Verify leads

1. Import text/CSV/JSON clues with `scripts/import_clues.py`. For screenshots, transcribe only relevant recruiting facts and label OCR uncertainty.
2. Search for the employer's official campus recruiting site. Verify cycle, graduation dates, deadline and timezone, shared quota, eligibility, and the full JD.
3. Save official URL, retrieval timestamp, and evidence. Keep the original lead URL separately.
4. Mark facts as `verified`, `unverified`, or `conflicting`. If official evidence is unavailable, keep it as a lead and state what remains unknown.
5. Never log in, solve a CAPTCHA, or submit an application without the user taking that action.

Use the role schema in `references/data-schema.md`. Do not treat search snippets or a third-party summary as official proof.

## Score and prioritize

1. Check hard requirements before computing preference scores. Missing evidence is `unknown`, not an automatic pass.
2. Run `scripts/score_roles.py --profile <private-profile.json> --roles <roles.json> --output <ranked.json>`.
3. Review the script's evidence and adjust only with an explicit reason. The dimensions are resume fit, relative competition, personal interest, development outlook, and location preference.
4. Present four groups: **努力争取**, **重点投递**, **相对保底**, and **不建议占用名额**.
5. For a shared application quota, explain why each selected role displaces the next alternative.
6. Always state that relative competition and “相对保底” are heuristic comparisons, not admission or hiring guarantees.

Read `references/scoring.md` when changing weights, thresholds, or competition estimates.

## Assist the application

1. Compare each JD requirement with explicit resume evidence. Separate `strong evidence`, `partial evidence`, `gap`, and `needs user confirmation`.
2. Suggest truthful resume wording. Never fabricate skills, dates, metrics, employers, projects, awards, or credentials.
3. Draft open-question answers from verified facts and the JD. Highlight placeholders and claims requiring user verification.
4. Reuse repeated fields only from the user's private configuration. Show a final review checklist before form entry.
5. Stop before final submission. Browser login, CAPTCHA, legal attestations, consent, and submit remain manual.

## Track applications

Use `scripts/tracker.py` to initialize, add, update, list, and show due items in a local CSV tracker. Store the real tracker outside the repository or in an ignored `private/` path.

```text
python scripts/tracker.py init --file private/applications.csv
python scripts/tracker.py add --file private/applications.csv --company "星河科技（虚构）" --role "数据产品培训生" --cycle "2027秋招" --deadline "2026-09-30T23:59:00+08:00"
python scripts/tracker.py update --file private/applications.csv --id APP-0001 --status "笔试" --next-action "完成在线测评"
```

## Extract email deadlines

1. Read `references/email-extension.md` before connecting.
2. Prefer mock files. For 163 Mail, use IMAP with an authorization code in environment variables or ignored local secrets. Never store or print it.
3. Run `scripts/email_imap.py mock --input <messages.json> --output <todos.json>` offline, or `fetch` only after user confirmation.
4. Treat extracted dates and event types as candidates. Show source, timezone, and confidence for review.
5. Do not write to a calendar until the user explicitly confirms selected events.

## Finish each run

Separate verified facts from assumptions, list unresolved questions, show upcoming deadlines, and state one concrete next manual action. Keep sensitive artifacts private and check repository status before committing.
