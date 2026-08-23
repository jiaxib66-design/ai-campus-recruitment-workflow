# Data schemas

## Private profile

The scoring script accepts JSON with `education`, `skills`, `languages`, `locations`, `interests`, `hard_constraints`, and optional `weights`. Weight keys are `resume_fit`, `competition`, `interest`, `development`, and `location`, and values must sum to 1.

## Verified role

Each role uses identifiers (`company`, `role`, `cycle`, `location`), date and quota fields (`deadline`, `application_limit`, `quota_group`), evidence fields (`official_url`, `retrieved_at`, `verification_status`, `source_notes`), hard requirements, and five 0–100 scoring inputs (`resume_fit`, `competition_level`, `interest`, `development`, `location_fit`).

Hard requirements may include `required_degree`, eligible graduation range, `required_majors`, `required_languages`, `required_skills`, `work_authorization`, and `max_travel_percent`. `competition_level` means estimated difficulty: 100 is more competitive. It must have a short explanation and is never a hiring probability.

## Tracker

The CSV columns are controlled by `scripts/tracker.py`. Datetimes use ISO 8601. Recommended statuses are `线索`, `待投递`, `已投递`, `测评`, `笔试`, `面试`, `Offer`, `拒绝`, `撤回`, and `结束`.

## Application history

The optional JSONL history is append-only. Each event contains `recorded_at`, `application_id`, `event_type`, `source`, `source_id`, and field-level `changes` with `from` and `to`. Use a fictional or mailbox-derived event key as `source_id`; never place message bodies or credentials in history.

## Monitor state and report

The private monitor state contains processed event keys, pending status changes, sent reminder keys, and the last check time. The generated report separates `status_change_candidates`, `reminders`, and `unmatched_events`, and always declares whether a tracker write occurred. Status candidates require explicit user confirmation before `tracker.py update`.
