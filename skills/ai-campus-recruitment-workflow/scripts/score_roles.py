#!/usr/bin/env python3
"""Apply hard gates, score verified roles, and enforce shared application quotas."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DEFAULT_WEIGHTS = {
    "resume_fit": 0.35,
    "competition": 0.15,
    "interest": 0.20,
    "development": 0.15,
    "location": 0.15,
}
DEGREE_RANK = {"associate": 1, "bachelor": 2, "master": 3, "phd": 4, "专科": 1, "本科": 2, "硕士": 3, "博士": 4}
DISCLAIMER = "竞争程度和“相对保底”仅为基于有限信息的辅助判断，不代表录用概率，也不承诺录用。"


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def text_set(values) -> set[str]:
    return {str(value).strip().casefold() for value in (values or []) if str(value).strip()}


def check_hard_gates(profile: dict, role: dict) -> tuple[list[str], list[str]]:
    conflicts: list[str] = []
    unknowns: list[str] = []
    education = profile.get("education", {})
    constraints = profile.get("hard_constraints", {})

    required_degree = role.get("required_degree")
    degree = education.get("degree")
    if required_degree:
        if not degree:
            unknowns.append("用户学历未填写")
        elif DEGREE_RANK.get(str(degree).casefold(), 0) < DEGREE_RANK.get(str(required_degree).casefold(), 0):
            conflicts.append(f"学历低于要求：{required_degree}")

    graduation = education.get("graduation_date")
    start, end = role.get("eligible_graduation_start"), role.get("eligible_graduation_end")
    if start or end:
        if not graduation:
            unknowns.append("毕业时间未填写")
        elif (start and graduation < start) or (end and graduation > end):
            conflicts.append("毕业时间不在招聘范围内")

    required_majors = text_set(role.get("required_majors"))
    if required_majors and not (required_majors & text_set(education.get("majors"))):
        conflicts.append("专业不在明确接受范围内")

    missing_skills = sorted(text_set(role.get("required_skills")) - text_set(profile.get("skills")))
    if missing_skills:
        conflicts.append("缺少硬性技能：" + ", ".join(missing_skills))

    language_names = text_set(profile.get("languages", {}).keys())
    missing_languages = sorted(text_set(role.get("required_languages")) - language_names)
    if missing_languages:
        conflicts.append("缺少语言要求：" + ", ".join(missing_languages))

    auth_required = role.get("work_authorization")
    auth_user = constraints.get("work_authorization")
    if auth_required and auth_user and str(auth_required).casefold() != str(auth_user).casefold():
        conflicts.append("工作许可不匹配")
    elif auth_required and not auth_user:
        unknowns.append("工作许可未填写")

    if role.get("location") in set(constraints.get("excluded_locations", [])):
        conflicts.append("岗位地点属于排除地区")

    role_travel = role.get("max_travel_percent")
    user_travel = constraints.get("max_travel_percent")
    if role_travel is not None and user_travel is not None and float(role_travel) > float(user_travel):
        conflicts.append("出差比例超过用户上限")

    for required in constraints.get("must_have", []):
        haystack = json.dumps(role, ensure_ascii=False).casefold()
        if str(required).casefold() not in haystack:
            conflicts.append(f"岗位未体现用户硬性条件：{required}")

    if role.get("verification_status") != "verified":
        unknowns.append("关键岗位信息尚未由官网核验")
    return conflicts, unknowns


def weights_for(profile: dict) -> dict:
    weights = profile.get("weights") or DEFAULT_WEIGHTS
    if set(weights) != set(DEFAULT_WEIGHTS):
        raise ValueError(f"weights keys must be: {', '.join(DEFAULT_WEIGHTS)}")
    total = sum(float(v) for v in weights.values())
    if abs(total - 1.0) > 1e-6 or any(float(v) < 0 for v in weights.values()):
        raise ValueError("weights must be non-negative and sum to 1")
    return {k: float(v) for k, v in weights.items()}


def numeric(role: dict, key: str) -> float:
    value = float(role.get(key, 0))
    if not 0 <= value <= 100:
        raise ValueError(f"{role.get('company')} / {role.get('role')}: {key} must be 0..100")
    return value


def classify(score: float, competition: float, conflicts: list[str]) -> str:
    if conflicts:
        return "不建议占用名额"
    if score >= 72 and competition >= 70:
        return "努力争取"
    if score >= 70:
        return "重点投递"
    if score >= 60 and competition <= 45:
        return "相对保底"
    return "不建议占用名额"


def score_role(profile: dict, role: dict, weights: dict) -> dict:
    conflicts, unknowns = check_hard_gates(profile, role)
    values = {
        "resume_fit": numeric(role, "resume_fit"),
        "competition": 100 - numeric(role, "competition_level"),
        "interest": numeric(role, "interest"),
        "development": numeric(role, "development"),
        "location": numeric(role, "location_fit"),
    }
    raw_score = sum(values[key] * weights[key] for key in weights)
    uncertainty_penalty = min(10, len(unknowns) * 3)
    score = round(max(0, raw_score - uncertainty_penalty), 2)
    result = dict(role)
    result.update({
        "hard_gate": "fail" if conflicts else ("unknown" if unknowns else "pass"),
        "hard_conflicts": conflicts,
        "unknowns": unknowns,
        "score": score,
        "category": classify(score, numeric(role, "competition_level"), conflicts),
        "score_breakdown": values,
        "uncertainty_penalty": uncertainty_penalty,
        "quota_selected": None,
        "quota_reason": "",
    })
    return result


def deadline_key(item: dict) -> str:
    value = item.get("deadline") or "9999-12-31T23:59:59+00:00"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return "9999-12-31T23:59:59+00:00"


def apply_quotas(items: list[dict]) -> None:
    groups: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        groups[item.get("quota_group") or f"{item.get('company')}::__unshared__::{item.get('role')}"] .append(item)
    for group_items in groups.values():
        limits = [int(x["application_limit"]) for x in group_items if x.get("application_limit") not in (None, "")]
        limit = min(limits) if limits else len(group_items)
        candidates = sorted(
            (x for x in group_items if not x["hard_conflicts"]),
            key=lambda x: (-x["score"], -numeric(x, "interest"), -numeric(x, "resume_fit"), deadline_key(x)),
        )
        selected_ids = {id(x) for x in candidates[:limit]}
        cutoff = candidates[limit]["score"] if len(candidates) > limit else None
        for item in group_items:
            if item["hard_conflicts"]:
                item["quota_selected"] = False
                item["quota_reason"] = "存在硬性门槛冲突，不占用名额"
            elif id(item) in selected_ids:
                item["quota_selected"] = True
                detail = f"在共享名额中按综合分 {item['score']:.2f} 排序入选"
                if cutoff is not None:
                    detail += f"，高于首个未入选岗位 {cutoff:.2f}"
                item["quota_reason"] = detail
            else:
                item["quota_selected"] = False
                item["quota_reason"] = f"共享名额上限为 {limit}，当前综合分 {item['score']:.2f} 未进入前 {limit}"


def rank(profile: dict, roles: list[dict]) -> dict:
    weights = weights_for(profile)
    items = [score_role(profile, role, weights) for role in roles]
    apply_quotas(items)
    items.sort(key=lambda x: (not bool(x["quota_selected"]), -x["score"], x.get("company", ""), x.get("role", "")))
    return {"disclaimer": DISCLAIMER, "weights": weights, "roles": items}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--roles", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    roles_data = load_json(args.roles)
    roles = roles_data.get("roles", roles_data) if isinstance(roles_data, dict) else roles_data
    if not isinstance(roles, list):
        parser.error("roles input must be a list or an object containing a roles list")
    result = rank(load_json(args.profile), roles)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Ranked {len(roles)} role(s) to {output}")
    print(DISCLAIMER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
