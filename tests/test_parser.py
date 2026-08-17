from parser.url_parser import URLParser


parser = URLParser()

result = parser.parse(
    "https://iitj.ac.in/electrical-engineering/en/research-highlights?tab=faculty#section"
)

print(result)