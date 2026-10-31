import pdfplumber
from parser import parse_pdf

# Путь к скачанному PDF (можешь положить вручную в папку проекта)
pdf_path = "03.10.2026.pdf"

data = parse_pdf(pdf_path)

print("=" * 50)
print("ГРУППЫ, КОТОРЫЕ НАШЁЛ ПАРСЕР:")
print("=" * 50)
for key, value in data.items():
    if key == "__legend__":
        print(f"\n__legend__: {len(value)} строк")
        for item in value:
            print(f"   {item}")
        continue
    print(f"\n{key}: {len(value)} уроков")
    for z in value[:3]:  # первые 3 урока
        print(f"   {z}")

print()
print("=" * 50)
print("ПОИСК ГРУППЫ 526:")
print("=" * 50)
group = "526"
if group in data:
    for z in data[group]:
        print(z)
else:
    print(f"❌ Группа {group} НЕ найдена!")
    print("Все ключи:", list(data.keys()))