# Data schemas

## Private profile

The scoring script accepts JSON with `education`, `skills`, `languages`, `locations`, `interests`, `hard_constraints`, and optional `weights`. Weight keys are `resume_fit`, `competition`, `interest`, `development`, and `location`, and values must sum to 1.

## Verified role

Each role uses identifiers (`company`, `role`, `cycle`, `location`), date and quota fields (`deadline`, `application_limit`, `quota_group`), evidence fields (`official_url`, `retrieved_at`, `verification_status`, `source_notes`), hard requirements, and five 0–100 scoring inputs (`resume_fit`, `competition_level`, `interest`, `development`, `location_fit`).

Hard requirements may include `required_degree`, eligible graduation range, `required_majors`, `required_languages`, `required_skills`, `work_authorization`, and `max_travel_percent`. `competition_level` means estimated difficulty: 100 is more competitive. It must have a short explanation and is never a hiring probability.

## Tracker

The CSV columns are controlled by `scripts/tracker.py`. Datetimes use ISO 8601. Recommended statuses are `线索`, `待投递`, `已投递`, `测评`, `笔试`, `面试`, `Offer`, `拒绝`, `撤回`, and `结束`.
