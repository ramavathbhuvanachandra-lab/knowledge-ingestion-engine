from url_normalizer import normalize_url

urls = [

    " https://iitj.ac.in/main/ ",

    "https://iitj.ac.in/main////",

    "https://iitj.ac.in/main#about",

    "https://iitj.ac.in/main/en/help/",

]

for url in urls:

    print(normalize_url(url))