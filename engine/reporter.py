"""报告生成模块"""
import os
from datetime import datetime
from typing import Optional
import plotly.graph_objects as go


REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
  body { font-family: 'Microsoft YaHei', sans-serif; max-width: 1100px; margin: 0 auto; padding: 40px 20px; color: #333; }
  h1 { border-bottom: 3px solid #1a73e8; padding-bottom: 10px; }
  h2 { color: #1a73e8; margin-top: 40px; }
  .meta { color: #888; font-size: 14px; margin-bottom: 30px; }
  .chart { margin: 20px 0; border: 1px solid #eee; border-radius: 8px; padding: 10px; }
  table { border-collapse: collapse; width: 100%; margin: 15px 0; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
  th { background: #f5f5f5; }
  .summary-box { background: #f0f7ff; border-left: 4px solid #1a73e8; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
  .conclusion { background: #f5fff0; border-left: 4px solid #34a853; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
</style>
</head>
<body>
<h1>{{ title }}</h1>
<p class="meta">生成时间: {{ created_at }} | 数据: {{ data_source }} ({{ rows }} 行 x {{ cols }} 列)</p>

{% for section in sections %}
<h2>{{ section.title }}</h2>
{% if section.text %}
<div class="summary-box">{{ section.text }}</div>
{% endif %}
{% if section.table %}
{{ section.table }}
{% endif %}
{% if section.chart_html %}
<div class="chart">{{ section.chart_html }}</div>
{% endif %}
{% endfor %}

<div class="conclusion">
<h2>分析结论</h2>
<p>{{ conclusion }}</p>
</div>
</body>
</html>"""


def chart_to_html(fig: go.Figure, chart_id: str) -> str:
    """将 plotly 图表转为可嵌入 HTML 的 div"""
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=chart_id)


def save_chart(fig: go.Figure, filepath: str) -> str:
    """保存图表为独立 HTML 文件"""
    fig.write_html(filepath)
    return filepath


def dataframe_to_html_table(df_data: list, columns: list = None, max_rows: int = 20) -> str:
    """将字典列表转换为 HTML 表格"""
    if not df_data:
        return "<p>无数据</p>"
    cols = columns or list(df_data[0].keys())
    rows_html = ""
    for row in df_data[:max_rows]:
        cells = "".join(f"<td>{row.get(c, '')}</td>" for c in cols)
        rows_html += f"<tr>{cells}</tr>"
    header = "".join(f"<th>{c}</th>" for c in cols)
    return f"<table><thead><tr>{header}</tr></thead><tbody>{rows_html}</tbody></table>"


def generate_html_report(
    title: str,
    sections: list,
    conclusion: str,
    data_source: str,
    rows: int,
    cols: int,
    charts: Optional[list] = None,
) -> str:
    """生成完整 HTML 报告"""
    from jinja2 import Template
    template = Template(REPORT_TEMPLATE)
    return template.render(
        title=title,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        data_source=data_source,
        rows=rows,
        cols=cols,
        sections=sections,
        conclusion=conclusion,
    )


def build_section(title: str, text: str = "", table: str = "", chart_html: str = "") -> dict:
    return {"title": title, "text": text, "table": table, "chart_html": chart_html}
