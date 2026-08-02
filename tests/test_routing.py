from services.routing import difficulty, same_location


def test_same_location_detects_identical_coordinates():
    start = {"lon": 4.8357, "lat": 45.764}
    end = {"lon": 4.8357001, "lat": 45.7640001}
    assert same_location(start, end)


def test_same_location_rejects_different_coordinates():
    start = {"lon": 4.8357, "lat": 45.764}
    end = {"lon": 4.9, "lat": 45.8}
    assert not same_location(start, end)


def test_difficulty_levels():
    assert difficulty(20, 100) == "Facile"
    assert difficulty(45, 500) == "Intermédiaire"
    assert difficulty(90, 1200) == "Sportif"
