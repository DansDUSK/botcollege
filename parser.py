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


def _clean(s: str) -> str:
    if not s: return ""
    s = s.replace("│", "").replace("┼", "").replace("─", "").replace("┤", "")
    s = s.replace("┌", "").replace("┐", "").replace("└", "").replace("┘", "")
    s = s.replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip(" .")


def _extract_teachers(raw_text: str) -> str:
    if not raw_text:
        return ""
    matches = TEACHER_RE.findall(raw_text)
    teachers = []
    for surname, initials in matches:
        t = f"{surname} {initials.replace(' ', '')}"
        if t not in teachers:
            teachers.append(t)
    return ", ".join(teachers)


def _parse_legend(pdf_path: str) -> list[str]:
    legend = []
    legend_teachers = set()
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.split("\n"):
                    s = line.replace("│", " ").replace("┼", " ").replace("─", " ").replace("┤", " ")
                    s = s.replace("┌", " ").replace("┐", " ").replace("└", " ").replace("┘", " ")
                    s = re.sub(r"\s+", " ", s).strip()
                    
                    if not s:
                        continue
                    
                    matches = re.findall(
                        r"([А-ЯЁ][а-яё\-]+\s+[А-ЯЁ]\.\s?[А-ЯЁ]?\.?)\s+([\dА-Яа-яё\-\.]+?)\s*\(([\d,\-\s]+)\)",
                        s
                    )
                    for m in matches:
                        teacher = m[0].strip()
                        room = m[1].strip()
                        lessons = m[2].strip()
                        if teacher not in legend_teachers:
                            item = f"{teacher} — {room} ({lessons})"
                            legend.append(item)
                            legend_teachers.add(teacher)
                    
                    if "Поликарпова" in line and "Поликарпова" not in legend_teachers:
                        match = re.search(
                            r"(Поликарпова\s+[А-ЯЁ]\.\s?[А-ЯЁ]?\.?)\s+([\dА-Яа-яё\-\.]+?)\s*\(([\dА-Яа-яё,\-\s]+)\)",
                            line
                        )
                        if match:
                            teacher = match.group(1).strip()
                            room = match.group(2).strip()
                            lessons = match.group(3).strip()
                            item = f"{teacher} — {room} ({lessons})"
                            legend.append(item)
                            legend_teachers.add(teacher)
    except Exception as e:
        print(f"❌ Ошибка легенды: {e}")
    
    # Удаляем артефакты
    unwanted = ["Степанова Т.В.", "Дайнеко И.А."]
    legend = [item for item in legend if not any(u in item for u in unwanted)]
    
    # Умная проверка для Прокопьевой
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.split("\n"):
                    if "Прокопьева" in line and "115" in line:
                        for i, item in enumerate(legend):
                            if "Прокопьева Е.А." in item and "115" not in item:
                                legend[i] = "Прокопьева Е.А. — 402 (1-4), 115 (5-6)"
                                break
                        break
    except Exception as e:
        print(f"❌ Ошибка проверки Прокопьевой: {e}")
    
    return legend


def parse_pdf(pdf_path: str) -> dict[str, list[dict]]:
    result = defaultdict(list)
    
    try:
        tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
    except Exception as e:
        print(f"❌ Ошибка camelot: {e}")
        return {"__legend__": []}

    current_group = None
    current_lesson = None

    for table in tables:
        df = table.df
        for _, row in df.iterrows():
            raw_cell = str(row.tolist()[0])
            if not raw_cell or raw_cell == "nan":
                continue

            for line in raw_cell.split("\n"):
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

                gm = GROUP_NUM_RE.search(cells[0])
                if gm:
                    current_group = gm.group(1)
                
                if not current_group:
                    continue

                lesson_cell = cells[1] if len(cells) > 1 else ""
                is_new_lesson = bool(LESSON_NUM_RE.match(lesson_cell))
                
                if is_new_lesson:
                    lesson_num = int(lesson_cell)
                    current_lesson = {
                        "lesson": lesson_num,
                        "new_subject": "",
                        "new_teacher": "",
                        "old_subject": "",
                        "old_teacher": "",
                        "cancelled": False,
                    }
                    result[current_group].append(current_lesson)
                else:
                    if current_lesson is None:
                        continue
                
                new_subj = _clean(parts[2]) if len(parts) > 2 else ""
                new_teach = _extract_teachers(parts[4]) if len(parts) > 4 else ""
                old_subj = _clean(parts[5]) if len(parts) > 5 else ""
                old_teach = _extract_teachers(parts[7]) if len(parts) > 7 else ""

                if not is_new_lesson:
                    if new_subj and new_subj not in current_lesson["new_subject"]:
                        current_lesson["new_subject"] = (current_lesson["new_subject"] + ", " + new_subj).strip(", ")
                    if new_teach and new_teach not in current_lesson["new_teacher"]:
                        current_lesson["new_teacher"] = (current_lesson["new_teacher"] + ", " + new_teach).strip(", ")
                    if old_subj and old_subj not in current_lesson["old_subject"]:
                        current_lesson["old_subject"] = (current_lesson["old_subject"] + ", " + old_subj).strip(", ")
                    if old_teach and old_teach not in current_lesson["old_teacher"]:
                        current_lesson["old_teacher"] = (current_lesson["old_teacher"] + ", " + old_teach).strip(", ")
                else:
                    current_lesson["new_subject"] = new_subj
                    current_lesson["new_teacher"] = new_teach
                    current_lesson["old_subject"] = old_subj
                    current_lesson["old_teacher"] = old_teach

                if CANCELLED_RE.search(new_subj):
                    current_lesson["cancelled"] = True

    # Чистим галочки (даже если они внутри строки)
    for group in result:
        for l in result[group]:
            l["new_subject"] = re.sub(r"\s*[√✓vV]\s*", "", l["new_subject"]).strip(", ")
            l["old_subject"] = re.sub(r"\s*[√✓vV]\s*", "", l["old_subject"]).strip(", ")
            
            if l["cancelled"]:
                l["new_subject"] = ""
                l["new_teacher"] = ""

    result["__legend__"] = _parse_legend(pdf_path)
    return dict(result)


# --- ФОРМАТИРОВАНИЕ ---
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
    for item in legend:
        lines.append(f"• {item}")
    return "\n".join(lines)
