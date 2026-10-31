import pdfplumber

pdf_path = "03.10.2026.pdf"  # ← поставь имя своего PDF

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    print(f"Ширина страницы: {page.width}")
    print(f"Высота: {page.height}")

    # Вертикальные линии (если есть)
    lines = [l for l in page.lines + page.rects if abs(l["x0"] - l["x1"]) < 2]
    xs = sorted({round(l["x0"]) for l in lines})
    print(f"\nВертикальные линии (x): {xs}")
    print(f"Всего линий: {len(lines)}")

    # Первые 50 слов с координатами
    words = page.extract_words()
    print(f"\nВсего слов: {len(words)}")
    print("\nПервые 50 слов (текст, x0, x1, top):")
    for w in words[:50]:
        print(f"  {w['text']!r:25} x0={w['x0']:7.1f}  x1={w['x1']:7.1f}  top={w['top']:7.1f}")