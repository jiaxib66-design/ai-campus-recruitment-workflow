# Scoring model

Default weights: resume fit 35%, relative competition advantage 15% (`100 - competition_level`), interest 20%, development 15%, and location 15%.

Apply hard gates first. A confirmed conflict is `不建议占用名额`. An unknown requirement is flagged and incurs a small uncertainty penalty; it is not treated as a confirmed pass.

- `努力争取`: score at least 72 and competition level at least 70
- `重点投递`: score at least 70 and not categorized above
- `相对保底`: score at least 60 and competition level at most 45
- `不建议占用名额`: hard conflict or remaining cases

These are workflow labels, not outcome predictions. Competition depends on incomplete, changing information; “相对保底” never means guaranteed admission or employment.

Within each `quota_group`, rank passing roles by score, interest, resume fit, then earlier verified deadline. Select only up to the confirmed `application_limit` and explain selected versus displaced roles.
