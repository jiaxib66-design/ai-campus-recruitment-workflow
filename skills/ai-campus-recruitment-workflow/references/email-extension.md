# Optional IMAP email extension

Start with mock mode. Connect to a real mailbox only after the user confirms the mailbox, search scope, and time window. Fetch only recruiting-related messages. Do not delete, move, mark, reply, forward, or modify mail.

For 163 Mail, enable IMAP and create an authorization code. Supply credentials at runtime:

- `RECRUITMENT_IMAP_HOST=imap.163.com`
- `RECRUITMENT_IMAP_USER=<private mailbox address>`
- `RECRUITMENT_IMAP_AUTH_CODE=<authorization code>`

Do not commit these values. The standard-library script reads environment variables and does not automatically parse `.env`.

`email_imap.py fetch` performs read-only search and produces local JSON candidates. `mock` uses fictional exported messages and needs no network. Both extract likely assessment, written-test, interview, and material deadlines. Review output because dates and timezones can be ambiguous.

Calendar creation is intentionally outside the automatic path. After the user confirms candidates, pass reviewed JSON to the chosen calendar integration and request confirmation again before writing.
