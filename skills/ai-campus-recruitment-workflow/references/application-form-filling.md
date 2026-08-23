# Application form filling

Read this reference when a real campus application involves resume upload, automatic parsing, or population of an employer form.

## Inspect before typing

1. Confirm that the user authorized work on the specific role and completed any required login.
2. Inspect the form before changing it. Identify resume upload and parsing support, accepted file formats, required sections, pre-existing saved data, and the final submission control.
3. Prefer upload-and-parse when the employer supports it. Do not start manual field-by-field entry until the upload path and any existing parsed data have been checked.

## Keep one visible browser session

1. Identify the browser surface and tab that Codex can actually control. Treat a controlled browser, a separate desktop browser, and an in-app browser as different sessions even when they show the same URL.
2. Before entering data, observe the login indicator and current form state in the controllable session. Do not assume that a login, upload, or draft from another surface is shared.
3. “Open the page” means make the exact relevant page visible to the user. Selecting a background tab or opening an empty duplicate is not sufficient.
4. After entering data, observe the values in that same session and bring the exact populated tab or window to the foreground when the interface supports it.
5. If Codex cannot both control and expose the same session, state the mismatch precisely. Never tell the user that the page they are viewing was populated when only a separate session contains the changes.

## Handle the resume upload

1. Explain that uploading sends the resume to the named employer, and obtain explicit authorization if the user has not already clearly authorized that disclosure.
2. If the browser can access the user-selected original file, upload it and observe the resulting page state. Never claim that upload or parsing succeeded without evidence.
3. If a local file picker, sandbox boundary, or browser permission prevents Codex from choosing the file, ask the user to perform only that smallest action: select the original resume in the open form. Resume control immediately after the user reports completion.
4. Respect the runtime storage choice. When data is conversation-only, do not copy, convert, or temporarily save the resume inside the workspace merely to bypass a browser file-access restriction.

## Reconcile parsed content

1. Wait for parsing to finish, then inspect every visible section, including contact information, education, internships, work, projects, skills, and application questions.
2. Compare parsed fields with explicit user-confirmed resume evidence. Treat parser output and pre-existing saved fields as unverified until checked.
3. Before requesting more information, report which sections are populated, which contain parsing errors, and which remain blank. Reuse facts the user already supplied and ask only for the missing fields needed to continue.
4. Classify experience by its actual nature: internships belong under internship experience, while full-time or other non-internship employment belongs under work experience. Do not move an internship into work experience merely to fill an empty section, and do not mark “no work experience” without confirmed evidence.
5. Correct factual parsing errors and formatting problems. Apply concise, truthful wording improvements only where the form accepts descriptive text; never invent dates, metrics, duties, credentials, or achievements.
6. Leave unsupported or ambiguous fields unresolved and ask for the missing fact instead of inferring it.
7. Treat password-bearing, access-code, private-share, or otherwise restricted project links as sensitive disclosure. Obtain explicit authorization to send the link and its access code to the named employer before entering it.
8. Avoid saving form snapshots, extracted personal fields, transformed resume copies, or application answers in the Skill or repository. Remove agent-created transient browser artifacts before committing when they may contain runtime data.

## Check role alignment

Do not equate a complete form with a strong role match. Before final review, compare the populated evidence with the official JD, distinguish demonstrated strengths from missing role-specific evidence, and ask whether the user has truthful information that can close a material gap. If the evidence does not exist, keep the gap explicit and do not manufacture targeting language.

## Ask for user review

After the form is populated, give the user a compact review with three groups:

- fields kept from parsing because they match confirmed evidence;
- fields Codex corrected or polished;
- fields still blank, ambiguous, or requiring the user's decision.

Ask whether the current form is accurate. If the user says it is not, request only the field name and correct content, apply the correction, and recheck the affected section. Do not advance to final submission until the user confirms the populated information.

## Stop at human checkpoints

The user handles login credentials, SMS or image CAPTCHA, legal attestations, consent, and the final submit action. Codex may navigate to the final review state but must not click the final submission control.
