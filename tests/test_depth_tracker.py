from crawler.depth_tracker import DepthTracker


ROOT = "https://gwpgc.ac.in/"
ADMISSION = "https://gwpgc.ac.in/admission"
FACULTY = "https://gwpgc.ac.in/faculty"
EE = "https://gwpgc.ac.in/faculty/electrical-engineering"


def test_root_depth():

    tracker = DepthTracker()

    depth = tracker.register_root(ROOT)

    assert depth == 0
    assert tracker.get_depth(ROOT) == 0


def test_child_depth():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    depth = tracker.register_child(
        ADMISSION,
        ROOT,
    )

    assert depth == 1
    assert tracker.get_depth(ADMISSION) == 1


def test_grandchild_depth():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    tracker.register_child(
        FACULTY,
        ROOT,
    )

    depth = tracker.register_child(
        EE,
        FACULTY,
    )

    assert depth == 2
    assert tracker.get_depth(EE) == 2


def test_multiple_children_same_depth():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    tracker.register_child(
        ADMISSION,
        ROOT,
    )

    tracker.register_child(
        FACULTY,
        ROOT,
    )

    assert tracker.get_depth(ADMISSION) == 1
    assert tracker.get_depth(FACULTY) == 1


def test_duplicate_url_keeps_first_depth():

    tracker = DepthTracker()

    tracker.register_root(ROOT)

    tracker.register_child(
        FACULTY,
        ROOT,
    )

    tracker.register_child(
        EE,
        FACULTY,
    )

    # Try to rediscover EE from the root.
    # The original depth must remain 2.
    depth = tracker.register_child(
        EE,
        ROOT,
    )

    assert depth == 2
    assert tracker.get_depth(EE) == 2


def test_unknown_parent_starts_at_depth_one():

    tracker = DepthTracker()

    depth = tracker.register_child(
        ADMISSION,
        ROOT,
    )

    assert depth == 1


def test_contains():

    tracker = DepthTracker()

    assert tracker.contains(ROOT) is False

    tracker.register_root(ROOT)

    assert tracker.contains(ROOT) is True


def test_size():

    tracker = DepthTracker()

    assert tracker.size() == 0

    tracker.register_root(ROOT)

    tracker.register_child(
        ADMISSION,
        ROOT,
    )

    tracker.register_child(
        FACULTY,
        ROOT,
    )

    assert tracker.size() == 3


if __name__ == "__main__":

    test_root_depth()
    test_child_depth()
    test_grandchild_depth()
    test_multiple_children_same_depth()
    test_duplicate_url_keeps_first_depth()
    test_unknown_parent_starts_at_depth_one()
    test_contains()
    test_size()

    print("DEPTH TRACKER TESTS: PASS")