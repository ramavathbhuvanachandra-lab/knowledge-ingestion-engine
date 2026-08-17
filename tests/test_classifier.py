from url_classifier import classify_url


urls = [

    "https://iitj.ac.in/ece",

    "https://iitj.ac.in/file.pdf",

    "https://iitj.ac.in/logo.png",

    "https://google.com",

    "abc"

]


for url in urls:

    info = classify_url(
        raw_url=url,
        normalized_url=url,
        base_domain="iitj.ac.in",
        discovered_from="homepage"
    )

    print(info)