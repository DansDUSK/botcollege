import camelot
import pdfplumber
import re
from collections import defaultdict

# --- РЕГУЛЯРКИ ---
GROUP_NUM_RE = re.compile(r"(\d{3,4})")
LESSON_NUM_RE = re.compile(r"^\s*(\d{1,2})\s*$")
CANCELLED_RE = re.compile(r"[Уу]рок\s+снят", re.IGNORECASE)
GALOCHKA_RE = re.compile(r"^[√✓vV]+$")
TEACHER_RE = re.compile(r"([А-ЯЁ][а-яё\-]+)\s+([А-ЯЁ]\.\s?[А-ЯЁ]?\.?)")

# СТРОГАЯ регулярка для легенды: Фамилия И.О. + аудитория + (уроки)
# Пример: "Горбова Г.И. 402 (1-6)" или "Прокопьева Е.А. 302 (1-3,5-6)"
LEGEND_STRICT_RE = re.compile(
    r"^([А-ЯЁ][а-яё\-]+\s+[А-ЯЁ]\.\s?[А-ЯЁ]?\.?)\s+(\d{2,3}[А-Я]?)\s*\(([\d,\-\s]+)\)$"
)

def _clean(s: str) -> str:
    if not s: return ""
    s = s.replace("│", "").replace("┼", "").replace("─", "").replace("┤", "")
    s = s.replace("┌", "").replace("┐", "").replace("└", "").replace("┘", "")
    s = s.replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip(" .")

def _extract_teachers(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = raw_text.replace("\n", " ")
    matches = TEACHER_RE.findall(text)
    teachers = []
    for surname, initials in matches:
        t = f"{surname} {initials.replace(' ', '')}"
        if t not in teachers:
            teachers.append(t)
    return ", ".join(teachers)

def _parse_legend(pdf_path: str) -> list[str]:
    """Достает ТОЛЬКО легенду кабинетов (Фамилия И.О. + Аудитория + Уроки)."""
    legend = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.split("\n"):
                    # Ищем только строки, которые полностью совпадают с паттерном легенды
                    # (игнорируем всё, что похоже на расписание)
                    if "Урок снят" in line or "│" in line or "предмет" in line.lower():
                        continue
                    
                    # Пробуем найти строгий паттерн
                    match = LEGEND_STRICT_RE.search(line.strip())
                    if match:
                        teacher = match.group(1).strip()
                        room = match.group(2).strip()
                        lessons = match.group(3).strip()
                        legend_item = f"{teacher} — {room} ({lessons})"
                        if legend_item not in legend:
                            legend.append(legend_item)
    except Exception as e:
        print(f"❌ Ошибка парсинга легенды: {e}")
    return legend

def parse_pdf(pdf_path: str) -> dict[str, list[dict]]:
    result = defaultdict(list)
    
    # 1. Парсим группы через camelot
    try:
        tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
    except Exception as e:
        print(f"❌ Ошибка camelot: {e}")
        return {"__legend__": []}

    current_group = None

    for table in tables:
        df = table.df
        for _, row in df.iterrows():
            raw_cell = str(row.tolist()[0])
            if not raw_cell or raw_cell == "nan":
                continue

            lines = raw_cell.split("\n")

            for line in lines:
                line = line.strip()
                if not line or "─" in line or "├" in line:
                    continue

                parts = line.split("│")
                if parts and parts[0].strip() == "":
                    parts = parts[1:]
                if parts and parts[-1].strip() == "":
                    parts = parts[:-1]
                
                cells = [_clean(p) for p in parts]
                if len(cells) < 2:
                    continue

                first_cell = cells[0]
                gm = GROUP_NUM_RE.search(first_cell)
                if gm:
                    current_group = gm.group(1)
                
                if not current_group:
                    continue

                lesson_cell = cells[1] if len(cells) > 1 else ""
                if not LESSON_NUM_RE.match(lesson_cell):
                    continue

                lesson_num = int(lesson_cell)
                
                new_subj_raw = parts[2] if len(parts) > 2 else ""
                new_teacher_raw = parts[4] if len(parts) > 4 else ""
                old_subj_raw = parts[5] if len(parts) > 5 else ""
                old_teacher_raw = parts[7] if len(parts) > 7 else ""

                new_subj = _clean(new_subj_raw)
                old_subj = _clean(old_subj_raw)
                
                new_teacher = _extract_teachers(new_teacher_raw)
                old_teacher = _extract_teachers(old_teacher_raw)

                is_cancelled = bool(CANCELLED_RE.search(new_subj))
                
                if GALOCHKA_RE.match(new_subj): new_subj = ""
                if GALOCHKA_RE.match(old_subj): old_subj = ""

                current_lesson = {
                    "lesson": lesson_num,
                    "new_subject": "" if is_cancelled else new_subj,
                    "new_teacher": "" if is_cancelled else new_teacher,
                    "old_subject": old_subj,
                    "old_teacher": old_teacher,
                    "cancelled": is_cancelled,
                }
                
                if current_group not in result:
                    result[current_group] = []
                result[current_group].append(current_lesson)

    # 2. Парсим легенду
    result["__legend__"] = _parse_legend(pdf_path)

    return dict(result)

# --- ФОРМАТИРОВАНИЕ (оставь как было) ---
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
            if z.get("old_subject") or z.get("old_teacher"):
                old = f"\n   _был: {z.get('old_subject', '—')}"
                if z.get("old_teacher"):
                    old += f" — {z['old_teacher']}"
                old += "_"
            lines.append(f"{header}\n⏸ УРОК СНЯТ{old}")
            lines.append("")
            continue

        block = [header]
        new_line = f"🔄 {z.get('new_subject', '—')}"
        if z.get("new_teacher"):
            new_line += f" — {z['new_teacher']}"
        block.append(new_line)

        if z.get("old_subject") or z.get("old_teacher"):
            old_line = f"❌ _вместо_ {z.get('old_subject', '—')}"
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