from __future__ import annotations

import html
import math
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Export Market Intelligence",
    page_icon="▦",
    layout="wide",
    initial_sidebar_state="expanded",
)


OUTPUT_FILES = {
    "ranking": "market_opportunity_ranking_2024.csv",
    "priority": "priority_export_markets_2024.csv",
    "change": "market_opportunity_change_2023_2024.csv",
    "risers": "top_market_opportunity_risers_2024.csv",
    "validation": "final_market_validation_decision_2024.csv",
}

SEGMENT_ORDER = [
    "成熟核心市场",
    "高增长机会市场",
    "常规培育市场",
    "低活跃脉冲市场",
    "低基数暴增市场",
    "边缘沉寂市场",
]

SEGMENT_LABELS_EN = {
    "成熟核心市场": "Mature Core Market",
    "高增长机会市场": "High-growth Opportunity Market",
    "常规培育市场": "Steady Nurture Market",
    "低活跃脉冲市场": "Low-activity Pulse Market",
    "低基数暴增市场": "Low-base Surge Market",
    "边缘沉寂市场": "Peripheral Dormant Market",
    # Historical labels used only in the 2023–2024 dynamics output.
    "低活跃回落市场": "Low-activity Declining Market",
    "边缘脉冲市场": "Peripheral Pulse Market",
}

TIER_LABELS_EN = {
    "重点候选": "Priority Candidate",
    "培育候选": "Nurture Candidate",
    "观察名单": "Watchlist",
    "低优先级": "Low Priority",
}

SEGMENT_COLORS = {
    "成熟核心市场": "#2F6FED",
    "高增长机会市场": "#D97757",
    "常规培育市场": "#3E9B73",
    "低活跃脉冲市场": "#8768A8",
    "低基数暴增市场": "#D6A24A",
    "边缘沉寂市场": "#9AA4B2",
}

DYNAMIC_SEGMENT_COLORS = {
    **SEGMENT_COLORS,
    "低活跃回落市场": "#8768A8",
    "边缘脉冲市场": "#9AA4B2",
}

DIMENSION_LABELS_EN = {
    "size_score": "Size",
    "growth_score": "Growth",
    "momentum_score": "Momentum",
    "stability_score": "Stability",
    "activity_score": "Activity",
}

DIMENSION_LABELS_ZH = {
    "size_score": "规模（Size）",
    "growth_score": "增长（Growth）",
    "momentum_score": "动量（Momentum）",
    "stability_score": "稳定性（Stability）",
    "activity_score": "活跃度（Activity）",
}

SCORE_COLUMNS = list(DIMENSION_LABELS_EN)

PAGE_LABELS = {
    "zh": {
        "global": "全球市场机会",
        "explorer": "市场探索",
        "dynamics": "机会动态",
        "validation": "验证与决策",
    },
    "en": {
        "global": "Global Market Opportunity",
        "explorer": "Market Explorer",
        "dynamics": "Opportunity Dynamics",
        "validation": "Validation & Decision",
    },
}


def t(zh: str, en: str, language: str) -> str:
    """Return the requested UI language, with Chinese as the default."""

    return zh if language == "zh" else en


def localize_segment(value: object, language: str) -> str:
    raw = str(value)
    return raw if language == "zh" else SEGMENT_LABELS_EN.get(raw, raw)


def localize_tier(value: object, language: str) -> str:
    raw = str(value)
    return raw if language == "zh" else TIER_LABELS_EN.get(raw, raw)


def dimension_labels(language: str) -> dict[str, str]:
    return DIMENSION_LABELS_ZH if language == "zh" else DIMENSION_LABELS_EN


def localized_segment_colors(language: str) -> dict[str, str]:
    return {
        localize_segment(raw, language): color
        for raw, color in DYNAMIC_SEGMENT_COLORS.items()
    }


STRATEGY_LABELS_EN = {
    "重点深耕 / 防守优势": "Deepen / Defend Advantage",
    "需求扩张型 / 谨慎验证": "Demand Expansion / Validate Cautiously",
    "重点进攻 / 提升份额": "Prioritize Expansion / Grow Share",
    "选择性拓展 / 控制风险": "Selective Expansion / Control Risk",
}

DECISION_REASON_EN = {
    "France": (
        "2024 imports were about $3.45B, up 14.3% year over year. China supplied about 51.3% of imports, "
        "and China supply growth outpaced the market. The opportunity is to deepen and defend the existing position."
    ),
    "Uzbekistan": (
        "Import demand surged in 2024, while China supplied about 99% of imports. The opportunity comes from local "
        "demand expansion rather than further share capture, so the sustainability of the rapid growth should be validated."
    ),
    "Romania": (
        "The 2024 import market was about $424.8M, up 54.8% year over year. China’s share was only about 16.4%, "
        "while China supply grew 78.9%. This creates room for both market expansion and share growth."
    ),
    "Serbia": (
        "The import market grew 109.7% year over year, and China’s share was about 69.7%. The signal is strong, "
        "but the absolute market size was only about $18.2M, favoring selective expansion over large-scale investment."
    ),
}

DATA_RISK_EN = {
    "France": (
        "The supplier structure is relatively concentrated and China already holds a large share; future growth will "
        "depend more on continued market expansion. Key competing suppliers such as Poland should be monitored."
    ),
    "Uzbekistan": (
        "China’s share is close to 99% and HHI is close to 1. Annual growth is more than tenfold, creating sustainability "
        "risk and single-supplier concentration risk."
    ),
    "Romania": (
        "China’s current share is still low, indicating competitive room. It also means that the leading competing "
        "suppliers and the feasibility of gaining share need to be assessed further."
    ),
    "Serbia": (
        "The absolute market is small and supplier concentration is relatively high. Fast growth may be amplified by "
        "the low-base effect, so scale and volatility require caution."
    ),
}


def localize_strategy(value: object, language: str) -> str:
    raw = str(value)
    return raw if language == "zh" else STRATEGY_LABELS_EN.get(raw, raw)


def localize_validation_text(row: pd.Series, field: str, language: str) -> str:
    if language == "zh":
        return str(row[field])
    if field == "decision_reason":
        return DECISION_REASON_EN.get(str(row["market"]), str(row[field]))
    if field == "data_risk":
        return DATA_RISK_EN.get(str(row["market"]), str(row[field]))
    return str(row[field])


def find_project_root() -> Path:
    """Find the repository root without relying on a machine-specific path."""

    starts = [Path(__file__).resolve().parent, Path.cwd()]
    seen: set[Path] = set()

    for start in starts:
        for candidate in (start, *start.parents):
            candidate = candidate.resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            if (candidate / "notebooks" / "outputs").is_dir():
                return candidate

    # The normal layout is app/app.py below the project root. This fallback
    # keeps the app usable while still avoiding an absolute path.
    return Path(__file__).resolve().parents[1]


def find_output_dir(project_root: Path) -> Path:
    """Find the output directory used by the notebooks."""

    candidates = [
        project_root / "notebooks" / "outputs",
        project_root / "outputs",
        project_root / "data" / "outputs",
    ]

    for candidate in candidates:
        if any((candidate / filename).is_file() for filename in OUTPUT_FILES.values()):
            return candidate

    return candidates[0]


@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    """Load a UTF-8 CSV produced by the analysis notebooks."""

    file_path = Path(path)
    try:
        return pd.read_csv(file_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding="utf-8")


def load_dashboard_data(output_dir: Path) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Load all dashboard inputs and return missing filenames separately."""

    frames: dict[str, pd.DataFrame] = {}
    missing: list[str] = []

    for key, filename in OUTPUT_FILES.items():
        path = output_dir / filename
        if not path.is_file():
            missing.append(filename)
            continue
        frames[key] = load_csv(str(path))

    return frames, missing


def validate_required_columns(
    frames: dict[str, pd.DataFrame],
) -> list[str]:
    required = {
        "ranking": {
            "opportunity_rank",
            "destination",
            "export_2024",
            "market_segment",
            "decision_tier",
            "opportunity_score",
            *SCORE_COLUMNS,
        },
        "change": {
            "destination",
            "score_2023",
            "score_2024",
            "rank_2023",
            "rank_2024",
            "score_change",
            "rank_improvement",
        },
        "risers": {
            "destination",
            "score_2023",
            "score_2024",
            "rank_2023",
            "rank_2024",
            "score_change",
            "rank_improvement",
        },
        "validation": {
            "market",
            "opportunity_rank",
            "market_segment",
            "opportunity_score",
            "total_import_2024",
            "china_share_2024",
            "market_growth",
            "china_growth",
            "share_change",
            "hhi_2024",
            "strategy",
            "decision_reason",
            "data_risk",
            "mirror_gap_pct",
            "mirror_similarity",
        },
    }

    problems: list[str] = []
    for key, columns in required.items():
        if key not in frames:
            continue
        missing = sorted(columns - set(frames[key].columns))
        if missing:
            problems.append(f"{OUTPUT_FILES[key]} 缺少字段：{', '.join(missing)}")
    return problems


def as_number(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if pd.notna(number) else None


def format_money(value: object) -> str:
    number = as_number(value)
    if number is None:
        return "N/A"

    sign = "-" if number < 0 else ""
    amount = abs(number)
    if amount >= 1_000_000_000:
        return f"{sign}${amount / 1_000_000_000:,.2f}B"
    if amount >= 1_000_000:
        return f"{sign}${amount / 1_000_000:,.1f}M"
    if amount >= 1_000:
        return f"{sign}${amount / 1_000:,.1f}K"
    return f"{sign}${amount:,.0f}"


def format_score(value: object) -> str:
    number = as_number(value)
    return "N/A" if number is None else f"{number:,.1f}"


def format_pct(value: object, decimals: int = 1) -> str:
    number = as_number(value)
    return "N/A" if number is None else f"{number * 100:,.{decimals}f}%"


def format_pct_already_scaled(value: object, decimals: int = 1) -> str:
    number = as_number(value)
    return "N/A" if number is None else f"{number:,.{decimals}f}%"


def format_pp(value: object, decimals: int = 1) -> str:
    number = as_number(value)
    return "N/A" if number is None else f"{number * 100:+,.{decimals}f} pp"


def format_signed(value: object, decimals: int = 1) -> str:
    number = as_number(value)
    return "N/A" if number is None else f"{number:+,.{decimals}f}"


def format_rank(value: object) -> str:
    number = as_number(value)
    return "N/A" if number is None else f"#{int(number):,}"


def clean_text(value: object) -> str:
    return html.escape(str(value))


def apply_chart_style(fig: go.Figure, height: int | None = None) -> go.Figure:
    layout = {
        "template": "plotly_white",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "#FFFFFF",
        "font": {"family": "Inter, Segoe UI, Arial, sans-serif", "color": "#1F2937"},
        "margin": {"l": 12, "r": 18, "t": 22, "b": 24},
        "hoverlabel": {"bgcolor": "#14213D", "font": {"color": "#FFFFFF"}},
        "legend": {"orientation": "h", "y": -0.18, "x": 0},
    }
    if height is not None:
        layout["height"] = height
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=True, gridcolor="#E9EEF5", zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


def render_kpis(items: Iterable[tuple[str, str, str | None]]) -> None:
    # Materialize once so the function works with generators too.
    items = list(items)
    columns = st.columns(len(items))
    for column, (label, value, hint) in zip(columns, items):
        hint_html = f'<div class="kpi-hint">{clean_text(hint)}</div>' if hint else ""
        column.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{clean_text(label)}</div>
                <div class="kpi-value">{clean_text(value)}</div>
                {hint_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


def page_header(eyebrow: str, title: str, description: str) -> None:
    st.markdown(f'<div class="eyebrow">{clean_text(eyebrow)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="page-description">{clean_text(description)}</div>', unsafe_allow_html=True)


def render_global_opportunity(ranking: pd.DataFrame, language: str) -> None:
    page_header(
        t("全球市场机会", "GLOBAL MARKET OPPORTUNITY", language),
        t("全球机会格局", "Where the opportunity is concentrated", language),
        t(
            "基于正式分析结果，查看中国 HS850760 出口市场的 2024 Opportunity Score 格局。",
            "A global view of China’s HS850760 export markets, ranked by the supplied 2024 Opportunity Score.",
            language,
        ),
    )

    total_markets = len(ranking)
    priority_markets = int((ranking["decision_tier"] == "重点候选").sum())
    avg_score = ranking["opportunity_score"].mean()
    scored = ranking.dropna(subset=["opportunity_score"]).sort_values("opportunity_rank")
    top_market = scored.iloc[0]["destination"] if not scored.empty else "N/A"

    render_kpis(
        [
            (t("分析市场数", "Markets Analyzed", language), f"{total_markets:,}", t("2024 个目的地市场", "2024 destination markets", language)),
            (t("重点候选市场", "Priority Markets", language), f"{priority_markets:,}", t("决策层级：重点候选", "Decision tier: Priority Candidate", language)),
            (t("平均 Opportunity Score", "Average Opportunity Score", language), format_score(avg_score), t("仅统计有分数市场", "Scored markets only", language)),
            (t("最高机会市场", "Top Opportunity Market", language), str(top_market), t("排名第 1", "Rank 1", language)),
        ]
    )

    missing_scores = int(ranking["opportunity_score"].isna().sum())
    if missing_scores:
        st.info(
            t(
                f"原始排名表保留了 {missing_scores} 个市场，但其 Opportunity Score 缺失；这些市场不会进入按分数排序的图表。",
                f"{missing_scores} markets are retained in the source ranking, but their Opportunity Score is missing; they are excluded from score-ranked charts.",
                language,
            )
        )

    left, right = st.columns([1, 1])
    with left:
        all_option = "__ALL__"
        segment_options = [all_option] + [
            value for value in SEGMENT_ORDER if value in set(ranking["market_segment"].dropna())
        ]
        selected_segment = st.selectbox(
            t("市场类型", "Market segment", language),
            segment_options,
            format_func=lambda value: t("全部", "All", language) if value == all_option else localize_segment(value, language),
            key="global_segment",
        )
    with right:
        tier_values = sorted(ranking["decision_tier"].dropna().unique().tolist())
        selected_tier = st.selectbox(
            t("决策层级", "Decision tier", language),
            [all_option] + tier_values,
            format_func=lambda value: t("全部", "All", language) if value == all_option else localize_tier(value, language),
            key="global_tier",
        )

    filtered = ranking.copy()
    if selected_segment != all_option:
        filtered = filtered[filtered["market_segment"] == selected_segment]
    if selected_tier != all_option:
        filtered = filtered[filtered["decision_tier"] == selected_tier]

    plot_ranking = (
        filtered.dropna(subset=["opportunity_score"])
        .sort_values(["opportunity_score", "destination"], ascending=[False, True])
        .head(15)
        .sort_values("opportunity_score", ascending=True)
    )

    st.markdown(f"#### {t('Top 15 市场机会排名', 'Top 15 Market Opportunity Ranking', language)}")
    if plot_ranking.empty:
        st.warning(t("当前筛选条件下没有可展示的市场。", "No markets are available under the current filters.", language))
    else:
        plot_ranking = plot_ranking.copy()
        plot_ranking["export_2024_display"] = plot_ranking["export_2024"].map(format_money)
        plot_ranking["market_segment_display"] = plot_ranking["market_segment"].map(
            lambda value: localize_segment(value, language)
        )
        plot_ranking["decision_tier_display"] = plot_ranking["decision_tier"].map(
            lambda value: localize_tier(value, language)
        )
        fig = px.bar(
            plot_ranking,
            x="opportunity_score",
            y="destination",
            orientation="h",
            color="market_segment_display",
            color_discrete_map=localized_segment_colors(language),
            text="opportunity_score",
            custom_data=["market_segment_display", "decision_tier_display", "export_2024_display"],
        )
        fig.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>" + t("Opportunity Score", "Opportunity Score", language) + ": %{x:.1f}"
                "<br>" + t("市场类型", "Segment", language) + ": %{customdata[0]}"
                "<br>" + t("决策层级", "Tier", language) + ": %{customdata[1]}"
                "<br>" + t("2024 出口额", "Export 2024", language) + ": %{customdata[2]}<extra></extra>"
            ),
        )
        fig.update_layout(
            showlegend=True,
            xaxis_title="Opportunity Score",
            yaxis_title=t("目的地市场", "Destination market", language),
        )
        fig.update_xaxes(range=[0, 105], dtick=20)
        apply_chart_style(fig, max(440, 30 * len(plot_ranking) + 110))
        st.plotly_chart(fig, width="stretch")

    matrix_col, distribution_col = st.columns([1.65, 1])
    with matrix_col:
        st.markdown(f"#### {t('市场机会矩阵', 'Market Opportunity Matrix', language)}")
        matrix = filtered.dropna(subset=["size_score", "growth_score", "opportunity_score"]).copy()
        if matrix.empty:
            st.warning(t("当前筛选条件下没有可绘制的市场矩阵。", "No markets are available for the matrix under the current filters.", language))
        else:
            matrix["export_2024_display"] = matrix["export_2024"].map(format_money)
            matrix["market_segment_display"] = matrix["market_segment"].map(
                lambda value: localize_segment(value, language)
            )
            log_exports = matrix["export_2024"].map(math.log1p)
            log_min = log_exports.min()
            log_max = log_exports.max()
            if log_max > log_min:
                matrix["bubble_size_display"] = 8 + 34 * (log_exports - log_min) / (log_max - log_min)
            else:
                matrix["bubble_size_display"] = 28
            fig = px.scatter(
                matrix,
                x="size_score",
                y="growth_score",
                size="bubble_size_display",
                color="market_segment_display",
                color_discrete_map=localized_segment_colors(language),
                size_max=42,
                custom_data=[
                    "destination",
                    "opportunity_score",
                    "momentum_score",
                    "stability_score",
                    "export_2024_display",
                ],
            )
            max_bubble_size = matrix["bubble_size_display"].max()
            if max_bubble_size > 0:
                fig.update_traces(marker_sizeref=2 * max_bubble_size / (42**2), marker_sizemode="area")
            fig.update_traces(
                marker={"opacity": 0.78, "line": {"width": 1, "color": "#FFFFFF"}},
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>" + t("Opportunity Score", "Opportunity Score", language) + ": %{customdata[1]:.1f}"
                    "<br>" + t("动量", "Momentum", language) + ": %{customdata[2]:.1f}"
                    "<br>" + t("稳定性", "Stability", language) + ": %{customdata[3]:.1f}"
                    "<br>" + t("2024 出口额", "Export 2024", language) + ": %{customdata[4]}<extra></extra>"
                ),
            )
            fig.update_layout(
                xaxis_title=t("规模评分（Size Score）", "Size Score", language),
                yaxis_title=t("增长评分（Growth Score）", "Growth Score", language),
                showlegend=True,
            )
            fig.update_xaxes(range=[0, 105], dtick=20)
            fig.update_yaxes(range=[0, 105], dtick=20)
            apply_chart_style(fig, 570)
            st.plotly_chart(fig, width="stretch")

    with distribution_col:
        st.markdown(f"#### {t('市场类型分布', 'Market Segment Distribution', language)}")
        distribution = (
            filtered["market_segment"]
            .value_counts()
            .reindex(SEGMENT_ORDER, fill_value=0)
            .rename_axis("market_segment")
            .reset_index(name="markets")
        )
        distribution["market_segment_display"] = distribution["market_segment"].map(
            lambda value: localize_segment(value, language)
        )
        fig = px.bar(
            distribution,
            x="markets",
            y="market_segment_display",
            orientation="h",
            color="market_segment_display",
            color_discrete_map=localized_segment_colors(language),
            text="markets",
        )
        fig.update_traces(
            textposition="outside",
            hovertemplate="%{y}: %{x} " + t("个市场", "markets", language) + "<extra></extra>",
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title=t("市场数量", "Markets", language),
            yaxis_title=t("市场类型", "Market segment", language),
            margin={"l": 12, "r": 30, "t": 22, "b": 24},
        )
        apply_chart_style(fig, 570)
        st.plotly_chart(fig, width="stretch")

    st.caption(
        t(
            "数据来源：market_opportunity_ranking_2024.csv · 评分直接读取正式分析结果。矩阵气泡使用 2024 出口额的对数尺度压缩，仅用于提升可读性。",
            "Source: market_opportunity_ranking_2024.csv · Scores are displayed as supplied by the formal analysis outputs. Matrix bubbles use a log-scaled Export 2024 display size for readability only.",
            language,
        )
    )


def render_market_explorer(ranking: pd.DataFrame, language: str) -> None:
    page_header(
        t("市场探索", "MARKET EXPLORER", language),
        t("为什么这个市场值得关注", "Why this market matters", language),
        t(
            "查看市场 Opportunity Score 背后的五个维度，并与全市场平均水平对比。",
            "Inspect the five score dimensions behind a market’s Opportunity Score and compare them with the global average.",
            language,
        ),
    )

    market_options = (
        ranking.sort_values(["opportunity_rank", "destination"])["destination"].drop_duplicates().tolist()
    )
    default_index = market_options.index("France") if "France" in market_options else 0
    selected_market = st.selectbox(
        t("选择目的地市场", "Select destination", language),
        market_options,
        index=default_index,
    )
    selected_rows = ranking[ranking["destination"] == selected_market]
    if selected_rows.empty:
        st.error(t("找不到所选市场。", "The selected market could not be found.", language))
        return
    selected = selected_rows.iloc[0]

    render_kpis(
        [
            (t("机会排名", "Opportunity Rank", language), format_rank(selected["opportunity_rank"]), t("2024 排名", "2024 ranking", language)),
            (t("Opportunity Score", "Opportunity Score", language), format_score(selected["opportunity_score"]), "0–100"),
            (t("市场类型", "Market Segment", language), localize_segment(selected["market_segment"], language), t("KMeans 市场类型", "KMeans segment label", language)),
            (t("决策层级", "Decision Tier", language), localize_tier(selected["decision_tier"], language), t("组合优先级", "Portfolio priority", language)),
            (t("2024 出口额", "Export 2024", language), format_money(selected["export_2024"]), t("中国报告出口额", "China reported exports", language)),
        ]
    )

    average_scores = ranking[SCORE_COLUMNS].mean()
    labels = dimension_labels(language)
    average_label = t("全市场平均", "Global Average", language)
    comparison_records: list[dict[str, object]] = []
    for column, label in labels.items():
        comparison_records.extend(
            [
                {"Dimension": label, "Series": selected_market, "Score": as_number(selected[column])},
                {"Dimension": label, "Series": average_label, "Score": as_number(average_scores[column])},
            ]
        )
    comparison = pd.DataFrame(comparison_records).dropna(subset=["Score"])

    st.markdown(f"#### {t('五维评分画像', 'Five-dimension score profile', language)}")
    if comparison.empty:
        st.warning(t("该市场的评分维度不可用。", "The score dimensions for this market are unavailable.", language))
    else:
        fig = px.bar(
            comparison,
            x="Score",
            y="Dimension",
            color="Series",
            barmode="group",
            orientation="h",
            color_discrete_map={selected_market: "#2F6FED", average_label: "#AAB4C3"},
            text="Score",
            category_orders={"Dimension": list(labels.values())[::-1]},
        )
        fig.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x:.1f}<extra></extra>",
        )
        fig.update_layout(
            xaxis_title=t("评分", "Score", language),
            yaxis_title=None,
            showlegend=True,
        )
        fig.update_xaxes(range=[0, 105], dtick=20)
        apply_chart_style(fig, 390)
        st.plotly_chart(fig, width="stretch")

    france_uzbekistan = ranking[ranking["destination"].isin(["France", "Uzbekistan"])].copy()
    if len(france_uzbekistan) == 2:
        st.markdown(f"#### {t('都是高分市场，但机会来源不同', 'Both high-scoring, different opportunity sources', language)}")
        focus_records: list[dict[str, object]] = []
        for _, row in france_uzbekistan.iterrows():
            for column, label in labels.items():
                focus_records.append(
                    {
                        "Dimension": label,
                        "Market": row["destination"],
                        "Score": row[column],
                    }
                )
        focus = pd.DataFrame(focus_records)
        fig = px.bar(
            focus,
            x="Score",
            y="Dimension",
            color="Market",
            barmode="group",
            orientation="h",
            color_discrete_map={"France": "#2F6FED", "Uzbekistan": "#D97757"},
            text="Score",
            category_orders={"Dimension": list(labels.values())[::-1]},
        )
        fig.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x:.1f}<extra></extra>",
        )
        fig.update_layout(xaxis_title=t("评分", "Score", language), yaxis_title=None, showlegend=True)
        fig.update_xaxes(range=[0, 105], dtick=20)
        apply_chart_style(fig, 390)
        st.plotly_chart(fig, width="stretch")

        france = france_uzbekistan.loc[france_uzbekistan["destination"] == "France"].iloc[0]
        uzbekistan = france_uzbekistan.loc[france_uzbekistan["destination"] == "Uzbekistan"].iloc[0]
        st.markdown(
            f"""
            <div class="insight-grid">
                <div class="insight-card blue">
                    <div class="insight-title">France · {format_score(france['opportunity_score'])}</div>
                    <div class="insight-body">{t(f"成熟核心市场。优势更偏向规模 Size（{format_score(france['size_score'])}）与稳定性 Stability（{format_score(france['stability_score'])}），适合深耕已有规模。", f"Mature Core Market. The profile is led by Size ({format_score(france['size_score'])}) and Stability ({format_score(france['stability_score'])}), supporting deeper investment in the existing base.", language)}</div>
                </div>
                <div class="insight-card orange">
                    <div class="insight-title">Uzbekistan · {format_score(uzbekistan['opportunity_score'])}</div>
                    <div class="insight-body">{t(f"高增长机会市场。增长 Growth（{format_score(uzbekistan['growth_score'])}）与动量 Momentum（{format_score(uzbekistan['momentum_score'])}）突出，但稳定性 Stability 仅 {format_score(uzbekistan['stability_score'])}。", f"High-growth Opportunity Market. Growth ({format_score(uzbekistan['growth_score'])}) and Momentum ({format_score(uzbekistan['momentum_score'])}) stand out, while Stability is only {format_score(uzbekistan['stability_score'])}.", language)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.caption(
        t(
            "数据来源：market_opportunity_ranking_2024.csv · 五个评分维度直接读取结果文件，Dashboard 不重新计算 Opportunity Score。",
            "Source: market_opportunity_ranking_2024.csv · The explorer reads the five supplied score dimensions and does not recompute Opportunity Score.",
            language,
        )
    )


def render_opportunity_dynamics(change: pd.DataFrame, risers: pd.DataFrame, language: str) -> None:
    page_header(
        t("机会动态", "OPPORTUNITY DYNAMICS", language),
        t("机会正在变化", "Opportunity is moving", language),
        t(
            "跟踪底层贸易数据变化带来的 2023 → 2024 Opportunity Score 与排名变化。",
            "Track how market scores and ranks changed from 2023 to 2024 as the underlying trade data evolved.",
            language,
        ),
    )

    compared = len(change)
    score_gainers = int((change["score_change"] > 0).sum())
    top_riser = risers.sort_values("rank_improvement", ascending=False).iloc[0] if not risers.empty else None
    top_improvement = top_riser["rank_improvement"] if top_riser is not None else None
    max_score_change = change["score_change"].max() if not change.empty else None

    render_kpis(
        [
            (t("比较市场数", "Markets Compared", language), f"{compared:,}", t("2023 与 2024 均有数据", "2023 and 2024 overlap", language)),
            (t("分数上升市场", "Markets with Score Gain", language), f"{score_gainers:,}", t("Score change > 0", "Score change > 0", language)),
            (t("最大分数增幅", "Largest Score Increase", language), format_signed(max_score_change), t("Opportunity Score 点数", "Opportunity Score points", language)),
            (t("排名提升第一", "Top Rank Riser", language), str(top_riser["destination"] if top_riser is not None else "N/A"), f"+{int(top_improvement):,} {t('名次', 'ranks', language)}" if top_improvement is not None else None),
        ]
    )

    st.info(
        t(
            "动态表沿用 Notebook 的年度内连接结果，共比较 194 个市场；它反映的是可匹配市场的变化，不是对缺失市场的预测。",
            "The dynamics table follows Notebook 03’s inner join and compares 194 markets; it describes matched-market movement, not a prediction for missing markets.",
            language,
        )
    )

    riser_col, movement_col = st.columns([1, 1.35])
    with riser_col:
        st.markdown(f"#### {t('机会跃升市场', 'Top Opportunity Risers', language)}")
        top_risers = risers.sort_values("rank_improvement", ascending=True).copy()
        top_risers["market_segment_display"] = top_risers["market_segment_2024_pred"].map(
            lambda value: localize_segment(value, language)
        )
        fig = px.bar(
            top_risers,
            x="rank_improvement",
            y="destination",
            orientation="h",
            color="market_segment_display" if "market_segment_display" in top_risers else None,
            color_discrete_map=localized_segment_colors(language),
            text="rank_improvement",
            custom_data=["score_2023", "score_2024", "rank_2023", "rank_2024", "score_change"],
        )
        fig.update_traces(
            texttemplate="+%{text}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>" + t("排名提升", "Rank improvement", language) + ": +%{x}"
                "<br>" + t("分数", "Score", language) + ": %{customdata[0]:.1f} → %{customdata[1]:.1f}"
                "<br>" + t("排名", "Rank", language) + ": %{customdata[2]} → %{customdata[3]}"
                "<br>" + t("分数变化", "Score change", language) + ": %{customdata[4]:+.1f}<extra></extra>"
            ),
        )
        fig.update_layout(
            xaxis_title=t("排名提升幅度", "Rank improvement", language),
            yaxis_title=t("目的地市场", "Destination market", language),
            showlegend=False,
        )
        fig.update_xaxes(range=[0, max(10, float(top_risers["rank_improvement"].max()) * 1.15)])
        apply_chart_style(fig, max(500, 25 * len(top_risers) + 100))
        st.plotly_chart(fig, width="stretch")

    with movement_col:
        st.markdown(f"#### {t('2023 排名 vs 2024 排名', '2023 Rank vs 2024 Rank', language)}")
        rank_plot = change.copy()
        rank_plot["label"] = ""
        top_labels = rank_plot.nlargest(8, "rank_improvement").index
        rank_plot.loc[top_labels, "label"] = rank_plot.loc[top_labels, "destination"]
        max_rank = int(max(rank_plot["rank_2023"].max(), rank_plot["rank_2024"].max()))
        fig = px.scatter(
            rank_plot,
            x="rank_2023",
            y="rank_2024",
            color="score_change",
            color_continuous_scale=["#C85B67", "#D8DEE8", "#2F6FED"],
            text="label",
            custom_data=["destination", "score_2023", "score_2024", "rank_improvement"],
        )
        fig.update_traces(
            marker={"size": 8, "opacity": 0.72, "line": {"width": 0.5, "color": "#FFFFFF"}},
            textposition="top center",
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>" + t("排名", "Rank", language) + ": %{x} → %{y}"
                "<br>" + t("分数", "Score", language) + ": %{customdata[1]:.1f} → %{customdata[2]:.1f}"
                "<br>" + t("排名提升", "Rank improvement", language) + ": %{customdata[3]:+d}<extra></extra>"
            ),
        )
        fig.add_shape(
            type="line",
            x0=1,
            y0=1,
            x1=max_rank,
            y1=max_rank,
            line={"color": "#AAB4C3", "width": 1, "dash": "dash"},
        )
        fig.update_layout(
            xaxis_title=t("2023 排名", "2023 rank", language),
            yaxis_title=t("2024 排名", "2024 rank", language),
            coloraxis_colorbar={"title": t("分数变化", "Score Δ", language)},
        )
        fig.update_xaxes(range=[max_rank + 3, 0], dtick=25)
        fig.update_yaxes(range=[max_rank + 3, 0], dtick=25)
        apply_chart_style(fig, 570)
        st.plotly_chart(fig, width="stretch")

    st.markdown(f"#### {t('跃升市场明细', 'Riser detail', language)}")
    riser_table = risers.sort_values("rank_improvement", ascending=False).copy()
    riser_table = riser_table[
        [
            "destination",
            "rank_2023",
            "rank_2024",
            "rank_improvement",
            "score_2023",
            "score_2024",
            "score_change",
        ]
    ].rename(
        columns={
            "destination": t("市场", "Market", language),
            "rank_2023": t("2023 排名", "2023 Rank", language),
            "rank_2024": t("2024 排名", "2024 Rank", language),
            "rank_improvement": t("排名提升", "Rank Improvement", language),
            "score_2023": t("2023 分数", "2023 Score", language),
            "score_2024": t("2024 分数", "2024 Score", language),
            "score_change": t("分数变化", "Score Change", language),
        }
    )
    riser_table[t("2023 排名", "2023 Rank", language)] = riser_table[t("2023 排名", "2023 Rank", language)].map(format_rank)
    riser_table[t("2024 排名", "2024 Rank", language)] = riser_table[t("2024 排名", "2024 Rank", language)].map(format_rank)
    riser_table[t("排名提升", "Rank Improvement", language)] = riser_table[t("排名提升", "Rank Improvement", language)].map(lambda x: f"+{int(x):,}")
    riser_table[t("2023 分数", "2023 Score", language)] = riser_table[t("2023 分数", "2023 Score", language)].map(format_score)
    riser_table[t("2024 分数", "2024 Score", language)] = riser_table[t("2024 分数", "2024 Score", language)].map(format_score)
    riser_table[t("分数变化", "Score Change", language)] = riser_table[t("分数变化", "Score Change", language)].map(lambda x: format_signed(x))
    st.dataframe(riser_table, hide_index=True, width="stretch")
    st.caption(
        t(
            "排名提升为正，表示数值排名变小：rank_improvement = rank_2023 − rank_2024。",
            "Positive rank improvement means the numeric rank became smaller: rank_improvement = rank_2023 − rank_2024.",
            language,
        )
    )


def render_validation_decision(validation: pd.DataFrame, language: str) -> None:
    page_header(
        t("验证与决策", "VALIDATION & DECISION", language),
        t("验证与决策", "Validation & Decision", language),
        t(
            "连接模型初筛、外部进口结构验证与 Notebook 04 记录的最终商业策略。",
            "Connects model screening, external import structure validation, and the final strategy recorded in Notebook 04.",
            language,
        ),
    )

    stages = [
        ("01", t("模型初筛", "Model screen", language), t("Opportunity Score + 市场类型", "Opportunity Score + market segment", language)),
        ("02", t("贸易验证", "Trade validation", language), t("进口规模、中国份额、增长、HHI", "Import scale, China share, growth, HHI", language)),
        ("03", t("商业决策", "Decision", language), t("策略、理由与数据风险", "Strategy, rationale, and data risk", language)),
    ]
    stage_columns = st.columns(3)
    for column, (number, title, detail) in zip(stage_columns, stages):
        column.markdown(
            f"""
            <div class="stage-card">
                <div class="stage-number">{number}</div>
                <div><div class="stage-title">{title}</div><div class="stage-detail">{detail}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    market_options = validation.sort_values(["opportunity_rank", "market"])["market"].tolist()
    default_index = market_options.index("France") if "France" in market_options else 0
    selected_market = st.selectbox(
        t("选择验证市场", "Select validated market", language),
        market_options,
        index=default_index,
    )
    selected_rows = validation[validation["market"] == selected_market]
    if selected_rows.empty:
        st.error(t("找不到所选验证市场。", "The selected validated market could not be found.", language))
        return
    selected = selected_rows.iloc[0]

    st.markdown(f"#### {t('验证市场画像', 'Validated market profile', language)}")
    render_kpis(
        [
            (t("Opportunity Score", "Opportunity Score", language), format_score(selected["opportunity_score"]), f"{t('排名', 'Rank', language)} {int(selected['opportunity_rank'])}"),
            (t("进口总额", "Total Import", language), format_money(selected["total_import_2024"]), t("2024 年报告进口额", "2024 reported imports", language)),
            (t("中国供应份额", "China Share", language), format_pct(selected["china_share_2024"]), t("占当地进口比重", "Share of local imports", language)),
            (t("市场增长", "Market Growth", language), format_pct(selected["market_growth"]), "2023 → 2024"),
        ]
    )
    render_kpis(
        [
            (t("中国供应增长", "China Growth", language), format_pct(selected["china_growth"]), "2023 → 2024"),
            (t("份额变化", "Share Change", language), format_pp(selected["share_change"]), t("百分点变化", "Percentage-point change", language)),
            ("HHI", f"{as_number(selected['hhi_2024']):.3f}" if as_number(selected["hhi_2024"]) is not None else "N/A", t("供应商集中度", "Supplier concentration", language)),
            (t("市场类型", "Market Segment", language), localize_segment(selected["market_segment"], language), t("模型分类", "Model classification", language)),
        ]
    )

    selected_strategy = localize_strategy(selected["strategy"], language)
    selected_reason = localize_validation_text(selected, "decision_reason", language)
    st.markdown(f"#### {t('建议行动', 'Recommended action', language)}")
    st.markdown(
        f"""
        <div class="decision-panel">
            <div class="decision-label">{t('策略', 'STRATEGY', language)}</div>
            <div class="decision-title">{clean_text(selected_strategy)}</div>
            <div class="decision-label rationale-label">{t('决策理由', 'DECISION REASON', language)}</div>
            <div class="decision-body">{clean_text(selected_reason)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"#### {t('数据可靠性检查', 'Data reliability check', language)}")
    selected_risk = localize_validation_text(selected, "data_risk", language)
    reliability_columns = st.columns(3)
    reliability_columns[0].markdown(
        f'<div class="reliability-metric"><div class="kpi-label">{t("镜像差异", "Mirror Gap", language)}</div><div class="reliability-value">{format_pct_already_scaled(selected["mirror_gap_pct"])} </div><div class="kpi-hint">{t("报告进口额 vs. 中国出口额", "Reported import vs. China export", language)}</div></div>',
        unsafe_allow_html=True,
    )
    reliability_columns[1].markdown(
        f'<div class="reliability-metric"><div class="kpi-label">{t("镜像相似度", "Mirror Similarity", language)}</div><div class="reliability-value">{as_number(selected["mirror_similarity"]):.3f}</div><div class="kpi-hint">{t("两项报告值的 min / max", "min / max of the two reported values", language)}</div></div>',
        unsafe_allow_html=True,
    )
    reliability_columns[2].markdown(
        f'<div class="reliability-metric risk"><div class="kpi-label">{t("数据风险", "Data Risk", language)}</div><div class="risk-text">{clean_text(selected_risk)}</div></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        t(
            "Notebook 04 将双边镜像差异视为数据质量与解释风险，不纳入 Opportunity Score。",
            "Notebook 04 treats bilateral mirror differences as a data-quality and interpretation risk; they are not included in Opportunity Score.",
            language,
        )
    )

    st.markdown(f"#### {t('全部验证市场', 'All validated markets', language)}")
    overview = validation.sort_values("opportunity_rank")[[
        "market",
        "opportunity_rank",
        "market_segment",
        "opportunity_score",
        "total_import_2024",
        "china_share_2024",
        "market_growth",
        "strategy",
    ]].copy().rename(
        columns={
            "market": t("市场", "Market", language),
            "opportunity_rank": t("排名", "Rank", language),
            "market_segment": t("市场类型", "Segment", language),
            "opportunity_score": t("Opportunity Score", "Opportunity Score", language),
            "total_import_2024": t("进口总额", "Total Import", language),
            "china_share_2024": t("中国供应份额", "China Share", language),
            "market_growth": t("市场增长", "Market Growth", language),
            "strategy": t("策略", "Strategy", language),
        }
    )
    overview[t("排名", "Rank", language)] = overview[t("排名", "Rank", language)].map(format_rank)
    overview[t("Opportunity Score", "Opportunity Score", language)] = overview[t("Opportunity Score", "Opportunity Score", language)].map(format_score)
    overview[t("进口总额", "Total Import", language)] = overview[t("进口总额", "Total Import", language)].map(format_money)
    overview[t("中国供应份额", "China Share", language)] = overview[t("中国供应份额", "China Share", language)].map(format_pct)
    overview[t("市场增长", "Market Growth", language)] = overview[t("市场增长", "Market Growth", language)].map(format_pct)
    overview[t("市场类型", "Segment", language)] = overview[t("市场类型", "Segment", language)].map(
        lambda value: localize_segment(value, language)
    )
    overview[t("策略", "Strategy", language)] = overview[t("策略", "Strategy", language)].map(
        lambda value: localize_strategy(value, language)
    )
    st.dataframe(overview, hide_index=True, width="stretch")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --navy: #14213D;
            --ink: #1F2937;
            --muted: #667085;
            --line: #E5EAF1;
            --surface: #FFFFFF;
            --blue: #2F6FED;
        }
        .stApp { background: #F6F8FB; color: var(--ink); }
        [data-testid="stHeader"] { background: rgba(246,248,251,0.92); }
        [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] .block-container { padding-top: 2rem; }
        .brand-mark { color: var(--navy); font-size: 1.35rem; font-weight: 760; letter-spacing: -0.02em; }
        .brand-subtitle { color: var(--muted); font-size: 0.75rem; margin-top: 0.2rem; }
        .eyebrow { color: var(--blue); font-size: 0.72rem; font-weight: 760; letter-spacing: 0.12em; margin-top: 0.25rem; }
        h1 { color: var(--navy); letter-spacing: -0.035em; margin-bottom: 0.3rem !important; }
        h3, h4 { color: var(--navy); letter-spacing: -0.02em; }
        .page-description { color: var(--muted); font-size: 1rem; margin-bottom: 1.5rem; }
        .kpi-card { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.05rem; min-height: 106px; box-shadow: 0 2px 8px rgba(20,33,61,0.025); }
        .kpi-label { color: var(--muted); font-size: 0.73rem; font-weight: 650; letter-spacing: 0.01em; }
        .kpi-value { color: var(--navy); font-size: 1.28rem; font-weight: 750; line-height: 1.25; margin-top: 0.45rem; word-break: break-word; }
        .kpi-hint { color: #98A2B3; font-size: 0.68rem; line-height: 1.35; margin-top: 0.35rem; }
        .stage-card { align-items: center; background: #FFFFFF; border: 1px solid var(--line); border-radius: 8px; display: flex; gap: 0.8rem; min-height: 72px; padding: 0.8rem 0.95rem; }
        .stage-number { color: var(--blue); font-size: 0.75rem; font-weight: 800; }
        .stage-title { color: var(--navy); font-size: 0.9rem; font-weight: 750; }
        .stage-detail { color: var(--muted); font-size: 0.7rem; margin-top: 0.15rem; }
        .insight-grid { display: grid; gap: 1rem; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: 0.4rem 0 1rem; }
        .insight-card { background: #FFFFFF; border-left: 4px solid var(--blue); border-radius: 6px; border-top: 1px solid var(--line); border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 1rem; }
        .insight-card.orange { border-left-color: #D97757; }
        .insight-title { color: var(--navy); font-size: 0.9rem; font-weight: 760; }
        .insight-body { color: var(--muted); font-size: 0.78rem; line-height: 1.6; margin-top: 0.45rem; }
        .decision-panel { background: #FFFFFF; border: 1px solid #D9E2F0; border-left: 5px solid var(--blue); border-radius: 8px; padding: 1.2rem 1.35rem; }
        .decision-label { color: var(--blue); font-size: 0.7rem; font-weight: 800; letter-spacing: 0.11em; }
        .decision-title { color: var(--navy); font-size: 1.25rem; font-weight: 780; margin: 0.3rem 0 1rem; }
        .rationale-label { border-top: 1px solid var(--line); padding-top: 0.9rem; }
        .decision-body { color: var(--ink); font-size: 0.9rem; line-height: 1.75; margin-top: 0.35rem; }
        .reliability-metric { background: #FFFFFF; border: 1px solid var(--line); border-radius: 8px; min-height: 112px; padding: 0.95rem 1rem; }
        .reliability-value { color: var(--navy); font-size: 1.22rem; font-weight: 750; margin-top: 0.4rem; }
        .reliability-metric.risk { border-left: 4px solid #D6A24A; }
        .risk-text { color: var(--ink); font-size: 0.78rem; line-height: 1.55; margin-top: 0.4rem; }
        [data-testid="stMetric"] { background: #FFFFFF; border: 1px solid var(--line); padding: 0.75rem; }
        div[data-testid="stDataFrame"] { border: 1px solid var(--line); }
        footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_styles()
    project_root = find_project_root()
    output_dir = find_output_dir(project_root)
    frames, missing = load_dashboard_data(output_dir)

    with st.sidebar:
        language_display = st.selectbox("语言 / Language", ["中文", "English"], index=0, key="language")
        language = "zh" if language_display == "中文" else "en"
        st.markdown(
            f'<div class="brand-mark">{t("出口市场智能分析", "Export Market Intelligence", language)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="brand-subtitle">{t("中国 · HS850760 · 2024", "China · HS850760 · 2024", language)}</div>',
            unsafe_allow_html=True,
        )
        st.divider()
        page_keys = ["global", "explorer", "dynamics", "validation"]
        page_key = st.radio(
            t("页面导航", "Navigate", language),
            page_keys,
            format_func=lambda key: PAGE_LABELS[language][key],
            key="navigation",
        )
        st.divider()
        st.markdown(f"**{t('数据状态', 'Data status', language)}**")
        output_location = output_dir.relative_to(project_root) if output_dir.is_relative_to(project_root) else output_dir
        st.caption(f"{t('使用目录', 'Using', language)}: {output_location}")
        st.caption(t("来自 Notebook 01–04 的正式结果", "Formal outputs from Notebooks 01–04", language))

    if missing:
        st.error(
            t(
                "Dashboard 缺少以下正式分析结果文件：",
                "The Dashboard is missing these formal analysis output files:",
                language,
            )
        )
        for filename in missing:
            st.markdown(f"- `{filename}`")
        st.info(
            t(
                "请先运行 Notebook 02–04 生成 outputs 文件，或将已有结果放入 notebooks/outputs/。",
                "Run Notebooks 02–04 first, or place the existing outputs in notebooks/outputs/.",
                language,
            )
        )
        st.stop()

    column_problems = validate_required_columns(frames)
    if column_problems:
        st.error(
            t(
                "Dashboard 输入字段与 Notebook 输出不一致：",
                "Dashboard input fields do not match the Notebook outputs:",
                language,
            )
        )
        for problem in column_problems:
            st.markdown(f"- {problem}")
        st.stop()

    if page_key == "global":
        render_global_opportunity(frames["ranking"], language)
    elif page_key == "explorer":
        render_market_explorer(frames["ranking"], language)
    elif page_key == "dynamics":
        render_opportunity_dynamics(frames["change"], frames["risers"], language)
    else:
        render_validation_decision(frames["validation"], language)


if __name__ == "__main__":
    main()
