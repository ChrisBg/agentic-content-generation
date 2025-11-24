import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from tools import search_web, search_industry_trends

print("--- Testing search_web ---")
results = search_web("python programming language")
print(f"Status: {results.get('status')}")
print(f"Count: {results.get('count')}")
print(f"Full Result: {results}")
if results.get("results"):
    print(f"First result: {results['results'][0]['title']}")

print("\n--- Testing search_industry_trends ---")
trends = search_industry_trends("Generative AI", region="US")
print(f"Status: {trends.get('status')}")
print(f"Trends found: {len(trends.get('trends', []))}")
if trends.get("trends"):
    print(f"First trend: {trends['trends'][0]}")
