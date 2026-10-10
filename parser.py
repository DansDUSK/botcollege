import pdfplumber
import re
from collections import defaultdict


GROUP_NUM_RE = re.compile(r"^\d{3,4}$")
LESSON_NUM_RE = re.compile(r"^\d{1,2}$")
GALOCHKA_RE = re.compile(r"^[√✓vV]+$")
CANCELLED_RE = re.compile(r"[Уу]рок\s+снят", re.IGNORECASE)

LEGEND_RE = re.compile(
    r"("
    r"[А-ЯЁ][а-яё\-]+\s+[А-ЯЁ]\.\s?[А-ЯЁ]?\.?\s*"
    r")?"
    r"\d{2,3}[А-Я]?\s*\([\d,\-\s]+\)"
)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" .")


def _split_row(line: str) -> list[str]:
    parts = line.split("│")
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [_clean(p) for p in parts]


def _merge(old: str, new: str) -> str:
    if not new or new == "√":
        return old
    if not old:
        return new
    if new in old:
        return old
    if old in new:
        return new
    return f"{old}, {new}"


def _extract_legend_from_line(line: str, legend_lines: list[str]) -> None:
    parts = re.split(r"[│┤]", line)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        for m in LEGEND_RE.finditer(part):
            text = m.group(0).strip()
            if not text:
                continue
            if text[0].isdigit() and legend_lines:
                if text not in legend_lines[-1]:
                    legend_lines[-1] = f"{legend_lines[-1]}, {text}"
            elif text not in legend_lines:
                legend_lines.append(text)


def parse_pdf(pdf_path: str) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = defaultdict(list)
    legend_lines: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    current_group: str | None = None
    current_lesson: dict | None = None

    for raw_line in full_text.split("\n"):
        line = raw_line.strip()

        if not line:
            continue
        _extract_legend_from_line(line, legend_lines)

        if "─" in line or line.startswith("┌") or line.startswith("└"):
            continue

        if "│" not in line:
            continue

        cells = _split_row(line)
        if len(cells) < 2:
            continue

        first_cell = cells[0]

        if any(kw in line for kw in ["Замена", "расписанию", "Предмет", "Преподаватель"]):
            continue
        if first_cell in ("No", "гр.", "ур"):
            continue

        if GROUP_NUM_RE.match(first_cell):
            current_group = first_cell
            current_lesson = None

        if current_group is None:
            continue

        cleaned_cells = []
        for cell in cells:
            cell_stripped = cell.strip()
            if cell_stripped and LEGEND_RE.search(cell_stripped):
                continue
            cleaned_cells.append(cell)
        cells = cleaned_cells

        rest = cells[1:]
        if len(rest) < 1:
            continue

        lesson_cell = rest[0] if len(rest) > 0 else ""
        new_subj    = rest[1] if len(rest) > 1 else ""
        new_aud     = rest[2] if len(rest) > 2 else ""
        new_teacher = rest[3] if len(rest) > 3 else ""
        old_subj    = rest[4] if len(rest) > 4 else ""
        old_aud     = rest[5] if len(rest) > 5 else ""
        old_teacher = rest[6] if len(rest) > 6 else ""

        if GALOCHKA_RE.match(new_subj):
            new_subj = ""
        if GALOCHKA_RE.match(old_subj):
            old_subj = ""

        if LESSON_NUM_RE.match(lesson_cell):
            lesson_num = int(lesson_cell)
            cancelled = bool(CANCELLED_RE.search(new_subj))

            current_lesson = {
                "lesson": lesson_num,
                "new_subject": new_subj if not cancelled else "",
                "new_teacher": new_teacher if not cancelled else "",
                "old_subject": old_subj,
                "old_teacher": old_teacher,
                "cancelled": cancelled,
                "unchanged": False,
            }
            result[current_group].append(current_lesson)
            continue

        if current_lesson is None:
            continue

        if GALOCHKA_RE.match(new_subj) and not current_lesson["cancelled"]:
            current_lesson["unchanged"] = True

        current_lesson["new_subject"] = _merge(current_lesson["new_subject"], new_subj)
        current_lesson["new_teacher"] = _merge(current_lesson["new_teacher"], new_teacher)
        current_lesson["old_subject"] = _merge(current_lesson["old_subject"], old_subj)
        current_lesson["old_teacher"] = _merge(current_lesson["old_teacher"], old_teacher)

    result["__legend__"] = legend_lines
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