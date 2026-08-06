from url_validator import is_valid_url


urls = [

    "https://iitj.ac.in",

    "https://iitj.ac.in/main/en/contact",

    "javascript:void(0)",

    "mailto:test@gmail.com",

    "tel:+911234567890",

    "#",

    "https://iitj.ac.in/main-key functionaries",

    "",

]


for url in urls:

    print(url, "->", is_valid_url(url))