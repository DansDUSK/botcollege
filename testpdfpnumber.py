import pdfplumber

with pdfplumber.open("03.10.2026.pdf") as pdf:
    page = pdf.pages[0]
    print("=== extract_text() ===")
    text = page.extract_text()
    print(text if text else "❌ Текст НЕ извлекается")

    print("\n=== extract_tables() ===")
    tables = page.extract_tables()
    print(f"Найдено таблиц: {len(tables)}")
    if tables:
        for i, table in enumerate(tables):
            print(f"\n--- Таблица {i+1} ---")
            for row in table[:5]:  # первые 5 строк
                print(row)