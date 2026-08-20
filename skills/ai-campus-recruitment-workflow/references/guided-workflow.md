# Guided workflow

Use this protocol to run the recruitment loop naturally for first-time and returning users. Real usage and Skill improvement are separate modes.

## Operating modes

### Run mode

Default to run mode. Help the user complete the recruitment task without discussing Skill internals, versions, test plans, or file changes. Treat real profiles, resumes, companies, roles, and outcomes as runtime inputs only.

Guide one useful next action at a time in natural language. Use a short checklist only when several facts are needed together. Do not mechanically repeat stage metadata or privacy notices after the user has settled the data boundary.

### Improvement mode

Enter improvement mode only when the user explicitly asks to record a workflow issue, change the Skill, or publish a version. Preserve the interrupted run step. Agree on the reusable change, edit and validate the Skill, then return to run mode.

## Runtime data boundary

- Treat all user-provided profiles, resumes, company names, job descriptions, screenshots, links, application answers, tracker records, emails, and feedback artifacts as runtime data.
- Keep runtime inputs in a user-selected ignored `private/` path only when persistence is needed. Keep disposable derived results in an ignored `output/` path. If persistence is unnecessary, keep the data in the conversation only.
- Never copy runtime data into `SKILL.md`, `references/`, `assets/`, `scripts/`, `agents/`, repository `examples/`, `config/`, or `tests/`.
- Use fictional and visibly labeled data for reusable examples and automated tests.
- Before saving a new category of user data, state the exact target path and why persistence is needed.

## Stages

### 0. Determine user state and data boundary

Determine whether the user is first-time or returning before asking for profile information.

- **First-time user**: no user-confirmed profile is accessible in the current conversation or an explicitly authorized private path.
- **Returning user**: a user-confirmed profile is accessible in the current conversation or an explicitly authorized private path.

Never claim to remember or reuse a profile that is not actually accessible. If a new task has no authorized profile, treat the user as first-time.

Ask once whether runtime data should remain conversation-only or may be saved in a private path. Explain human checkpoints briefly, then continue without repeating the notice.

Completion: user state and storage choice are explicit.

### 1. Build or refresh the candidate profile

For a first-time user:

1. Invite the user to provide a resume first. If no resume is available, collect only the minimum education, graduation, experience, skills, location, and hard-constraint facts needed for the current run.
2. Extract evidence and propose a small number of tentative direction hypotheses, such as internet, AI, gaming, state-owned enterprise, government digitalization, enterprise software, consumer, ecommerce, or finance. Label them as hypotheses, not decisions.
3. Ask one adaptive follow-up round about preferred roles, industries, company types, regions, and reasons.
4. Ask a second round only when an important tradeoff or evidence gap remains, such as stability versus growth, location flexibility, work intensity, or missing project details.
5. If the user has much to explain and the current interface offers voice input, mention that they may speak naturally and Codex will organize the answer for confirmation.
6. Show the resulting profile once for truthfulness and preference confirmation.

For a returning user:

1. Ask whether graduation timing, experience, skills, preferences, or hard constraints changed.
2. Reuse unchanged user-confirmed facts and collect only the delta.
3. If the user requests a clean restart, follow the first-time path.

Completion: required profile facts are present and user-confirmed, or clearly marked unknown.

### 2. Discover target companies and roles

Choose one route from the user's current level of clarity:

- **Named companies**: accept company names, role links, screenshots, or a company list. Preserve each original lead and search the official campus source for those employers.
- **Direction or region**: when the user knows a role, industry, company type, or location but has no company names, clarify only consequential boundaries, then find a reviewable company pool. Explain why each company fits and let the user choose which employers to verify in depth.
- **Unclear target**: use the confirmed profile to offer a few tentative directions, ask about interest and tradeoffs, then narrow to a company-search brief.

Do not force the user to provide company names when discovery is what they need. Do not search broadly before enough region, role, industry, or constraint information exists to make the results useful.

Completion: named company leads or a user-approved company-search brief is ready for official verification.

### 3. Verify official facts

Find the employer's official recruiting source and verify the cycle, eligibility, graduation window, deadline and timezone, quota, location, and full JD. Separate verified, conflicting, and unresolved facts. Ask the user to resolve any fact available only after login.

After filtering out hard conflicts and weak or unverified leads, form the smallest useful shortlist of suitable roles, usually two to five. When the current Codex interface can open browser tabs, automatically open each shortlisted role's official employer page for the user. Do not substitute a search result, aggregator, social post, or inferred URL for the official role page.

If browser opening is unavailable or fails, provide clearly labeled clickable official links instead. Avoid flooding the user with every discovered role, reopening pages already visible, or opening login and submission pages prematurely.

Ask the user to review the real role pages and say which role or roles they prefer and what attracts them. Treat this stated preference as new scoring evidence; do not finalize the application order solely from resume fit before the user has had this review opportunity.

Completion: material facts have official evidence or remain explicitly unresolved, the suitable official role pages have been opened or linked, and the user has been invited to express a preference.

### 4. Check gates and prioritize

Compare verified requirements with the private profile and the user's reaction after reviewing the official pages, show hard conflicts and unknowns, then score eligible roles. Explain category labels and any shared-quota displacement. Ask the user whether the priorities reflect their real preferences.

Completion: the user accepts the ranking or supplies corrections for a rerun.

### 5. Assist application materials

Map JD requirements to explicit resume evidence and help draft truthful wording or open-question answers. Mark every placeholder and claim that needs verification. Provide a final review checklist.

Completion: the user confirms the materials are factually accurate and ready for manual entry.

### 6. Hand off manual submission

Guide the user to open the official application page and manually handle login, CAPTCHA, consent, legal attestations, and final submission. Never claim submission occurred based only on prepared materials.

Completion: the user reports the actual outcome, timestamp, and any next action.

### 7. Update the tracker

Show the exact tracker record to be created or changed and request confirmation before writing real application status. Record the official source, deadline, submission status, and next action without storing credentials.

Completion: the private tracker reflects the user-confirmed state.

### 8. Review deadlines and reminders

List upcoming deadlines from verified sources or user-confirmed messages. Treat extracted email dates as candidates. Ask separately before mailbox access and before every calendar write.

Completion: deadlines are reviewed and any external write has explicit approval.

### 9. Close and improve

Summarize verified outcomes, unresolved questions, upcoming deadlines, and one next manual action. Accept feedback without switching modes automatically. Enter improvement mode only when the user explicitly asks to change the reusable workflow.

Completion: the current run is closed or the user explicitly starts another stage.

## Change-control checkpoint

Before modifying this Skill because of a test result, present:

1. the observed workflow gap;
2. the proposed reusable behavior change;
3. the files that would change;
4. what would remain unchanged, especially privacy and human checkpoints;
5. the validation to run afterward.

Do not edit until the user approves that specific change.
