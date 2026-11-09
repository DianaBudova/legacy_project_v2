# Лабораторна №8 — варіант 2 (process.py)

План до змін: REENGINEERING_PLAN.md. Початковий модуль: process_before.py.
Метрики та сирий вивід: before/, iteration1/, iteration2/, after/.
У before/ враховано 14 попередніх тестів; tests/test_process.py ще не застосовано.
Для coverage джерело — src, звіт відфільтровано до src/process.py.
Це дозволяє чесно показати 0%, навіть якщо модуль взагалі не імпортується.
Ітерація 1: 73 characterization-тести, загалом 87 passed; код ще не змінено.
Ітерація 2: спільні фінансові правила, 87 passed, proc CC 21 → 11.
Ітерація 3 (after): індекси, декомпозиція, Enum, валідація; 87 passed,
100% statement coverage, pylint 10.00, proc CC 3, validate_order CC 4, max CC 5.

Середовище вимірювання: Linux, Python 3.12.3; версії пакетів — tool_versions.txt.
Відтворення після встановлення pytest pytest-cov pylint radon:

```bash
python3 artifacts/lab8/measure.py after
PYTHONPATH=. python3 artifacts/lab8/check_compatibility.py
```

compatibility.txt: порівняння з незміненим модулем на 200 детермінованих
пакетах замовлень і вбудованих демонстраційних даних, включно з save().
Ідентифікатори довідників мають бути hashable (штатні цілочислові ID).
Збережено перший запис при однакових id, порядок помилок та результатів.
Існуючу неузгодженість refunded між validate_order і proc збережено.
Покриття 100% означає statement coverage, а не доказ коректності всіх входів.
