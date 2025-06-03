#!/usr/bin/env python3
# test_system.py

import sys
sys.path.append('.')  # Dodaj bieżący katalog do ścieżki

from agents.improved_system import run_query

# Testowe zapytania
test_queries = [
    "Ile czasu Dawid spędził na Facebooku?",
    "Kto najwięcej używał social media wczoraj?",
    "Ile kosztowało nas granie w gry w tym tygodniu?",
]

print("🚀 Testowanie systemu wieloagentowego\n")

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*60}")
    print(f"Test {i}: {query}")
    print(f"{'='*60}")
    
    try:
        result = run_query(query)
        print(f"\n✅ ODPOWIEDŹ:\n{result['answer']}")
        print(f"\n📝 SQL:\n{result['sql_query']}")
    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")