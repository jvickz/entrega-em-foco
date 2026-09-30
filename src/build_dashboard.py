"""Create the action-focused 2024 delivery operations dashboard."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from html import escape
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TEMPLATE = ROOT / "dashboard_template.html"
MONTHS = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho"]
CAUSES = [
    "Descumprimento da roteirização",
    "Absenteísmo de motorista/ajudantes",
    "Pagamento de diárias",
    "Atraso na liberação da carga",
    "Veículos em manutenção",
    "Outros",
    "Sem causa identificada",
]
CAUSE_SHORT = [
    "Roteirização",
    "Ausência de motorista/ajudante",
    "Pagamento de diárias",
    "Liberação da carga",
    "Manutenção de veículos",
    "Outros",
    "Sem causa identificada",
]
PRE_DISPATCH_CAUSES = (
    "Roteirização",
    "Ausência de motorista/ajudante",
    "Pagamento de diárias",
)
PORTUGUESE_MONTHS = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
}


def normalized(text: object) -> str:
    value = unicodedata.normalize("NFKD", str(text))
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    return "".join(char for char in value if char.isalnum())


def as_int(value: object) -> int:
    number = pd.to_numeric(value, errors="coerce")
    return int(number) if pd.notna(number) else 0


def workbook_by_name(keyword: str) -> Path:
    wanted = normalized(keyword)
    for path in RAW.glob("*.xlsx"):
        if wanted in normalized(path.name):
            return path
    raise FileNotFoundError(f"Não encontrei a planilha {keyword!r} em {RAW}")


def sheet_by_name(path: Path, keyword: str) -> str:
    wanted = normalized(keyword)
    for name in pd.ExcelFile(path).sheet_names:
        if wanted in normalized(name):
            return name
    raise ValueError(f"A planilha {path.name} não tem uma aba compatível com {keyword!r}")


def daily_monthly(path: Path, sheet_key: str) -> pd.DataFrame:
    sheet = sheet_by_name(path, sheet_key)
    frame = pd.read_excel(path, sheet_name=sheet).dropna(how="all").copy()
    if frame.shape[1] < 4:
        raise ValueError(f"A aba {sheet} precisa conter data, total e dois resultados.")
    date_column = frame.columns[0]
    frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
    frame = frame.dropna(subset=[date_column])
    frame["_month"] = frame[date_column].dt.month
    numeric = [column for column in frame.columns[1:] if column != "_month"]
    if len(numeric) < 3:
        raise ValueError(f"Não encontrei as três colunas de contagem na aba {sheet}.")
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce").fillna(0)
    totals = frame.groupby("_month")[numeric].sum().reset_index()
    return totals


def forecast_data(path: Path, sheet_key: str, window: int = 5) -> dict[str, object]:
    """Build a transparent next-record forecast and a chronological holdout."""
    sheet = sheet_by_name(path, sheet_key)
    frame = pd.read_excel(path, sheet_name=sheet).dropna(how="all").copy()
    frame.iloc[:, 0] = pd.to_datetime(frame.iloc[:, 0], errors="coerce")
    frame = frame.dropna(subset=[frame.columns[0]]).sort_values(frame.columns[0]).reset_index(drop=True)
    if frame.shape[1] < 4:
        raise ValueError(f"A aba {sheet} precisa conter data, total, no prazo e atrasadas.")

    observations = frame.iloc[:, :4].copy()
    observations.columns = ["date", "trips", "on_time", "late"]
    observations[["trips", "on_time", "late"]] = observations[["trips", "on_time", "late"]].apply(
        pd.to_numeric, errors="coerce"
    ).fillna(0)
    observations = observations[observations["trips"] > 0].reset_index(drop=True)
    if len(observations) < 2 * window + 5:
        raise ValueError("A série diária é curta demais para a previsão e a validação temporal.")

    holdout_size = math.ceil(len(observations) * 0.2)
    split_at = len(observations) - holdout_size
    actual: list[float] = []
    predictions: list[float] = []
    naive_predictions: list[float] = []
    for index in range(split_at, len(observations)):
        history = observations["late"].iloc[index - window : index]
        actual.append(float(observations.at[index, "late"]))
        predictions.append(float(history.mean()))
        naive_predictions.append(float(observations.at[index - 1, "late"]))

    y = pd.Series(actual, dtype="float64")
    pred = pd.Series(predictions, dtype="float64")
    naive = pd.Series(naive_predictions, dtype="float64")
    mae = float((y - pred).abs().mean())
    naive_mae = float((y - naive).abs().mean())
    actual_total = max(1.0, float(y.sum()))
    latest = observations.tail(window)
    observations["late_rate"] = observations["late"] / observations["trips"]
    high_delay_days = observations[observations["late_rate"] > 0.15]
    high_delay_late = int(high_delay_days["late"].sum())

    return {
        "as_of": observations.iloc[-1]["date"].strftime("%d/%m/%Y"),
        "window_records": window,
        "next_record_late_forecast": round(float(latest["late"].mean()), 1),
        "recent_rate": round(100 * float(latest["late"].sum()) / max(1.0, float(latest["trips"].sum())), 1),
        "recent_daily_trips": round(float(latest["trips"].mean()), 1),
        "validation_records": holdout_size,
        "validation_mae": round(mae, 2),
        "naive_mae": round(naive_mae, 2),
        "mae_improvement_pct": round(100 * (naive_mae - mae) / naive_mae, 1) if naive_mae else 0,
        "validation_wape": round(100 * float((y - pred).abs().sum()) / actual_total, 1),
        "naive_wape": round(100 * float((y - naive).abs().sum()) / actual_total, 1),
        "observations": len(observations),
        "high_delay_days": len(high_delay_days),
        "high_delay_day_share": round(100 * len(high_delay_days) / len(observations), 1),
        "high_delay_late": high_delay_late,
        "high_delay_late_share": round(
            100 * high_delay_late / max(1, int(observations["late"].sum())),
            1,
        ),
    }


def cause_data(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    sheet = sheet_by_name(path, "frequenciacausas")
    frame = pd.read_excel(path, sheet_name=sheet).dropna(how="all").copy()
    cause_counts: dict[str, int] = {label: 0 for label in CAUSE_SHORT}
    monthly: list[dict[str, object]] = []

    for _, row in frame.iterrows():
        month_name = normalized(row.iloc[0])
        month_number = PORTUGUESE_MONTHS.get(month_name)
        if not month_number:
            continue
        values = [as_int(row.iloc[index]) for index in range(2, 9)]
        for label, count in zip(CAUSE_SHORT, values):
            cause_counts[label] += count
        monthly.append(
            {
                "month": month_number,
                "label": MONTHS[month_number - 1],
                "logged_delay_incidents": as_int(row.iloc[1]),
                "cause_counts": values,
            }
        )

    total = sum(cause_counts.values())
    causes = [
        {
            "label": label,
            "count": count,
            "share": round(100 * count / total, 1) if total else 0.0,
        }
        for label, count in cause_counts.items()
    ]
    causes.sort(key=lambda item: (-int(item["count"]), str(item["label"])))
    return causes, monthly


def compile_data() -> dict[str, object]:
    order_path = workbook_by_name("Dados Pedido Perfeito")
    trip_path = workbook_by_name("Dados Viagem Perfeita")
    problem_path = workbook_by_name("Dados problemas e causas")

    on_time = daily_monthly(order_path, "entreganoprazo")
    forecast = forecast_data(order_path, "entreganoprazo")
    error_free = daily_monthly(order_path, "entregasem erros")
    complete = daily_monthly(order_path, "entregascompletas")
    metric_frames = []
    for data, names in (
        (on_time, ("trips", "on_time", "late")),
        (error_free, ("error_total", "error_free", "with_error")),
        (complete, ("complete_total", "complete", "incomplete")),
    ):
        data = data.rename(
            columns={
                data.columns[0]: "month",
                data.columns[1]: names[0],
                data.columns[2]: names[1],
                data.columns[3]: names[2],
            }
        )
        metric_frames.append(data)
    merged = metric_frames[0]
    for data in metric_frames[1:]:
        merged = merged.merge(data, on="month", how="outer", validate="one_to_one")
    merged = merged.sort_values("month").fillna(0)

    monthly: list[dict[str, object]] = []
    for row in merged.itertuples(index=False):
        month = int(row.month)
        trips = int(row.trips)
        monthly.append(
            {
                "month": month,
                "label": MONTHS[month - 1],
                "trips": trips,
                "on_time": int(row.on_time),
                "late": int(row.late),
                "on_time_rate": round(100 * row.on_time / trips, 2) if trips else 0.0,
                "error_total": int(row.error_total),
                "error_free": int(row.error_free),
                "with_error": int(row.with_error),
                "error_free_rate": round(100 * row.error_free / row.error_total, 2)
                if row.error_total
                else 0.0,
                "complete_total": int(row.complete_total),
                "complete": int(row.complete),
                "incomplete": int(row.incomplete),
                "complete_rate": round(100 * row.complete / row.complete_total, 2)
                if row.complete_total
                else 0.0,
            }
        )

    causes, cause_monthly = cause_data(problem_path)
    cause_count_by_label = {
        str(row["label"]): int(row["count"])
        for row in causes
    }
    total_trips = sum(int(row["trips"]) for row in monthly)
    total_late = sum(int(row["late"]) for row in monthly)
    cause_records = sum(int(row["count"]) for row in causes)
    logged_delay_incidents = sum(int(row["logged_delay_incidents"]) for row in cause_monthly)
    top_three = sum(int(row["count"]) for row in causes[:3])
    pre_dispatch_count = sum(cause_count_by_label.get(label, 0) for label in PRE_DISPATCH_CAUSES)
    unidentified_count = cause_count_by_label.get("Sem causa identificada", 0)
    pre_dispatch_active_months = sum(
        1
        for row in cause_monthly
        if sum(
            int(row["cause_counts"][CAUSE_SHORT.index(label)])
            for label in PRE_DISPATCH_CAUSES
        )
        > 0
    )
    april = next((row for row in monthly if row["month"] == 4), None)
    june = next((row for row in monthly if row["month"] == 6), None)

    # The second workbook covers Jul–Dec. Its reported trip count is used only
    # to flag a disagreement with the repository's full-year metadata.
    second_half = daily_monthly(trip_path, "viagem atenderam")
    h2_trips = int(second_half.iloc[:, 1].sum())
    metadata_trip_count = 2637

    quality_note = (
        f"A tabela de desempenho registra {total_late:,} entregas atrasadas; "
        f"a tabela de ocorrências registra {logged_delay_incidents:,} eventos classificados como atraso. "
        "As tabelas não permitem conciliar esses registros por viagem."
    )
    metadata_note = (
        f"A página da fonte descreve {metadata_trip_count:,} viagens em 2024, mas as planilhas somam "
        f"{total_trips:,} no 1º semestre e {h2_trips:,} no 2º semestre. "
        "A análise principal fica restrita ao 1º semestre, que tem a tabela de causas correspondente."
    )

    return {
        "summary": {
            "period": "Jan–Jun 2024",
            "company_type": "Transportadora rodoviária brasileira, anonimizada",
            "trips": total_trips,
            "late": total_late,
            "on_time": total_trips - total_late,
            "late_rate": round(100 * total_late / total_trips, 2) if total_trips else 0,
            "on_time_rate": round(100 * (total_trips - total_late) / total_trips, 2)
            if total_trips
            else 0,
            "error_free_rate": round(
                100
                * sum(int(row["error_free"]) for row in monthly)
                / max(1, sum(int(row["error_total"]) for row in monthly)),
                2,
            ),
            "complete_rate": round(
                100
                * sum(int(row["complete"]) for row in monthly)
                / max(1, sum(int(row["complete_total"]) for row in monthly)),
                2,
            ),
            "cause_records": cause_records,
            "logged_delay_incidents": logged_delay_incidents,
            "top_three_cause_records": top_three,
            "top_three_cause_share": round(100 * top_three / cause_records, 1)
            if cause_records
            else 0,
            "pre_dispatch_cause_count": pre_dispatch_count,
            "pre_dispatch_cause_share": round(100 * pre_dispatch_count / cause_records, 1)
            if cause_records
            else 0,
            "pre_dispatch_active_months": pre_dispatch_active_months,
            "unidentified_cause_count": unidentified_count,
            "unidentified_cause_share": round(100 * unidentified_count / cause_records, 1)
            if cause_records
            else 0,
            "april_on_time_rate": april["on_time_rate"] if april else 0,
            "june_on_time_rate": june["on_time_rate"] if june else 0,
            "april_to_june_drop_pp": round(
                float(april["on_time_rate"]) - float(june["on_time_rate"]), 1
            )
            if april and june
            else 0,
            "incident_gap": total_late - logged_delay_incidents,
            "source_metadata_trip_count": metadata_trip_count,
            "second_half_trip_count": h2_trips,
        },
        "monthly": monthly,
        "forecast": forecast,
        "causes": causes,
        "cause_monthly": cause_monthly,
        "data_quality": [quality_note, metadata_note],
        "source": {
            "title": "Data Set Perfect Trip",
            "doi": "10.17632/jn2dcs2m77.1",
            "url": "https://data.mendeley.com/datasets/jn2dcs2m77/1",
            "license": "CC BY 4.0",
        },
    }


def br_number(value: object) -> str:
    return f"{int(value):,}".replace(",", ".")


def br_decimal(value: object) -> str:
    return f"{float(value):.1f}".replace(".", ",")


def br_percent(value: object) -> str:
    return f"{br_decimal(value)}%"


def replace_inner(html: str, element_id: str, content: str) -> str:
    """Replace one element body while retaining the template's tag and attributes."""
    pattern = re.compile(
        rf'(<(?P<tag>[a-zA-Z0-9]+)\b[^>]*\bid="{re.escape(element_id)}"[^>]*>).*?(</(?P=tag)>)',
        re.DOTALL,
    )
    updated, replacements = pattern.subn(rf"\g<1>{content}\g<3>", html, count=1)
    if replacements != 1:
        raise ValueError(f"Não foi possível preencher o elemento #{element_id}.")
    return updated


def monthly_chart(data: dict[str, object]) -> str:
    rows = data["monthly"]
    width, height, left, right, top, bottom = 560, 226, 37, 9, 16, 38
    minimum, maximum = 65, 100
    chart_height = height - top - bottom
    chart_width = width - left - right

    def y(value: float) -> float:
        return top + (maximum - value) / (maximum - minimum) * chart_height

    parts = [f'<svg viewBox="0 0 {width} {height}" role="presentation">']
    for tick in (70, 80, 90, 100):
        tick_y = y(tick)
        parts.append(
            f'<line x1="{left}" x2="{width - right}" y1="{tick_y:.2f}" y2="{tick_y:.2f}" '
            'stroke="#dfe3db" stroke-width="1"/>'
            f'<text x="{left - 8}" y="{tick_y + 3:.2f}" text-anchor="end" '
            f'fill="#79837c" font-size="9">{tick}</text>'
        )
    band = chart_width / len(rows)
    for index, row in enumerate(rows):
        bar_width = min(48, band * 0.54)
        x = left + band * index + (band - bar_width) / 2
        bar_y = y(float(row["on_time_rate"]))
        fill = "#f16f56" if index == len(rows) - 1 else ("#123c2d" if index == 3 else "#82968a")
        label = escape(str(row["label"]))[:3]
        parts.append(
            f'<rect x="{x:.2f}" y="{bar_y:.2f}" width="{bar_width:.2f}" '
            f'height="{height - bottom - bar_y:.2f}" fill="{fill}"/>'
            f'<text x="{x + bar_width / 2:.2f}" y="{bar_y - 7:.2f}" text-anchor="middle" '
            f'fill="#33443a" font-size="10" font-weight="700">{br_percent(row["on_time_rate"])}</text>'
            f'<text x="{x + bar_width / 2:.2f}" y="{height - 12}" text-anchor="middle" '
            f'fill="#758078" font-size="9">{label}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def hydrate_html(template: str, data: dict[str, object]) -> str:
    """Pre-render content so the portfolio remains complete without JavaScript."""
    summary = data["summary"]
    forecast = data["forecast"]
    values = {
        "hero-priority-share": br_percent(summary["pre_dispatch_cause_share"]),
        "decision-priority-count": br_number(summary["pre_dispatch_cause_count"]),
        "decision-cause-total": br_number(summary["cause_records"]),
        "late-count": br_number(summary["late"]),
        "late-share": f'{br_percent(summary["late_rate"])} das {br_number(summary["trips"])} viagens',
        "on-time-rate": br_percent(summary["on_time_rate"]),
        "on-time-detail": f'{br_number(summary["on_time"])} entregas no prazo',
        "critical-days": f'{br_number(forecast["high_delay_days"])}/{br_number(forecast["observations"])}',
        "critical-days-detail": f'{br_percent(forecast["high_delay_late_share"])} dos atrasos em dias &gt;15%',
        "unknown-cause-count": br_number(summary["unidentified_cause_count"]),
        "unknown-cause-share": f'{br_percent(summary["unidentified_cause_share"])} das causas',
        "root-late-count": br_number(summary["late"]),
        "root-late-rate": br_percent(summary["late_rate"]),
        "root-priority-share": br_percent(summary["pre_dispatch_cause_share"]),
        "root-priority-count": br_number(summary["pre_dispatch_cause_count"]),
        "scenario-base-count": br_number(summary["pre_dispatch_cause_count"]),
        "scenario-result": br_number(round(summary["pre_dispatch_cause_count"] * 0.75 * 0.50)),
        "forecast-next": br_decimal(forecast["next_record_late_forecast"]),
        "forecast-window": br_number(forecast["window_records"]),
        "forecast-as-of": escape(str(forecast["as_of"])),
        "forecast-mae": br_decimal(forecast["validation_mae"]),
        "forecast-improvement": br_percent(forecast["mae_improvement_pct"]),
        "forecast-observations": br_number(forecast["observations"]),
        "cause-total": br_number(summary["cause_records"]),
        "unknown-cause-callout": br_number(summary["unidentified_cause_count"]),
        "quality-on-time": br_percent(summary["on_time_rate"]),
        "quality-on-time-detail": f'{br_number(summary["on_time"])} de {br_number(summary["trips"])} viagens',
        "error-free-rate": br_percent(summary["error_free_rate"]),
        "complete-rate": br_percent(summary["complete_rate"]),
    }
    for element_id, content in values.items():
        template = replace_inner(template, element_id, content)

    recommendations = [
        {
            "window": "T−12h · planejamento",
            "signal": "Rota sem versão ou ETA validado",
            "copy": "Criar um contrato de rota: versão planejada, ETA e corredor geográfico. Desvio só vira alerta acima da tolerância; o motivo é estruturado para separar bloqueio, segurança, cliente e falha de planejamento.",
            "owner": "Dono da exceção · Planejamento logístico",
            "metric": "% de viagens com rota validada antes da saída",
        },
        {
            "window": "T−24h e T−2h · escala",
            "signal": "Equipe ainda não confirmada",
            "copy": "Usar confirmação em dois tempos e um banco de cobertura acionável. A ausência vira uma exceção com motivo padronizado e tempo até a substituição — sem transformar o dado em punição automática.",
            "owner": "Dono da exceção · Escala operacional",
            "metric": "% de equipes confirmadas até T−2h",
        },
        {
            "window": "T−2h · financeiro",
            "signal": "Diária sem comprovação de liberação",
            "copy": "Pré-validar a diária antes da carga e usar pagamento digital rastreável. Pendências entram em uma fila com SLA, responsável e evidência de liberação; “solicitado” não vale como “pago”.",
            "owner": "Dono da exceção · Financeiro + operações",
            "metric": "% de diárias comprovadas até T−2h",
        },
    ]
    priority_labels = ["Roteirização", "Ausência de motorista/ajudante", "Pagamento de diárias"]
    causes_by_label = {str(row["label"]): row for row in data["causes"]}
    actions = []
    for index, (label, recommendation) in enumerate(zip(priority_labels, recommendations), start=1):
        cause = causes_by_label[label]
        actions.append(
            '<article class="action"><div class="action-top">'
            f'<span class="action-step">{index:02d}</span><span class="action-window">{escape(recommendation["window"])}</span>'
            f'</div><h3>{escape(label)}</h3><p class="action-count">{br_number(cause["count"])} registros · '
            f'{br_percent(cause["share"])} das causas</p><p class="action-signal">Sinal de entrada</p>'
            f'<p class="action-copy"><b>{escape(recommendation["signal"])}.</b> {escape(recommendation["copy"])}</p>'
            f'<div class="action-meta"><span>{escape(recommendation["owner"])}</span>'
            f'<strong>Indicador antecedente: {escape(recommendation["metric"])}</strong></div></article>'
        )
    template = replace_inner(template, "action-list", "".join(actions))

    max_cause = max(int(row["count"]) for row in data["causes"])
    cause_rows = []
    for cause in data["causes"]:
        priority = " priority" if cause["label"] in priority_labels else ""
        width = int(cause["count"]) / max_cause * 100
        cause_rows.append(
            f'<div class="cause-row"><span class="cause-name">{escape(str(cause["label"]))}</span>'
            f'<div class="cause-track"><div class="cause-fill{priority}" style="width:{width:.2f}%"></div></div>'
            f'<span class="cause-value">{br_number(cause["count"])} · {br_percent(cause["share"])}</span></div>'
        )
    template = replace_inner(template, "cause-list", "".join(cause_rows))
    template = replace_inner(template, "monthly-chart", monthly_chart(data))
    template = replace_inner(
        template,
        "monthly-takeaway",
        f'<strong>Leitura:</strong> a pontualidade saiu de {br_percent(summary["april_on_time_rate"])} em abril para '
        f'{br_percent(summary["june_on_time_rate"])} em junho — queda de {br_decimal(summary["april_to_june_drop_pp"])} pontos percentuais.',
    )
    template = replace_inner(
        template,
        "cause-takeaway",
        f'<strong>Decisão:</strong> {br_number(summary["pre_dispatch_cause_count"])} registros de rota, equipe e diária entram na primeira fila do gate. '
        f'Os três sinais aparecem em todos os {br_number(summary["pre_dispatch_active_months"])} meses analisados.',
    )
    quality = "".join(f"<p>{escape(str(note))}</p>" for note in data["data_quality"])
    quality += (
        "<p><b>O desenho proposto:</b> registrar <em>trip_id</em>, horário da pendência, área responsável, decisão e resultado de entrega. "
        "Isso permite associar sinais a desfechos e calibrar um modelo individual apenas quando houver dados suficientes.</p>"
    )
    return replace_inner(template, "quality-note", quality)


def main() -> None:
    data = compile_data()
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    data_json = data_json.replace("<", "\\u003c")
    html = hydrate_html(TEMPLATE.read_text(encoding="utf-8"), data)
    html = html.replace("__PROJECT_DATA__", data_json)
    output = ROOT / "dashboard.html"
    output.write_text(html, encoding="utf-8")
    index_output = ROOT / "index.html"
    index_output.write_text(html, encoding="utf-8")
    portfolio_output = ROOT / "portfolio_joao_vitor_marinho.html"
    portfolio_output.write_text(html, encoding="utf-8")

    summary = data["summary"]
    forecast = data["forecast"]
    print(f"Painel atualizado: {output}")
    print(f"Página para GitHub Pages atualizada: {index_output}")
    print(f"Portfólio local atualizado: {portfolio_output}")
    print(
        f"Jan–Jun/2024 | {summary['trips']:,} viagens | "
        f"{summary['late']:,} atrasadas ({summary['late_rate']:.2f}%) | "
        f"{summary['top_three_cause_records']:,}/{summary['cause_records']:,} "
        f"registros nas três causas prioritárias ({summary['top_three_cause_share']:.1f}%)."
    )
    print("Somente estatísticas agregadas foram incorporadas ao painel.")
    print(
        f"Previsão média móvel ({forecast['window_records']} registros): "
        f"{forecast['next_record_late_forecast']:.1f} atrasos no próximo registro; "
        f"MAE temporal {forecast['validation_mae']:.2f} vs. "
        f"{forecast['naive_mae']:.2f} do último dia."
    )


if __name__ == "__main__":
    main()
