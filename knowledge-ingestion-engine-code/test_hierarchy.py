from parser.url_parser import URLParser
from analyzer.hierarchy_analyzer import HierarchyAnalyzer

parser = URLParser()
analyzer = HierarchyAnalyzer()

url = "https://iitj.ac.in/electrical-engineering/en/research-highlights"

url_structure = parser.parse(url)

hierarchy = analyzer.analyze(url_structure)

print(url_structure)
print()
print(hierarchy)