"""The anonymity rule for the leadership dashboard (app/privacy.py).

Most important idea: if a group is hidden, changing the answers of the people in it must not change
anything leadership sees. If it did, someone could work their answers out by subtraction.
"""
import copy
import random

import pytest

from app.config import check_min_group_size
from app.privacy import OTHER_TEAMS, band, publish_groups
from app.services.llm import ALLOWED_FLAGS
from app.utils import maturity_level

K = 5  # the default MIN_GROUP_SIZE


def person(average=3.0, flags=(), awaiting_review=0):
    return {"average": average, "flags": list(flags), "awaiting_review": awaiting_review}


def group(name, respondents, employees=None):
    return {"name": name, "employees": len(respondents) if employees is None else employees,
            "respondents": respondents}


def by_name(published):
    return {g["name"]: g for g in published["groups"]}


def risk_counts(published):
    return {row["risk"]: row["people"] for row in published["overall"]["top_risks"]}


# ---------- rule a: groups with at least K respondents are shown ----------

def test_group_with_enough_respondents_is_shown():
    published = publish_groups([group("Sales", [person(2), person(3), person(4), person(4), person(2)], employees=7)])
    assert by_name(published)["Sales"] == {
        "name": "Sales", "privacy": "shown", "employees": 7, "respondents": 5,
        "average_score": 3.0, "level": "Practitioner",
    }


def test_shown_group_uses_the_same_levels_as_the_report():
    published = publish_groups([group("Sales", [person(3.5)] * 5)])
    assert by_name(published)["Sales"]["level"] == maturity_level(3.5) == "Practitioner"


def test_only_respondents_count_towards_group_size():
    # 20 employees but only 4 respondents: still too small.
    published = publish_groups([group("Sales", [person()] * 4, employees=20)])
    assert "Sales" not in by_name(published)


# ---------- rule b: small groups are merged into "Other teams" ----------

def test_small_groups_are_merged_into_other_teams():
    published = publish_groups([
        group("Sales", [person(4)] * 5),
        group("Engineering", [person(2), person(3), person(4)], employees=4),
        group("HR", [person(1), person(5)]),
        group("Unassigned", [], employees=1),
    ])
    assert by_name(published)[OTHER_TEAMS] == {
        "name": OTHER_TEAMS, "privacy": "merged", "teams": ["Engineering", "HR", "Unassigned"],
        "employees": 7, "respondents": 5, "average_score": 3.0, "level": "Practitioner",
    }
    assert set(by_name(published)) == {"Sales", OTHER_TEAMS}


# ---------- rule c: an "Other teams" group that is still too small is hidden ----------

def test_other_teams_under_k_is_hidden_with_no_numbers():
    published = publish_groups([group("Sales", [person()] * 5), group("Eng", [person()] * 3), group("HR", [person()])])
    assert by_name(published)[OTHER_TEAMS] == {
        "name": OTHER_TEAMS, "privacy": "hidden", "teams_hidden": 2,
        "message": "2 teams hidden to protect anonymity",
    }


def test_single_hidden_team_message():
    published = publish_groups([group("Sales", [person()] * 5), group("HR", [person()])])
    assert by_name(published)[OTHER_TEAMS]["message"] == "1 team hidden to protect anonymity"


# ---------- rule d: the overall figure is hidden whenever anyone is hidden ----------

def test_overall_is_hidden_when_hidden_respondents_exist():
    published = publish_groups([group("Sales", [person(4)] * 5), group("HR", [person(1)])])
    assert published["overall"] == {
        "privacy": "hidden",
        "reason": "Some teams are too small to show. An overall figure would let their results be "
                  "worked out by subtracting the visible teams.",
    }


def test_overall_is_shown_when_every_respondent_is_in_a_visible_group():
    published = publish_groups([group("Sales", [person(4)] * 5), group("Eng", [person(1)] * 3), group("HR", [person(1)] * 2)])
    overall = published["overall"]
    assert overall["privacy"] == "shown"
    assert overall["respondents"] == 10
    assert overall["average_score"] == 2.5


def test_overall_is_shown_when_the_hidden_teams_have_no_respondents():
    published = publish_groups([group("Sales", [person(4)] * 5), group("HR", [], employees=3)])
    assert by_name(published)[OTHER_TEAMS]["privacy"] == "hidden"
    assert published["overall"]["privacy"] == "shown"
    assert published["overall"]["respondents"] == 5


# ---------- rule e: hidden groups expose nothing; risks are never per group ----------

def test_no_group_ever_carries_risks():
    published = publish_groups([group("Sales", [person(flags=["policy_unaware"])] * 6), group("HR", [person()])])
    for g in published["groups"]:
        assert not {"risks", "top_risks", "flags", "awaiting_review"} & set(g)


def test_every_group_has_a_privacy_field():
    published = publish_groups([group("A", [person()] * 5), group("B", [person()] * 2), group("C", [person()] * 3)])
    assert all(g["privacy"] in ("shown", "merged", "hidden") for g in published["groups"])
    assert published["overall"]["privacy"] in ("shown", "hidden")


# ---------- rule f: risk counts ----------

def test_band_hides_small_counts():
    assert band(0) == band(1) == band(4) == "fewer than 5"
    assert band(5) == 5
    assert band(12) == 12


def test_risks_below_k_are_banded_and_every_allowed_flag_is_listed():
    respondents = [person(flags=["unreviewed_output"])] * 6 + [person(flags=["customer_data_shared"])] * 2
    counts = risk_counts(publish_groups([group("Sales", respondents)]))
    assert counts == {
        "unreviewed_output": 6,
        "customer_data_shared": "fewer than 5",
        "confidential_data_shared": "fewer than 5",  # 0 looks exactly like 1-4
        "policy_unaware": "fewer than 5",
    }


def test_risks_are_sorted_exact_counts_first():
    respondents = [person(flags=["policy_unaware"])] * 5 + [person(flags=["unreviewed_output"])] * 7
    rows = publish_groups([group("Sales", respondents)])["overall"]["top_risks"]
    assert [r["risk"] for r in rows] == ["unreviewed_output", "policy_unaware",
                                         "confidential_data_shared", "customer_data_shared"]


def test_a_person_counts_once_per_risk():
    respondents = [person(flags=["policy_unaware", "policy_unaware"])] * 5
    assert risk_counts(publish_groups([group("Sales", respondents)]))["policy_unaware"] == 5


def test_awaiting_review_is_banded():
    published = publish_groups([group("Sales", [person(awaiting_review=1)] * 3 + [person()] * 2)])
    assert published["overall"]["awaiting_review"] == "fewer than 5"


def test_one_person_joining_does_not_change_a_small_risk_count():
    # A new respondent with a rare flag must not move any number leadership sees for that flag.
    before = [person(flags=["policy_unaware"])] * 2 + [person()] * 4
    after = before + [person(flags=["policy_unaware"])]
    assert risk_counts(publish_groups([group("S", before)]))["policy_unaware"] == \
        risk_counts(publish_groups([group("S", after)]))["policy_unaware"]


# ---------- MIN_GROUP_SIZE setting ----------

def test_min_group_size_below_3_is_refused():
    with pytest.raises(RuntimeError, match="MIN_GROUP_SIZE"):
        check_min_group_size(2)
    assert check_min_group_size(3) == 3


def test_min_group_size_can_be_changed():
    published = publish_groups([group("Sales", [person()] * 3)], min_size=3)
    assert by_name(published)["Sales"]["privacy"] == "shown"


# ---------- attacker: try every subtraction ----------

def subtraction_attack(published):
    """Org total minus every visible group. Returns (people left over, their average) or None."""
    overall = published["overall"]
    if overall["privacy"] != "shown" or overall["average_score"] is None:
        return None
    visible = [g for g in published["groups"] if g["privacy"] in ("shown", "merged") and g["average_score"] is not None]
    left_n = overall["respondents"] - sum(g["respondents"] for g in visible)
    if left_n == 0:
        return (0, None)
    left_total = overall["average_score"] * overall["respondents"] - sum(g["average_score"] * g["respondents"] for g in visible)
    return (left_n, left_total / left_n)


def hidden_people(groups, min_size=K):
    """The respondents the rule must protect: everyone in a small group when the small groups total < K."""
    small = [r for g in groups if len(g["respondents"]) < min_size for r in g["respondents"]]
    return small if len(small) < min_size else []


def with_hidden_answers_changed(groups, min_size=K):
    """Same org, but every hidden person's score and flags are replaced."""
    changed = copy.deepcopy(groups)
    if not hidden_people(groups, min_size):
        return changed
    for g in changed:
        if len(g["respondents"]) < min_size:
            g["respondents"] = [person(average=5.0 if r["average"] != 5.0 else 1.0, flags=list(ALLOWED_FLAGS),
                                       awaiting_review=r["awaiting_review"] + 1) for r in g["respondents"]]
    return changed


def assert_no_leak(groups, min_size=K):
    published = publish_groups(groups, min_size)

    # 1. Changing the hidden people's answers changes nothing leadership sees.
    assert publish_groups(with_hidden_answers_changed(groups, min_size), min_size) == published

    # 2. Org total minus the visible groups never leaves anybody over.
    attack = subtraction_attack(published)
    assert attack is None or attack[0] == 0
    if hidden_people(groups, min_size):
        assert published["overall"]["privacy"] == "hidden"

    # 3. Every published average covers at least min_size people; hidden groups carry no numbers.
    for g in published["groups"]:
        if g["privacy"] == "hidden":
            assert set(g) == {"name", "privacy", "teams_hidden", "message"}
        else:
            assert g["respondents"] >= min_size
    overall = published["overall"]
    if overall["privacy"] == "shown":
        assert overall["respondents"] == 0 or overall["respondents"] >= min_size
        # 4. Risk totals: no exact count below min_size, and nothing per group to subtract them from.
        assert all(r["people"] == f"fewer than {min_size}" or r["people"] >= min_size for r in overall["top_risks"])
        assert {r["risk"] for r in overall["top_risks"]} == set(ALLOWED_FLAGS)
    else:
        assert set(overall) == {"privacy", "reason"}
    return published


def test_attacker_cannot_recover_a_hidden_team_from_the_org_total():
    groups = [group("Sales", [person(3)] * 5), group("Support", [person(4)] * 6), group("Legal", [person(1)])]
    published = assert_no_leak(groups)
    assert subtraction_attack(published) is None  # overall hidden: nothing to subtract from


def test_attacker_cannot_use_other_teams_to_isolate_a_team():
    # Other teams is published as one block; its member teams have no numbers of their own,
    # so "Other teams minus X" has no X to subtract.
    groups = [group("Sales", [person(3)] * 5), group("Eng", [person(2)] * 3), group("HR", [person(5)] * 2)]
    published = assert_no_leak(groups)
    names = {g["name"] for g in published["groups"]}
    assert "Eng" not in names and "HR" not in names


def test_attacker_cannot_recover_one_persons_flag_from_risk_totals():
    groups = [group("Sales", [person(flags=["policy_unaware"])] + [person()] * 4),
              group("Support", [person()] * 5)]
    published = assert_no_leak(groups)
    assert risk_counts(published)["policy_unaware"] == "fewer than 5"


def test_old_seed_shape_every_northwind_team_under_5():
    # Northwind as seeded before the demo data was extended: Vikram (Sales, 4.0) and Priya
    # (Support, 2.5, customer_data_shared) were the only respondents.
    groups = [
        group("Sales", [person(4.0)], employees=3),
        group("Support", [person(2.5, ["customer_data_shared"])], employees=3),
        group("Engineering", [], employees=2),
        group("HR", [], employees=2),
        group("Unassigned", [], employees=1),
    ]
    published = assert_no_leak(groups)
    assert published["groups"] == [{
        "name": OTHER_TEAMS, "privacy": "hidden", "teams_hidden": 5,
        "message": "5 teams hidden to protect anonymity",
    }]
    assert published["overall"]["privacy"] == "hidden"


def random_org(rng):
    groups = []
    for d in range(rng.randint(1, 6)):
        respondents = [
            person(average=None if rng.random() < 0.05 else round(rng.uniform(1, 5), 2),
                   flags=rng.sample(ALLOWED_FLAGS, rng.randint(0, 2)),
                   awaiting_review=rng.randint(0, 1))
            for _ in range(rng.randint(0, 12))
        ]
        groups.append(group(f"Dept {d}", respondents, employees=len(respondents) + rng.randint(0, 3)))
    return groups


@pytest.mark.parametrize("min_size", [3, 5])
def test_invariants_hold_for_200_random_orgs(min_size):
    rng = random.Random(20261028)
    for _ in range(200):
        assert_no_leak(random_org(rng), min_size)
