import pdfplumber
import re
from collections import defaultdict

GROUP_NUM_RE = re.compile(r"^\d{3,4}$")
LESSON_NUM_RE = re.compile(r"^\d{1,2}$")
CANCELLED_RE = re.compile(r"[Уу]рок\s+снят", re.IGNORECASE)
GALOCHKA_RE = re.compile(r"^[√✓vV]+$")

LEGEND_RE = re.compile(
    r"([А-ЯЁ][а-яё\-]+\s+[А-ЯЁ]\.\s?[А-ЯЁ]?\.?\s*)?\d{2,3}[А-Я]?\s*\([\d,\-\s]+\)"
)


def _clean_dup(s: str) -> str:
    """Убирает дубли букв (С С т т -> Ст) и лишние пробелы."""
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s).strip(" .")
    s = re.sub(r"(\b\w)\s+\1\b", r"\1", s)
    s = re.sub(r"([А-ЯЁа-яё])\1", r"\1", s)
    return s.strip(" .")


def parse_pdf(pdf_path: str) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = defaultdict(list)
    legend_lines: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        
        words = page.extract_words(x_tolerance=3, y_tolerance=3)
        
        words.sort(key=lambda w: (round(w['top'] / 5) * 5, w['x0']))
        
        current_group = None
        current_lesson = None
        
        for w in words:
            text = w['text']
            x0 = w['x0']
            
            if x0 < 80 and GROUP_NUM_RE.match(text):
                current_group = text
                current_lesson = None
                continue
                
            if not current_group:
                continue

            if 80 <= x0 < 110 and LESSON_NUM_RE.match(text):
                lesson_num = int(text)
                existing = [l for l in result[current_group] if l['lesson'] == lesson_num]
                if not existing:
                    current_lesson = {
                        "lesson": lesson_num,
                        "new_subject": "", "new_teacher": "",
                        "old_subject": "", "old_teacher": "",
                        "cancelled": False, "unchanged": False
                    }
                    result[current_group].append(current_lesson)
                else:
                    current_lesson = existing[0]
                continue
                
            if not current_lesson:
                continue

            if x0 >= 730:
                line_words = [w2['text'] for w2 in words if abs(w2['top'] - w['top']) < 5 and w2['x0'] >= 730]
                line_str = " ".join(line_words).strip()
                if line_str and line_str not in legend_lines:
                    legend_lines.append(line_str)
                continue
                
            if 110 <= x0 < 250:
                if CANCELLED_RE.search(text):
                    current_lesson["cancelled"] = True
                elif not GALOCHKA_RE.match(text):
                    current_lesson["new_subject"] += " " + text
            elif 250 <= x0 < 400:
                current_lesson["new_teacher"] += " " + text
            elif 400 <= x0 < 550:
                current_lesson["old_subject"] += " " + text
            elif 550 <= x0 < 730:
                current_lesson["old_teacher"] += " " + text
                
        for group, lessons in result.items():
            for l in lessons:
                l["new_subject"] = _clean_dup(l["new_subject"])
                l["new_teacher"] = _clean_dup(l["new_teacher"])
                l["old_subject"] = _clean_dup(l["old_subject"])
                l["old_teacher"] = _clean_dup(l["old_teacher"])

    cleaned_legend = []
    for line in legend_lines:
        line = _clean_dup(line)
        if line and line not in cleaned_legend:
            cleaned_legend.append(line)

    result["__legend__"] = cleaned_legend
    return dict(result)

def format_zameni(group: str, zameni: list[dict], day_label: str, date_label: str) -> str:
    if not zameni:
        return (
            f"📋 *Замены для группы {group}*\n"
            f"📅 {day_label}, {date_label}\n\n"
            f"_Замен для вашей группы нет._"
        )

    lines = [f"📋 *Замены для группы {group}*", f"📅 {day_label}, {date_label}", ""]

    for z in zameni:
        lesson = z.get("lesson", "?")
        header = f"*{lesson} урок*"

        if z.get("cancelled"):
            old = ""
            if z.get("old_subject"):
                old = f"\n   _был: {z['old_subject']}"
                if z.get("old_teacher"):
                    old += f" — {z['old_teacher']}"
                old += "_"
            lines.append(f"{header}\n⏸ УРОК СНЯТ{old}")
            lines.append("")
            continue

        if z.get("unchanged") and not z.get("new_subject"):
            lines.append(f"{header}\n✅ Изменений нет")
            lines.append("")
            continue

        block = [header]
        new_line = f"🔄 {z.get('new_subject', '—')}"
        if z.get("new_teacher"):
            new_line += f" — {z['new_teacher']}"
        block.append(new_line)

        if z.get("old_subject"):
            old_line = f"❌ _вместо_ {z['old_subject']}"
            if z.get("old_teacher"):
                old_line += f" — {z['old_teacher']}"
            block.append(old_line)

        lines.append("\n".join(block))
        lines.append("")

    return "\n".join(lines)


def format_legend(legend: list[str]) -> str:
    if not legend:
        return "📚 *Расписание кабинетов*\n\n_Информация отсутствует._"
    lines = ["📚 *Расписание кабинетов*", ""]
    for item in legend:
        lines.append(f"• {item}")
    return "\n".join(lines)
