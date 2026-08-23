# Optional IMAP email extension

Start with mock mode. Connect to a real mailbox only after the user confirms the mailbox, search scope, and time window. Fetch only recruiting-related messages. Do not delete, move, mark, reply, forward, or modify mail.

For 163 Mail, enable IMAP and create an authorization code. Supply credentials at runtime:

- `RECRUITMENT_IMAP_HOST=imap.163.com`
- `RECRUITMENT_IMAP_USER=<private mailbox address>`
- `RECRUITMENT_IMAP_AUTH_CODE=<authorization code>`

Do not commit these values. The standard-library script reads environment variables and does not automatically parse `.env`.

`email_imap.py fetch` performs read-only search and produces local JSON candidates. `mock` uses fictional exported messages and needs no network. Both recognize likely assessment, written-test, interview, material, Offer, and rejection events; a status event can exist without a deadline. Output contains only a minimized subject, sender, message id, matched date excerpt, and classification—not a durable full-mail archive. Review output because dates, timezones, senders, and classification can be ambiguous.

## Local monitoring loop

Run `recruitment_monitor.py` with the private tracker, extracted candidates, a private state file, and an output report. The monitor:

- matches by company and role evidence in the subject or sender;
- keeps ambiguous and unmatched mail separate;
- deduplicates message events and 72h/24h/3h reminder tiers;
- retains suggested status changes as pending until confirmed;
- never writes the tracker or calendar.

Review `status_change_candidates` with the user. Only after confirmation, call `tracker.py update` with `--source email_confirmed --source-id <event-key>`. After that update succeeds, run the monitor with `--confirmed-event-key <event-key>` to archive the pending candidate. If the user rejects a candidate, do not change the tracker; retain or archive it only according to the user's explicit choice.

Calendar creation is intentionally outside the automatic path. After the user confirms candidates, pass reviewed JSON to the chosen calendar integration and request confirmation again before writing.
