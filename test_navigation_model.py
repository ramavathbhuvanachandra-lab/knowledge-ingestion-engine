from models.navigation import NavigationCandidate


def main():

    candidate = NavigationCandidate(

        element_name="nav",

        element_id="navbar-main",

        classes=[
            "navbar",
            "navbar-expand-lg"
        ],

        aria_label="Main",

        links=[
            "Home",
            "Academics",
            "Research"
        ],

        link_count=3,

        navigation_type="primary",

        score=10
    )

    print("=" * 70)
    print("NAVIGATION CANDIDATE TEST")
    print("=" * 70)

    print("Element :", candidate.element_name)
    print("ID      :", candidate.element_id)
    print("Classes :", candidate.classes)
    print("ARIA    :", candidate.aria_label)
    print("Links   :", candidate.links)
    print("Count   :", candidate.link_count)
    print("Type    :", candidate.navigation_type)
    print("Score   :", candidate.score)

    print("\nRESULT  : PASS")


if __name__ == "__main__":
    main()