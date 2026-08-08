from models.navigation import NavigationCandidate
from analyzer.navigation_classifier import NavigationClassifier


TESTS = [

    NavigationCandidate(
        element_name="nav",
        element_id="navbar-main",
        classes=["navbar", "navbar-expand-lg"],
        aria_label="Main",
        links=["Home", "Academics", "Research"],
        link_count=3,
    ),

    NavigationCandidate(
        element_name="nav",
        element_id="footer-nav",
        classes=["footer-navigation"],
        aria_label="global footer menu",
        links=["Contact", "RTI"],
        link_count=2,
    ),

    NavigationCandidate(
        element_name="ul",
        element_id="superfish-main-menu",
        classes=["menu", "sf-menu"],
        aria_label="",
        links=["Home", "Admissions", "Research"],
        link_count=3,
    ),

    NavigationCandidate(
        element_name="div",
        element_id="content",
        classes=["content"],
        aria_label="",
        links=["One", "Two"],
        link_count=2,
    ),
]


def main():

    classifier = NavigationClassifier()

    results = classifier.classify(TESTS)

    print("\n" + "=" * 70)
    print("NAVIGATION CLASSIFIER TEST")
    print("=" * 70)

    for index, candidate in enumerate(results, start=1):

        print(f"\nCANDIDATE {index}")
        print("-" * 70)

        print("Element :", candidate.element_name)
        print("ID      :", candidate.element_id)
        print("Classes :", candidate.classes)
        print("ARIA    :", candidate.aria_label)
        print("Links   :", candidate.link_count)
        print("Type    :", candidate.navigation_type)
        print("Score   :", candidate.score)


if __name__ == "__main__":
    main()