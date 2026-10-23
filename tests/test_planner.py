from datetime import date

from core.planner import compute_shopping_list


def test_calculates_shopping_amounts_for_90_sandwiches():
    recipe = {
        "bread": 2,
        "ham": 1,
        "cheese": 1,
    }

    donations = [
        {
            "item": "bread",
            "quantity": 120,
            "expiry": date(2026, 10, 30),
        },
        {
            "item": "ham",
            "quantity": 40,
            "expiry": date(2026, 10, 30),
        },
    ]

    results = compute_shopping_list(
        recipe=recipe,
        unit_size=10,
        total_portions=9,
        event_date=date(2026, 10, 23),
        donations=donations,
    )

    amounts_to_buy = {
        item["item"]: item["to_buy"]
        for item in results
    }

    assert amounts_to_buy == {
        "bread": 60,
        "ham": 50,
        "cheese": 90,
    }
def test_reports_surplus_when_donations_exceed_need():
    recipe = {
        "bread": 2,
    }

    donations = [
        {
            "item": "bread",
            "quantity": 200,
            "expiry": date(2026, 10, 30),
        },
    ]

    results = compute_shopping_list(
        recipe=recipe,
        unit_size=10,
        total_portions=9,
        event_date=date(2026, 10, 23),
        donations=donations,
    )

    bread_result = results[0]

    assert bread_result["to_buy"] == 0
    assert bread_result["surplus"] == 20

def test_excludes_expired_donations_and_marks_them_for_review():
    recipe = {
        "bread": 2,
    }

    donations = [
        {
            "item": "bread",
            "quantity": 60,
            "expiry": date(2026, 10, 20),
        },
        {
            "item": "bread",
            "quantity": 60,
            "expiry": date(2026, 10, 30),
        },
    ]

    results = compute_shopping_list(
        recipe=recipe,
        unit_size=10,
        total_portions=9,
        event_date=date(2026, 10, 23),
        donations=donations,
    )

    bread_result = results[0]

    assert bread_result["usable_donations"] == 60
    assert bread_result["needs_review"] == 60
    assert bread_result["to_buy"] == 120

def test_shows_full_need_when_there_are_no_donations():
    recipe = {
        "bread": 2,
        "ham": 1,
        "cheese": 1,
    }

    results = compute_shopping_list(
        recipe=recipe,
        unit_size=10,
        total_portions=9,
        event_date=date(2026, 10, 23),
        donations=[],
    )

    amounts_to_buy = {
        item["item"]: item["to_buy"]
        for item in results
    }

    assert amounts_to_buy == {
        "bread": 180,
        "ham": 90,
        "cheese": 90,
    }

def test_rounds_fractional_ingredient_need_up():
    recipe = {
        "lettuce": 0.35,
    }

    results = compute_shopping_list(
        recipe=recipe,
        unit_size=10,
        total_portions=1,
        event_date=date(2026, 10, 23),
        donations=[],
    )

    lettuce_result = results[0]

    assert lettuce_result["need"] == 4
    assert lettuce_result["to_buy"] == 4

def test_returns_zero_need_when_no_portions_are_signed_up():
    recipe = {
        "bread": 2,
        "ham": 1,
    }

    results = compute_shopping_list(
        recipe=recipe,
        unit_size=10,
        total_portions=0,
        event_date=date(2026, 10, 23),
        donations=[],
    )

    for item in results:
        assert item["need"] == 0
        assert item["to_buy"] == 0