# -*- coding: utf-8 -*-
"""PAWKOREA Pet Hotel Yeongjong × PET-Aeye — MASTER deck.
버전/날짜는 아래 VERSION · DOC_DATE 상수에서 관리합니다 (커버 · 파일명에 자동 반영).
Integrates: 기획서(호텔·오픈·PET-Aeye·SaaS·관리) + 기능맵 요약 + 라이다 바이탈 + IR(시장·포지셔닝·투자)."""
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from lxml import etree

PAPER = RGBColor(0xF5, 0xF3, 0xEE)
INK = RGBColor(0x14, 0x14, 0x14)
GRAY = RGBColor(0x6B, 0x6B, 0x6B)
RULE = RGBColor(0xD9, 0xD5, 0xCC)
SAND = RGBColor(0xEA, 0xE6, 0xDD)
ACCENT = RGBColor(0xFF, 0x5B, 0x1F)
ACCENT_DIM = RGBColor(0xFF, 0xC9, 0xB3)
ACCENT_WASH = RGBColor(0xFF, 0xEC, 0xE4)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NIGHT = RGBColor(0x14, 0x14, 0x14)
NIGHT_GRAY = RGBColor(0x9A, 0x9A, 0x9A)

W, H = Inches(13.333), Inches(7.5)
MX = 0.7
CW = 11.93
FONT = "Malgun Gothic"

# ── 문서 버전 관리 ─────────────────────────────────────────────
VERSION = "1.3.1"        # 버전 올릴 때 여기만 수정 (커버 · 파일명 자동 반영)
DOC_DATE = "2026.10"     # 표기용 발행 월
# ──────────────────────────────────────────────────────────────
OUT = rf"D:\dev_pawkorea\pet-teamjang\doc\PLAN_PAWKOREA_pet_hotel_PET-Aeye_master_v{VERSION}.pptx"
MOCK = r"D:\dev_pawkorea\pet-teamjang\doc\_mockups"
BLE_ASSETS = r"D:\dev_pawkorea\pet-teamjang\assets\ble_tracking"
ADMIN_IMG = MOCK + r"\out_admin_wall.png"
STAFF_IMG = MOCK + r"\out_staff_app.png"
GUARD_IMG = MOCK + r"\out_guardian_app.png"
GRAD_IMG = MOCK + r"\out_graduation.png"

ROOMS = [
    ("소형", "2F", 52, "~7kg 소형견", 50_000, "객실당 1대 (다실 1캠 검토)"),
    ("중형", "2F", 34, "7~15kg 중형견", 65_000, "객실당 1대"),
    ("대형", "3F", 22, "15kg 이상 대형견", 90_000, "객실당 1대 · 우선 적용"),
    ("패밀리", "3F", 4, "다견 가족 · VIP", 150_000, "객실당 1~2대"),
]
ADDON = 0.15
OCC_SCENARIOS = (0.30, 0.45, 0.60)

# 부문별 연매출 가정 (억 원, 파우코리아 귀속) — 보수 / 기준 / 공격 · 실사 전 가정
RS_GROOM = 0.30                 # 펫 미용: 위탁 운영 RS, 파우코리아 30% (위탁사 70%)
GROOM_GROSS = (1.4, 2.1, 3.3)   # 펫 미용 총매출(위탁사 운영) → ×30%만 파우코리아 귀속
EXTRA_LINES = [
    ("펫유치원", (1.2, 2.0, 3.0)),
    ("펫 미용 (위탁 RS 30%)", tuple(round(g * RS_GROOM, 2) for g in GROOM_GROSS)),
    ("동물병원 (위탁 입점 · 임대+제휴)", (0.6, 1.2, 2.0)),
    ("펫용품 리테일", (1.2, 1.8, 2.8)),
    ("가든카페 · 독파크", (1.3, 2.0, 3.0)),
    ("이벤트 · 대관", (0.4, 0.8, 1.5)),
    ("공항 원스톱 주차", (0.5, 1.0, 1.8)),
    ("하드웨어 구독 · B2B 납품", (0.3, 0.8, 2.0)),
]


def portfolio_revenue(hotel_revenues):
    lines = [("본관 호텔 (숙박+부가)", tuple(round(r, 1) for r in hotel_revenues))] + EXTRA_LINES
    totals = [sum(l[1][i] for l in lines) for i in range(3)]
    return lines, totals


def I(v):
    return Inches(v)


def _font(run, size, color, bold):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = FONT
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", FONT)


def text(slide, x, y, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(lines):
        t, size, color, bold = line[:4]
        after = line[4] if len(line) > 4 else 6
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(after)
        r = p.add_run()
        r.text = t
        _font(r, size, color, bold)
    return tb


def box(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE):
    sh = slide.shapes.add_shape(shape, I(x), I(y), I(w), I(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def hline(slide, x, y, w, color=RULE, weight=0.015):
    return box(slide, x, y, w, weight, color)


def vline(slide, x, y, h, color=RULE, weight=0.015):
    return box(slide, x, y, weight, h, color)


def dot(slide, cx, cy, d, color):
    return box(slide, cx - d / 2, cy - d / 2, d, d, color, MSO_SHAPE.OVAL)


def new_slide(prs, dark=False):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = NIGHT if dark else PAPER
    return s


def frame(slide, page, section, title, dark=False):
    fg = WHITE if dark else INK
    sub = NIGHT_GRAY if dark else GRAY
    text(slide, MX, 0.45, 9.5, 0.3, [(section, 11, ACCENT, True)])
    text(slide, MX, 0.8, 11.9, 1.0, [(title, 25, fg, True)])
    text(slide, MX, 7.0, 9, 0.25, [("PAWKOREA Pet Hotel Yeongjong × PET-Aeye  ·  마스터 기획서", 9, sub, False)])
    text(slide, 11.63, 7.0, 1.0, 0.25, [(f"{page:02d}", 9, sub, True)], PP_ALIGN.RIGHT)


def style_chart(chart, number_format, colors):
    chart.has_legend = False
    chart.has_title = False
    chart.font.size = Pt(12)
    chart.font.name = FONT
    plot = chart.plots[0]
    plot.gap_width = 70
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.number_format = number_format
    labels.number_format_is_linked = False
    labels.position = XL_LABEL_POSITION.OUTSIDE_END
    labels.font.size = Pt(14)
    labels.font.bold = True
    labels.font.color.rgb = INK
    series = plot.series[0]
    for i, color in enumerate(colors):
        pt = series.points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = color
    va = chart.value_axis
    va.visible = False
    va.has_major_gridlines = False
    va.minimum_scale = 0
    ca = chart.category_axis
    ca.tick_labels.font.size = Pt(12)
    ca.tick_labels.font.color.rgb = GRAY
    ca.format.line.color.rgb = RULE
    ca.has_major_gridlines = False


def table(slide, x, y, cols, rows, row_h, body=12, strong_first=True, head_gap=0.45):
    cx = x
    for name, w in cols:
        text(slide, cx, y, w - 0.15, 0.3, [(name, 11, GRAY, True)])
        cx += w
    total_w = sum(w for _, w in cols)
    hline(slide, x, y + head_gap - 0.08, total_w, INK, 0.02)
    ry = y + head_gap + 0.05
    for row in rows:
        cx = x
        for ci, ((_, w), cell) in enumerate(zip(cols, row)):
            bold = strong_first and ci == 0
            text(slide, cx, ry, w - 0.15, row_h - 0.05, [(t, body, INK, bold, 1) for t in cell.split("\n")])
            cx += w
        hline(slide, x, ry + row_h - 0.1, total_w)
        ry += row_h
    return ry


def room_economics():
    total = sum(r[2] for r in ROOMS)
    adr = sum(r[2] * r[4] for r in ROOMS) / total
    full_year = total * 365 * adr * (1 + ADDON)
    revenues = [full_year * occ / 1e8 for occ in OCC_SCENARIOS]
    return total, adr, revenues


def section_divider(prs, kicker, title, items):
    s = new_slide(prs, dark=True)
    box(s, 0, 0, 13.333, 0.12, ACCENT)
    text(s, MX, 1.3, 9, 0.3, [(kicker, 12, ACCENT, True)])
    text(s, MX, 1.9, 11.8, 1.4, [(title, 40, WHITE, True)])
    for i, it in enumerate(items):
        y = 4.2 + i * 0.6
        dot(s, MX + 0.12, y + 0.12, 0.16, ACCENT)
        text(s, MX + 0.45, y, 11.0, 0.5, [(it, 15, NIGHT_GRAY, False)])
    return s


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    total_rooms, adr, revenues = room_economics()
    step_10pt = (revenues[1] - revenues[0]) / ((OCC_SCENARIOS[1] - OCC_SCENARIOS[0]) * 10)
    pf_lines, pf_totals = portfolio_revenue(revenues)
    page = 0

    # ===== 01 COVER =====
    page += 1
    s = new_slide(prs)
    box(s, 0, 0, 13.333, 0.12, ACCENT)
    text(s, MX, 0.7, 10, 0.3, [(f"MASTER PLAN  ·  {DOC_DATE}  ·  v{VERSION}  ·  내부 논의용", 11, GRAY, True)])
    text(s, MX, 1.5, 11.8, 2.6, [("파우코리아 펫호텔 영종", 44, INK, True, 0), ("× PET-Aeye 마스터 기획서", 44, ACCENT, True, 0)])
    text(
        s,
        MX,
        3.95,
        11.3,
        0.9,
        [
            ("시장 · 호텔 · 제품(PET-Aeye) · 라이다 바이탈 · 비즈니스 · 관리", 17, INK, True, 4),
            ("맡기는 순간부터, 보이는 안심을. 영종에서 운영하고, 다른 펫호텔로 넓힙니다.", 14, GRAY, False),
        ],
    )
    hline(s, MX, 5.55, CW, INK, 0.02)
    facts = [(f"{total_rooms}실", "4개 타입 위탁 객실"), ("2개동 캠퍼스", "본관 호텔 · 별관 생활권"), ("PET-Aeye", "실시간 AI 관제 솔루션"), ("SaaS", "타 펫호텔 확장")]
    for i, (v, lab) in enumerate(facts):
        text(s, MX + i * 3.0, 5.8, 2.8, 0.5, [(v, 22, INK, True, 2), (lab, 12, GRAY, False)])

    # ===== 02 CONTENTS =====
    page += 1
    s = new_slide(prs)
    frame(s, page, "CONTENTS", "이 문서가 다루는 것")
    parts = [
        ("PART 1", "왜 · 시장", "진입 기회 · 수요 · 포지셔닝"),
        ("PART 2", "호텔에 담을 것", "공간 · 객실 · 서비스 · 운영 기준"),
        ("PART 3", "PET-Aeye (제품)", "관제 · 앱 · 여정 · 기능맵"),
        ("PART 4", "라이다 바이탈 확장", "FMCW 라이다 · 비접촉 바이탈 (PoC)"),
        ("PART 5", "비즈니스 & 확장", "수익모델 · 단위경제 · SaaS 요금 · 홈서비스 · 경쟁 · 투자"),
        ("PART 6", "관리", "지표 · 리스크 · 결정 · 로드맵"),
    ]
    for i, (n, h, d) in enumerate(parts):
        cx = MX + (i % 2) * 6.1
        cy = 1.95 + (i // 2) * 1.55
        text(s, cx, cy, 1.6, 0.6, [(n, 15, ACCENT, True)])
        text(s, cx + 1.7, cy, 4.3, 1.2, [(h, 18, INK, True, 2), (d, 12, GRAY, False)])
        hline(s, cx, cy + 1.2, 5.8)
    text(s, MX, 6.7, CW, 0.3, [("전체 사업 범위(펫장례 포함)는 프로젝트_범위_확장_초안.md에서 다룹니다.", 10, GRAY, False)])

    # ========================= PART 1 · WHY & MARKET =========================
    page += 1
    section_divider(
        prs,
        "PART 1 · WHY & MARKET",
        "왜 지금, 영종인가",
        ["인스파이어는 반려동물 입실이 어렵고, 공항 15분 거리와 신도시 생활권이 한 섬에 겹칩니다",
         "공식 공항 채널이 담지 못하는 중대형 수요가 남아 있습니다",
         "객실이 아니라 '보이는 안심'으로 차별화합니다"],
    )

    # 제안 요지 (thesis)
    page += 1
    s = new_slide(prs)
    frame(s, page, "INVESTMENT THESIS", "이 사업을 제안하는 세 가지 이유")
    thesis = [
        ("01", "영종에는 구조적인 위탁 수요가 있습니다", "인스파이어 리조트는 반려동물 입실이 어렵고, 공항 15분 거리와 신도시 생활권이 한 섬에 겹쳐 있습니다."),
        ("02", "공식 공항 채널 밖에 중대형 수요가 남아 있습니다", "인천공항 공식 호텔링은 1개 업체가 운영하며 약 13kg 이하 소형견 중심입니다."),
        ("03", "객실이 아니라 '보이는 안심'으로 차별화합니다", "자체 AI 관제 PET-Aeye가 실시간 캠 · AI 행동 이벤트 · 일일 리포트를 전 객실에 제공합니다."),
    ]
    for i, (n, head, proof) in enumerate(thesis):
        y = 2.05 + i * 1.55
        hline(s, MX, y - 0.2, CW)
        text(s, MX, y, 1.0, 0.8, [(n, 34, ACCENT, True)])
        text(s, MX + 1.3, y + 0.05, 10.5, 1.2, [(head, 19, INK, True, 6), (proof, 13, GRAY, False)])
    hline(s, MX, 2.05 + 3 * 1.55 - 0.2, CW)

    # Wedge
    page += 1
    s = new_slide(prs)
    frame(s, page, "THE WEDGE", "세 가지 숫자에서 진입 기회를 찾았습니다")
    wedge = [
        ("0실", "인스파이어 리조트의\n반려동물 입실 가능 객실", "보조견 외에는 입실이 어려워, 투숙객에게 인근 위탁이 필요합니다."),
        ("13kg", "인천공항 공식 호텔링의\n수용 체중 기준(안내)", "중·대형견 보호자는 다른 선택지를 찾아야 합니다."),
        ("26실", "저희 3층의\n대형 22실 · 패밀리 4실", "공식 채널이 받기 어려운 보호자를 맞이합니다."),
    ]
    for i, (num, lab, note) in enumerate(wedge):
        x = MX + i * 4.1
        if i:
            vline(s, x - 0.3, 2.1, 4.2)
        text(s, x, 2.0, 3.8, 1.4, [(num, 72, ACCENT if i == 2 else INK, True)])
        text(s, x, 3.6, 3.7, 1.0, [(line, 16, INK, True, 2) for line in lab.split("\n")])
        text(s, x, 4.75, 3.6, 1.2, [(note, 13, GRAY, False)])
    text(s, MX, 6.45, CW, 0.4, [("Source: 인스파이어 이용약관·FAQ, 인천국제공항공사 보도자료(2024.3·11) 및 영문 안내, 원 사업계획서 3F 평면", 10, GRAY, False)])

    # Demand + chart
    page += 1
    s = new_slide(prs)
    frame(s, page, "DEMAND", "시장은 아직 작지만 빠르게 크고, 입지가 수요를 만듭니다")
    streams = [
        ("공항 출국", "출국 전 맡기고 귀국 시 찾는 수요입니다. 공항공사가 호텔링 카운터를 직접 열 만큼 수요가 확인됐습니다."),
        ("리조트 투숙", "반려 입실이 제한되는 인스파이어·파라다이스시티 등 대형 리조트 투숙객의 단기 위탁 수요입니다."),
        ("영종 생활권", "하늘도시·미단시티 거주 가구의 출장·여행·데이케어 수요로 비수기를 보완합니다."),
    ]
    for i, (h, b) in enumerate(streams):
        y = 2.0 + i * 1.45
        dot(s, MX + 0.12, y + 0.17, 0.18, ACCENT)
        text(s, MX + 0.45, y, 5.3, 1.3, [(h, 17, INK, True, 4), (b, 13, GRAY, False)])
    data = CategoryChartData()
    data.categories = ["2024", "2030E"]
    data.add_series("국내 펫 보딩", (980, 1830))
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, I(7.1), I(2.0), I(5.4), I(3.7), data)
    style_chart(gf.chart, '#,##0"억 원"', [SAND, ACCENT])
    text(s, 7.1, 5.8, 5.5, 0.9, [("국내 펫 보딩 시장 · CAGR 11.1% (2025–2030 전망)", 13, INK, True, 2), ("Grand View Horizon, USD→KRW 1,350원 환산(약수). 동반숙박 시장은 제외했습니다.", 10, GRAY, False)])

    # 대형 리조트 수요 연계
    page += 1
    s = new_slide(prs)
    frame(s, page, "DEMAND", "영종의 대형 리조트 투숙 수요를 함께 담습니다")
    box(s, MX, 1.95, 5.85, 1.75, SAND)
    text(s, MX + 0.35, 2.15, 5.2, 1.45, [
        ("인스파이어 엔터테인먼트 리조트", 12, ACCENT, True, 3),
        ("1,275실", 30, INK, True, 2),
        ("5성 3개 타워 · 아레나 1.5만석 · 워터파크 · 카지노", 11, GRAY, False),
    ])
    box(s, 6.75, 1.95, 5.88, 1.75, SAND)
    text(s, 7.1, 2.15, 5.25, 1.45, [
        ("파라다이스시티 (하얏트 리젠시 포함)", 12, ACCENT, True, 3),
        ("1,270실", 30, INK, True, 2),
        ("5성 · 카지노 · 원더박스 · 씨메르 스파 (2026 확장)", 11, GRAY, False),
    ])
    box(s, MX, 3.9, CW, 0.72, ACCENT_WASH)
    text(s, MX, 4.02, CW, 0.5, [("영종 생활권 5성 리조트 약 2,545실 — 다수가 반려동물 동반 투숙을 제한합니다", 15, INK, True)], PP_ALIGN.CENTER)
    text(s, MX, 4.85, 5.85, 1.8, [
        ("왜 우리에게 오나", 14, ACCENT, True, 6),
        ("· 리조트 대부분 반려 동반 투숙 제한 → 위탁 수요", 12.5, INK, False, 4),
        ("· 외국인 · 장기 · MICE 투숙객의 여행 중 안심 위탁", 12.5, INK, False, 4),
        ("· 공항 10분 · 리조트 5~10분, 같은 생활권 픽업·샌딩", 12.5, INK, False),
    ])
    text(s, 6.75, 4.85, 5.88, 1.8, [
        ("연계 방식 (B2B)", 14, ACCENT, True, 6),
        ("· 리조트 컨시어지 · FAQ 제휴 (추천 보딩 채널)", 12.5, INK, False, 4),
        ("· 객실+펫 위탁 번들 · 귀국 동선 미용·리테일 연결", 12.5, INK, False, 4),
        ("· 직원 · 장기 거주 수요 · 반려 이벤트 대관 송객", 12.5, INK, False),
    ])
    text(s, MX, 6.75, CW, 0.3, [("객실수: 인스파이어 1,275실 · 파라다이스시티 1,270실(2026, 하얏트 리젠시 포함). Source: 각 리조트 안내 · 보도자료.", 10, GRAY, False)])

    # Positioning 2x2
    page += 1
    s = new_slide(prs)
    frame(s, page, "POSITIONING", "영종의 '중대형 × 보이는 안심' 자리는 비어 있습니다")
    ox, oy, aw, ah = 1.6, 1.95, 6.6, 4.5
    box(s, ox + aw / 2, oy, aw / 2, ah / 2, ACCENT_WASH)
    vline(s, ox + aw / 2, oy, ah, RULE)
    hline(s, ox, oy + ah / 2, aw, RULE)
    vline(s, ox, oy, ah, INK, 0.02)
    hline(s, ox, oy + ah, aw, INK, 0.02)
    text(s, ox, oy + ah + 0.12, aw, 0.3, [("수용 범위  →  소형 중심 · · · 중대형·패밀리", 11, GRAY, True)], PP_ALIGN.CENTER)
    text(s, 0.35, oy + ah / 2 - 0.6, 1.15, 1.2, [("안심 투명성", 11, GRAY, True, 2), ("↑ 실시간 캠", 10, GRAY, False, 2), ("· AI 리포트", 10, GRAY, False)])
    players = [
        ("독독", 0.22, 0.48, INK, "공항 공식 채널"),
        ("더우프앤", 0.48, 0.42, INK, "공항 샌딩·장기 할인"),
        ("앤드", 0.75, 0.30, INK, "중대형·생활권"),
        ("호텔독스(서울)", 0.45, 0.85, GRAY, "참고 사례 · 권역 외"),
        ("파우코리아", 0.80, 0.82, ACCENT, "지향하는 위치"),
    ]
    for name, px, py, color, note in players:
        cx = ox + px * aw
        cy = oy + (1 - py) * ah
        dot(s, cx, cy, 0.34 if color == ACCENT else 0.22, color)
        text(s, cx + 0.22, cy - 0.22, 2.2, 0.6, [(name, 13, color, True, 0), (note, 10, GRAY, False)])
    text(s, 8.75, 2.0, 3.9, 4.3, [
        ("읽는 법", 13, ACCENT, True, 8),
        ("공식 채널(독독)은 접근성이 좋지만 소형견 중심입니다.", 13, INK, False, 8),
        ("로컬(앤드)은 중대형을 받지만, 공개 정보상 AI 리포트형 안심은 없습니다.", 13, INK, False, 8),
        ("서울에는 AI 캠으로 프리미엄을 만드는 사례가 있습니다. 영종에는 아직 없습니다.", 13, INK, False, 14),
        ("공개 정보 기반의 정성 배치입니다.", 10, GRAY, False),
    ])

    # ========================= PART 2 · 호텔에 담을 것 =========================
    page += 1
    section_divider(prs, "PART 2 · 호텔 & 캠퍼스", "두 개 동, 하나의 반려 캠퍼스",
                    ["본관 — 프리미엄 펫호텔(위탁 숙박 · 스파 · 미용 · 안심)",
                     "별관 — 펫유치원 · 펫용품 리테일로 생활권 수요 확장",
                     "24시간 상주 케어와 PET-Aeye 관제를 함께 운영합니다"])

    # Campus overview (2 buildings)
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 2 · 호텔 & 캠퍼스", "2개동 캠퍼스 — 본관(숙박) × 별관(생활권)")
    box(s, MX, 1.95, 5.85, 3.9, WHITE)
    box(s, 6.75, 1.95, 5.88, 3.9, ACCENT_WASH)
    text(s, MX + 0.35, 2.2, 5.2, 0.7, [("본관 · 프리미엄 펫호텔", 11, ACCENT, True, 3), ("머무는 안심 — 야간 · 숙박 중심", 17, INK, True)])
    for i, line in enumerate([
        "·  위탁 숙박 — 체급별 객실 · 스위트 · 테마룸",
        "·  스파 · 미용 — 자쿠지 스파 · 그루밍",
        "·  공항 샌딩 · 픽업 — T1 10분 · 발렛",
        "·  옥상 놀이방 — 그룹 활동 · 하이라이트",
        "·  PET-Aeye 안심 — 라이브 · CareReport",
    ]):
        text(s, MX + 0.35, 3.15 + i * 0.52, 5.2, 0.45, [(line, 13, INK, False)])
    text(s, 7.1, 2.2, 5.2, 0.7, [("별관 · 생활권 센터", 11, ACCENT, True, 3), ("매일 오는 이유 — 주간 · 통원 중심", 17, INK, True)])
    for i, line in enumerate([
        "·  펫유치원 — 주간 데이케어 · 사회화",
        "·  펫 미용 · 스파 — 트리밍 · 목욕 · 셀프워시",
        "·  펫용품 리테일 — 큐레이션 · 구독 · 체험형",
        "·  아카데미 — 행동교정 · 클래스",
        "·  펫 카페 · 커뮤니티 — 멤버십 허브",
    ]):
        text(s, 7.1, 3.15 + i * 0.52, 5.3, 0.45, [(line, 13, INK, False)])
    box(s, MX, 6.0, CW, 1.0, SAND)
    text(s, MX + 0.35, 6.14, 11.3, 0.8, [
        ("두 엔진의 시너지", 13, ACCENT, True, 4),
        ("시간대 상보(야간 숙박 × 주간 통원) · 수요 상보(여행 × 생활권) · 퍼널(유치원 → 호텔 전환) · 공용 자원(관제 · 픽업 · 백오피스 · PET-Aeye)", 12, INK, False),
    ])

    # Floors + extra
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 2 · 호텔 & 캠퍼스", "본관 — 층별 공간과 추가로 갖출 운영 공간")
    floors = [
        ("ROOF", "루프탑 가든", "피크닉 존 · 야외 테라스 · 정원", False),
        ("3F", "대형 22실 · 패밀리 4실", "VIP 2타입 · 라운지 — 중대형 전용 층", True),
        ("2F", "소형 52실 · 중형 34실", "2타입 객실 · 라운지 · 펫 플레이존", True),
        ("1F", "프런트 · 상담/예약 · 스파 · 미용", "휴식실 · 카페&베이커리", True),
    ]
    for i, (fl, name, note, core) in enumerate(floors):
        y = 1.95 + i * 1.12
        box(s, MX, y, 1.1, 0.95, ACCENT if core else SAND)
        text(s, MX, y, 1.1, 0.95, [(fl, 16, WHITE if core else GRAY, True)], PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
        box(s, MX + 1.2, y, 5.3, 0.95, WHITE if core else SAND)
        text(s, MX + 1.45, y + 0.14, 4.9, 0.8, [(name, 15, INK if core else GRAY, True, 2), (note, 11, GRAY, False)])
    text(s, MX, 6.45, 6.5, 0.3, [("위치: 인천 영종구 운남동로 44 · 운서역 5분 · 인천공항 약 10분 · 인허가: 동물위탁관리업 등록", 10, GRAY, False)])
    text(s, 7.7, 1.95, 4.9, 0.35, [("추가로 갖출 운영 공간", 13, ACCENT, True)])
    extra = [
        ("관제실", "PET-Aeye 룸 그리드 · 야간 관제"), ("격리실", "입실 후 이상 증상 개체 분리"),
        ("급식 준비실", "개체별 식단 · 특식 · 투약"), ("세탁 · 소독실", "객실 회전 청소 · 침구 세탁"),
        ("비품 · 의약품 보관", "응급 키트 · 투약 기록"), ("이중문 · 출입 통제", "층별 탈출 방지 · 출입 기록"),
    ]
    for i, (h, d) in enumerate(extra):
        y = 2.45 + i * 0.68
        text(s, 7.7, y, 1.9, 0.5, [(h, 13, INK, True)])
        text(s, 9.65, y, 3.0, 0.5, [(d, 12, GRAY, False)])
        hline(s, 7.7, y + 0.5, 4.93)

    # Rooms table
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 2 · 호텔 & 캠퍼스", "본관 객실 상품 — 4개 타입, 112실")
    cols = [("타입", 1.5), ("위치", 1.0), ("실수", 1.0), ("대상 (가정)", 2.6), ("1박 요금 (가정)", 2.2), ("카메라", 3.63)]
    rows = [(n, fl, f"{c}실", tgt, f"{p / 10000:g}만 원", cam) for n, fl, c, tgt, p, cam in ROOMS]
    rows.append(("합계", "", f"{total_rooms}실", "", f"평균 약 {adr / 10000:.1f}만 원", "전 객실 PET-Aeye 연결"))
    table(s, MX, 1.95, cols, rows, 0.62, body=13)
    box(s, MX, 5.4, CW, 1.15, SAND)
    text(s, MX + 0.35, 5.55, 11.3, 0.95, [
        ("3F 26실(대형 · 패밀리)을 중대형 수요의 핵심 상품으로 둡니다.", 14, INK, True, 4),
        (f"인천공항 공식 호텔링은 약 13kg 이하 중심입니다. 가동률 30 · 45 · 60% 기준 연매출은 약 {revenues[0]:.1f} · {revenues[1]:.1f} · {revenues[2]:.1f}억 원입니다(부가 15% 포함, 가정).", 12, GRAY, False),
    ])

    # Services
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 2 · 호텔 & 캠퍼스", "본관 서비스 메뉴 — 기본 · 부가 · 안심")
    menus = [
        ("BASIC", "기본 위탁", "모든 Stay", ["개체별 급식 · 급수", "하루 2회 이상 산책 · 놀이", "배변 처리 · 객실 청소", "24시간 상주 케어", "일일 케어 로그"]),
        ("ADD-ON", "부가 서비스", "선택", ["펫 스파 · 목욕", "미용", "공항 샌딩 · 픽업", "특식 (SPECIAL PET FOOD)", "투약 관리 · 데이케어"]),
        ("PET-Aeye", "안심 서비스", "PET-Aeye 제공", ["배정 룸 라이브 열람", "일일 CareReport", "이상 시 보호자 알림 (선택)", "퇴실 하이라이트 클립", "Stay 졸업 리포트 (종합 행동분석)"]),
    ]
    for i, (tag, name, sub, items) in enumerate(menus):
        x = MX + i * 4.05
        hline(s, x, 2.0, 3.75, ACCENT if i == 2 else INK, 0.03)
        text(s, x, 2.2, 3.7, 0.3, [(tag, 11, ACCENT, True)])
        text(s, x, 2.55, 3.7, 0.8, [(name, 21, INK, True, 2), (sub, 12, GRAY, False)])
        text(s, x, 3.55, 3.7, 2.0, [(f"·  {t}", 13, INK, False, 6) for t in items])
    box(s, MX, 5.6, CW, 0.95, ACCENT_WASH)
    text(s, MX + 0.35, 5.72, 11.3, 0.8, [
        ("대표 패키지  ‘공항 안심 보딩’ = 숙박 + 공항 샌딩 · 픽업 + 안심 서비스", 14, INK, True, 4),
        ("인스파이어 숏스테이 · 영종 생활권 데이케어는 같은 구성에서 기간만 다르게 운영합니다.", 12, GRAY, False),
    ])

    # Operating standards
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 2 · 호텔 & 캠퍼스", "본관 운영 기준 — 입실 · 케어 · 인력 · 정책")
    quads = [
        ("입실 기준", ["예방접종 증명 확인", "건강 문진 · 기저질환 · 복용약", "공격성 · 분리불안 체크", "생리 · 발정 여부"]),
        ("케어 기준", ["개체별 식단 · 급여 시간", "산책 · 놀이 일정", "순찰과 PET-Aeye 관제 병행", "케어 로그 기록 · 리포트 반영"]),
        ("인력 기준", ["24시간 상주", "위탁 20마리당 1명 이상", "가동률 연동 근무표", "야간 관제 담당 지정"]),
        ("정책 · 동의", ["이용 약관 · 취소 / 환불", "응급 진료 동의", "영상 촬영 · 열람 · 보존 고지", "배상책임보험 가입"]),
    ]
    for i, (h, items) in enumerate(quads):
        cx = MX + (i % 2) * 6.1
        cy = 1.95 + (i // 2) * 2.35
        hline(s, cx, cy, 5.8, INK, 0.02)
        text(s, cx, cy + 0.18, 5.7, 0.4, [(h, 16, ACCENT if i == 2 else INK, True)])
        text(s, cx, cy + 0.7, 5.7, 1.6, [(f"·  {t}", 13, INK, False, 5) for t in items])
    text(s, MX, 6.6, 11.9, 0.3, [("가동률 60%(하루 약 67마리)면 상시 최소 4명이 필요합니다. 근무표는 객실 판매 현황과 함께 짭니다.", 11, GRAY, False)])

    # ========================= 확장 · 별관 (펫유치원 · 리테일) =========================
    page += 1
    section_divider(prs, "확장 · 별관", "한 캠퍼스, 두 엔진 — 생활권으로 확장",
                    ["별관은 '매일 오는 이유' — 펫유치원 · 펫 미용 · 펫용품 리테일",
                     "본관 호텔과 고객 · 브랜드 · PET-Aeye를 공유합니다",
                     "주간 · 반복 수요로 비수기를 메우고 LTV를 키웁니다"])

    # 별관 ① 펫유치원
    page += 1
    s = new_slide(prs)
    frame(s, page, "확장 · 별관", "별관 ① 펫유치원 — 주간 데이케어 & 사회화")
    text(s, MX, 1.95, 5.6, 0.4, [("프로그램 · 요금 (운영 설계안)", 13, ACCENT, True)])
    prog = [
        ("정기권", "주 2~5회 · 월 정액 (주력 상품)"),
        ("일일권 · 반일 / 종일", "비정기 수요 · 체험 유입"),
        ("픽업 · 샌딩 옵션", "본관 차량 공유 · 발렛"),
        ("행동교정 · 클래스", "사회화 · 기초 훈련 (부가)"),
        ("호텔 전환 번들", "유치원 회원 숙박 할인"),
    ]
    for i, (h, d) in enumerate(prog):
        y = 2.5 + i * 0.72
        text(s, MX, y, 5.6, 0.6, [(h, 14, INK, True, 2), (d, 11, GRAY, False)])
        hline(s, MX, y + 0.6, 5.6)
    box(s, 6.9, 1.95, 5.73, 2.45, ACCENT_WASH)
    text(s, 7.2, 2.15, 5.1, 2.1, [
        ("PET-Aeye 등원 리포트", 14, ACCENT, True, 6),
        ("· 등원 중 배정 존 라이브 열람", 13, INK, False, 4),
        ("· 일일 리포트 (놀이 · 낮잠 · 사회성)", 13, INK, False, 4),
        ("· 월 성장 · 사회성 리포트 (졸업 리포트 응용)", 13, INK, False),
    ])
    box(s, 6.9, 4.6, 5.73, 1.95, SAND)
    text(s, 7.2, 4.8, 5.1, 1.65, [
        ("왜 유치원인가", 14, INK, True, 6),
        ("· 주간 · 반복 매출로 비수기 보완 · 현금흐름 안정", 13, INK, False, 4),
        ("· 통원 신뢰 → 호텔 위탁 전환 (LTV↑)", 13, INK, False, 4),
        ("· 사회화 · 행동 데이터가 호텔 케어로 연결", 13, INK, False),
    ])
    text(s, MX, 6.75, 11.9, 0.3, [("* 요금 · 프로그램은 운영 설계안이며 지역 수요로 조정합니다.", 10, GRAY, False)])

    # 별관 ② 펫 미용
    page += 1
    s = new_slide(prs)
    frame(s, page, "확장 · 별관", "별관 ② 펫 미용 — 생활권 트리밍 & 스파")
    text(s, MX, 1.95, 5.6, 0.4, [("서비스 · 요금 (운영 설계안)", 13, ACCENT, True)])
    groom = [
        ("기본 미용", "목욕 · 위생 · 발톱 · 부분 컷"),
        ("전체 미용", "가위컷 · 클리핑 · 스타일링"),
        ("스파", "약욕 · 버블 · 탄산 (보유 설비)"),
        ("셀프워시", "셀프 목욕 부스 · 생활권 재방문"),
        ("정기 구독", "월 미용권 · 유치원 · 호텔 번들"),
    ]
    for i, (h, d) in enumerate(groom):
        y = 2.5 + i * 0.72
        text(s, MX, y, 5.6, 0.6, [(h, 14, INK, True, 2), (d, 11, GRAY, False)])
        hline(s, MX, y + 0.6, 5.6)
    box(s, 6.9, 1.95, 5.73, 2.45, ACCENT_WASH)
    text(s, 7.2, 2.15, 5.1, 2.1, [
        ("PET-Aeye · 연계", 14, ACCENT, True, 6),
        ("· 미용 전 / 후 사진 · 리포트 보호자 전송", 13, INK, False, 4),
        ("· 호텔 투숙 중 그루밍 연계 (퇴실 전 단장)", 13, INK, False, 4),
        ("· 유치원 회원 정기 미용 번들", 13, INK, False),
    ])
    box(s, 6.9, 4.6, 5.73, 1.95, SAND)
    text(s, 7.2, 4.8, 5.1, 1.65, [
        ("왜 미용인가", 14, INK, True, 6),
        ("· 고마진 · 고빈도 재방문 — 생활권 핵심 반복매출", 13, INK, False, 4),
        ("· 그루밍 살롱 · 스파 설비 기보유 → 추가 capex 최소", 13, INK, False, 4),
        ("· 호텔 · 유치원과 교차 판매", 13, INK, False),
    ])
    text(s, MX, 6.75, 11.9, 0.3, [("* 본관은 투숙객 대상 부가 그루밍, 별관은 생활권 워크인 미용으로 운영합니다.", 10, GRAY, False)])

    # 별관 ③ 펫용품 리테일
    page += 1
    s = new_slide(prs)
    frame(s, page, "확장 · 별관", "별관 ③ 펫용품 리테일 — 큐레이션 · 구독 · 체험형")
    pillars = [
        ("큐레이션", "사료 · 간식 · 위생 · 장난감 · 웨어\n수의 · 행동 기반 추천"),
        ("구독", "정기배송(사료 · 위생)\n예측 가능한 반복 매출"),
        ("체험형 매장", "실사용 쇼룸 → 전환\n호텔 · 유치원 동선 노출"),
        ("번들 · 온라인", "회원 번들 할인\n스마트스토어 · 자사몰 · 픽업"),
    ]
    for i, (h, b) in enumerate(pillars):
        x = MX + i * 3.0
        hline(s, x, 2.0, 2.75, INK, 0.02)
        text(s, x, 2.2, 2.7, 0.4, [(h, 16, INK, True)])
        text(s, x, 2.95, 2.7, 1.3, [(t, 12, GRAY, False, 3) for t in b.split("\n")])
    box(s, MX, 4.6, CW, 1.9, ACCENT_WASH)
    text(s, MX + 0.35, 4.8, 11.3, 1.6, [
        ("왜 리테일인가", 14, ACCENT, True, 6),
        ("호텔 · 유치원 고객 기반 위에 얹는 고마진 부가매출입니다. 실제로 쓰는 제품을 매장에서 보여주니 전환이 쉽고,", 13, INK, False, 4),
        ("구독 · 번들로 재방문과 반복 매출을 만들며, 재고는 큐레이션 · 구독 예약으로 최소화합니다.", 13, INK, False),
    ])
    text(s, MX, 6.7, 11.9, 0.3, [("* 품목 · 마진 · 구독 설계는 수요 데이터로 조정합니다.", 10, GRAY, False)])

    # 별관 ④ 동물병원 (앵커 입점)
    page += 1
    s = new_slide(prs)
    frame(s, page, "확장 · 별관", "별관 ④ 동물병원 — 앵커 입점 (위탁 · 제휴)")
    text(s, MX, 1.95, 5.6, 0.4, [("핵심 포인트", 13, ACCENT, True)])
    vet = [
        ("운남동 의료 공백", "운남동 병원 1곳뿐 · 영종구 등록 14,347마리"),
        ("원스톱 검진", "호텔·유치원 입실 전 검진·예방접종"),
        ("응급 연계", "투숙 중 이상 → 원내 즉시 진료"),
        ("적법 구조", "수의사 개설·운영 / 파우는 공간·집객 제공"),
        ("파우 수익", "매출연동 임대 + 제휴 수수료(RS)"),
    ]
    for i, (h, d) in enumerate(vet):
        y = 2.5 + i * 0.72
        text(s, MX, y, 5.6, 0.6, [(h, 14, INK, True, 2), (d, 11, GRAY, False)])
        hline(s, MX, y + 0.6, 5.6)
    box(s, 6.9, 1.95, 5.73, 2.45, ACCENT_WASH)
    text(s, 7.2, 2.15, 5.1, 2.1, [
        ("앵커 효과", 14, ACCENT, True, 6),
        ("· 의료는 목적성 방문 → 미용·유치원·호텔·리테일 전환", 13, INK, False, 4),
        ("· PET-Aeye·라이다 바이탈 → 응급·건강관리 연계", 13, INK, False, 4),
        ("· '의료가 있는 호텔' 프리미엄 신뢰", 13, INK, False),
    ])
    box(s, 6.9, 4.6, 5.73, 1.95, SAND)
    text(s, 7.2, 4.8, 5.1, 1.65, [
        ("리스크 · 유의", 14, INK, True, 6),
        ("· 사무장병원 규제 → 임대·제휴 구조 + 법률 검토", 13, INK, False, 4),
        ("· 좋은 수의사 유치가 성패 / capex는 수의사 투자", 13, INK, False, 4),
        ("· 주간 일반·예방·검진부터, 24시 응급은 단계", 13, INK, False),
    ])
    text(s, MX, 6.75, 11.9, 0.3, [("* 동물병원 개설·운영 주체는 수의사입니다(수의사법). 파우코리아는 임대인·제휴자로 참여합니다.", 10, GRAY, False)])

    # 별관 수익 · 시너지 · 단계
    page += 1
    s = new_slide(prs)
    frame(s, page, "확장 · 별관", "별관 사업 — 수익 구조 · 시너지 · 단계")
    cols = [("사업", 2.5), ("핵심 수익원", 6.1), ("성격", 3.33)]
    rows = [
        ("펫유치원", "정기권 · 일일권 · 픽업 · 행동교정 클래스", "주간 · 반복"),
        ("펫 미용 · 스파", "기본 · 전체 미용 · 스파 · 셀프워시 · 월 구독", "고마진 · 고빈도"),
        ("동물병원", "위탁 입점 · 매출연동 임대 + 제휴(RS)", "앵커 · 저위험"),
        ("펫용품 리테일", "매대 · 구독(정기배송) · 온라인 · 번들", "고마진 · 반복"),
    ]
    table(s, MX, 1.9, cols, rows, 0.6, body=12)
    box(s, MX, 4.95, 5.85, 1.6, SAND)
    text(s, MX + 0.3, 5.12, 5.3, 1.35, [
        ("운영 시너지", 13, INK, True, 5),
        ("· 교차 인력 (주간 유치원 · 야간 호텔)", 12, INK, False, 3),
        ("· 공용 픽업 차량 · 관제실 · 백오피스", 12, INK, False, 3),
        ("· 공용 PET-Aeye (두 업태 쇼룸 → SaaS)", 12, INK, False),
    ])
    box(s, 6.75, 4.95, 5.88, 1.6, ACCENT_WASH)
    text(s, 7.05, 5.12, 5.3, 1.35, [
        ("단계", 13, ACCENT, True, 5),
        ("Phase 1 · 호텔 오픈 + 리테일 선오픈", 12, INK, False, 3),
        ("Phase 2 · 유치원 · 미용 · 병원 입점 · 멤버십", 12, INK, False, 3),
        ("Phase 3 · 아카데미 · 커뮤니티 · SaaS 확장", 12, INK, False),
    ])
    text(s, MX, 6.7, 11.9, 0.3, [("두 엔진은 고객 · 브랜드 · PET-Aeye를 공유합니다. 별관은 '매일 오는 이유'로 본관의 비수기를 메웁니다.", 11, GRAY, False)])

    # ========================= 확장 · 캠퍼스 자산 =========================
    page += 1
    section_divider(prs, "확장 · 캠퍼스 자산", "주차 100대 · 잔디밭 · 카페를 집객 엔진으로",
                    ["가든 카페 + 오프리쉬 독파크 — 신도시 주말 목적지",
                     "공항 원스톱 — 주차 + 보딩 + 샌딩 한 번에",
                     "잔디밭 + 주차 100대로 이벤트 · 대관 수익"])

    # A. 가든 카페 + 독파크
    page += 1
    s = new_slide(prs)
    frame(s, page, "확장 · 캠퍼스", "A. 가든 카페 + 오프리쉬 독파크 — 집객 플라이휠")
    acards = [
        ("잔디밭 → 독파크", "오프리쉬 · 어질리티\n입장권 · 멤버십"),
        ("1층 카페 → 허브", "브런치 · 베이커리\n수제간식 · 생일 케이크"),
        ("주차 100대 → 목적지", "차량 의존 상권에서\n'모을 수 있다'는 우위"),
    ]
    for i, (h, b) in enumerate(acards):
        x = MX + i * 4.05
        hline(s, x, 2.0, 3.75, INK, 0.02)
        text(s, x, 2.2, 3.7, 0.4, [(h, 16, INK, True)])
        text(s, x, 2.95, 3.7, 1.2, [(t, 12, GRAY, False, 3) for t in b.split("\n")])
    box(s, MX, 4.5, CW, 2.0, ACCENT_WASH)
    text(s, MX + 0.35, 4.7, 11.3, 1.7, [
        ("플라이휠 — 미끼로 모아 전환으로 번다", 14, ACCENT, True, 6),
        ("카페 · 독파크로 집객(반려가구 + 일반 신도시 주민) → 미용 · 유치원 · 리테일 · 호텔로 전환 → PET-Aeye로 안심 증명 → 재방문.", 13, INK, False, 4),
        ("수익: 독파크 입장 · 멤버십 · F&B · 수제간식 / 카페는 비반려 고객까지 유입하는 집객 엔진.", 12, GRAY, False),
    ])
    text(s, MX, 6.75, 11.9, 0.3, [("* 독파크는 견종 규칙 · 배상책임보험 · 안전요원 운영을 전제로 설계합니다.", 10, GRAY, False)])

    # B. 공항 원스톱
    page += 1
    s = new_slide(prs)
    frame(s, page, "확장 · 캠퍼스", "B. 공항 원스톱 — 주차 + 보딩 + 샌딩, 한 번에")
    bsteps = [
        ("①  지하 장기주차", "100대 · 전기차 충전\n출국 동안 차량 보관"),
        ("②  반려 보딩", "본관 위탁(중대형 OK)\nPET-Aeye 안심 열람"),
        ("③  공항 샌딩", "T1 차로 10분\n출국 · 귀국 픽업"),
    ]
    colw = CW / 3
    for i, (h, b) in enumerate(bsteps):
        x = MX + i * colw
        box(s, x + 0.1, 2.1, colw - 0.5, 2.3, ACCENT_WASH if i == 1 else SAND)
        text(s, x + 0.4, 2.4, colw - 1.0, 1.8, [(h, 17, INK, True, 6)] + [(t, 12, GRAY, False, 3) for t in b.split("\n")])
        if i < 2:
            text(s, x + colw - 0.45, 2.95, 0.5, 0.5, [("→", 24, GRAY, True)], PP_ALIGN.CENTER)
    box(s, MX, 4.9, CW, 1.6, SAND)
    text(s, MX + 0.35, 5.1, 11.3, 1.3, [
        ("왜 이기나", 14, INK, True, 6),
        ("공항 공식 채널이 받기 어려운 중대형견 + '주차 · 보딩 · 샌딩' 원스톱 편의를 영종 10분 거리에서 제공합니다.", 13, INK, False, 4),
        ("출국객 수요가 본관 가동률의 안정적 기반이 되고, 귀국 동선에서 미용 · 리테일로 연결됩니다.", 12, GRAY, False),
    ])

    # C. 이벤트 · 대관
    page += 1
    s = new_slide(prs)
    frame(s, page, "확장 · 캠퍼스", "C. 이벤트 · 대관 — 잔디밭 + 주차 100대")
    citems = [
        ("소규모 행사", "펫 돌 · 생일 · 입양식\n반려 웨딩 · 소셜 모임"),
        ("페스티벌 · 마켓", "펫 플리마켓 · 팝업\n부스 임대 + F&B"),
        ("브랜드 촬영 · 대여", "잔디 · 카페 · 주차\n촬영지 · 협찬 유입"),
        ("클래스 · 커뮤니티", "운동회 · 도그 요가\n멤버십 정기 모임"),
    ]
    for i, (h, b) in enumerate(citems):
        cx = MX + (i % 2) * 6.1
        cy = 1.95 + (i // 2) * 2.3
        hline(s, cx, cy, 5.8, INK, 0.02)
        text(s, cx, cy + 0.18, 5.7, 0.4, [(h, 16, ACCENT if i == 0 else INK, True)])
        text(s, cx, cy + 0.7, 5.7, 1.3, [(t, 13, GRAY, False, 4) for t in b.split("\n")])
    text(s, MX, 6.55, 11.9, 0.5, [("수익: 대관료 + 부스 임대 + F&B + 협찬. 이벤트 집객이 전 사업 노출과 미디어 · 제휴 유입으로 이어집니다.", 11, GRAY, False)])

    # ========================= PART 3 · PET-Aeye =========================
    page += 1
    section_divider(prs, "PART 3 · PET-Aeye (제품)", "보고, 알리고, 요약합니다",
                    ["전 객실 라이브 관제와 AI 행동 이벤트",
                     "스태프 앱과 보호자 앱, 그리고 일일 CareReport",
                     "모든 기록을 Stay(위탁 1건) 하나로 연결합니다"])

    # PET-Aeye overview
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 3 · PET-Aeye", "PET-Aeye — 보고, 알리고, 요약합니다")
    loop = [("보고", "룸별 카메라 라이브\n검출 오버레이"), ("알리고", "장시간 무움직임 · 이상 행동\n스태프 우선 알림"), ("요약", "Stay 단위 일일 리포트\n보호자 기간 한정 링크")]
    for i, (h, b) in enumerate(loop):
        x = MX + i * 2.05
        box(s, x, 2.0, 1.85, 1.85, ACCENT if i == 0 else INK, MSO_SHAPE.OVAL)
        text(s, x, 2.0, 1.85, 1.85, [(h, 20, WHITE, True)], PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
        text(s, x - 0.1, 4.05, 2.05, 1.0, [(t, 11, GRAY, False, 2) for t in b.split("\n")], PP_ALIGN.CENTER)
    text(s, MX, 5.05, 6.1, 1.0, [("원 사업계획의 '24시간 CHECKING SYSTEM'을 사람의 순찰과 PET-Aeye가 함께 맡습니다.", 12, INK, False)])
    vline(s, 7.0, 1.95, 4.5)
    text(s, 7.35, 1.95, 5.3, 0.35, [("스태프용 관제", 13, ACCENT, True)])
    text(s, 7.35, 2.35, 5.3, 1.6, [(f"✓  {t}", 13, INK, False, 5) for t in [f"{total_rooms}실 룸 그리드 · 이벤트 타임라인", "AI 검출 · 추적 · 행동 라벨", "이상 행동 알림 · PTZ 자동 추적 · 녹화"]])
    text(s, 7.35, 3.95, 5.3, 0.35, [("보호자용 안심", 13, ACCENT, True)])
    text(s, 7.35, 4.35, 5.3, 1.6, [(f"✓  {t}", 13, INK, False, 5) for t in ["기간 한정 링크로 배정 룸 라이브", "Stay 단위 일일 CareReport", "퇴실 후 하이라이트 클립"]])
    text(s, MX, 6.45, 11.9, 0.35, [("구성: RTSP 수신 · 녹화 · YOLO + ByteTrack · 이벤트 DB · 실시간 WebSocket · 관리자 웹 · 보호자 웹", 10, GRAY, False)])

    # Admin mockup
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 3 · PET-Aeye", "관리자 관제 화면 — 112실을 한 화면에서")
    pic = s.shapes.add_picture(ADMIN_IMG, I(MX), I(2.0), height=I(4.6))
    pic.line.color.rgb = RULE
    pic.line.width = Pt(0.75)
    ann = [("룸 그리드 관제", "전 객실 라이브를 한 화면에서"), ("AI 검출 오버레이", "개체 · 행동 · 신뢰도 실시간"), ("이상 감지 강조", "확인 필요한 객실만 눈에 띄게"), ("실시간 이벤트", "급식 · 산책 · 알림 로그")]
    for i, (h, d) in enumerate(ann):
        y = 2.05 + i * 1.05
        text(s, 9.15, y, 3.45, 0.9, [(h, 15, ACCENT, True, 3), (d, 12, GRAY, False)])
        if i < len(ann) - 1:
            hline(s, 9.15, y + 0.9, 3.45)
    text(s, MX, 6.75, 11.9, 0.3, [("* 화면은 구성 예시입니다.", 10, GRAY, False)])

    # Apps mockup
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 3 · PET-Aeye", "스태프 앱 · 보호자 앱")
    s.shapes.add_picture(STAFF_IMG, I(0.95), I(1.75), height=I(5.1))
    s.shapes.add_picture(GUARD_IMG, I(6.95), I(1.75), height=I(5.1))
    text(s, 3.55, 2.0, 2.95, 4.6, [
        ("스태프 앱", 16, ACCENT, True, 10),
        ("확인 필요 알림을 가장 위에", 13, INK, True, 2), ("한 객실만 빠르게 판단합니다", 11, GRAY, False, 12),
        ("객실 라이브 + AI 오버레이", 13, INK, True, 2), ("알림 화면에서 바로 확인", 11, GRAY, False, 12),
        ("현장 확인 / 정상 처리", 13, INK, True, 2), ("한 번의 조작으로 처리", 11, GRAY, False, 12),
        ("담당 층 할 일 · 케어 로그", 13, INK, True, 2), ("급식 · 산책 · 투약 체크", 11, GRAY, False),
    ])
    text(s, 9.55, 2.0, 3.05, 4.6, [
        ("보호자 앱", 16, ACCENT, True, 10),
        ("배정 객실만 실시간 열람", 13, INK, True, 2), ("전체 시설이 아닌 내 반려견 방", 11, GRAY, False, 12),
        ("오늘의 CareReport", 13, INK, True, 2), ("급식 · 산책 · 휴식 요약", 11, GRAY, False, 12),
        ("하이라이트 클립", 13, INK, True, 2), ("하루 활동을 짧은 영상으로", 11, GRAY, False, 12),
        ("기간 한정 안심 링크", 13, INK, True, 2), ("체크아웃까지 열리고 자동 만료", 11, GRAY, False),
    ])

    # Stay graduation report mockup
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 3 · PET-Aeye", "Stay 졸업 리포트 — 투숙 영상으로 만든 종합 행동분석")
    s.shapes.add_picture(GRAD_IMG, I(1.0), I(1.65), height=I(5.6))
    text(s, 4.95, 1.95, 3.65, 0.4, [("담기는 것", 15, ACCENT, True, 8)])
    grad_items = [
        ("활동 · 수면 요약", "투숙 전 기간 활동량 · 수면 패턴"),
        ("적응 곡선", "첫날 대비 안정도 변화"),
        ("행동 프로파일", "성향 · 분리불안 신호"),
        ("하이라이트 클립 묶음", "특이 이벤트 타임라인"),
        ("케어 로그 · 스태프 코멘트", "급식 · 산책 · 투약 + 다음 방문 팁"),
    ]
    for i, (h, d) in enumerate(grad_items):
        y = 2.45 + i * 0.74
        text(s, 4.95, y, 3.65, 0.68, [(h, 13, INK, True, 2), (d, 11, GRAY, False)])
    text(s, 8.9, 1.95, 3.7, 0.4, [("왜 보내나", 15, ACCENT, True, 8)])
    grad_why = [
        ("한계비용 ≈ 0", "투숙 영상 · 이벤트는 이미 쌓입니다.\n체크아웃에 자동 생성만 붙입니다."),
        ("재방문 · 추천 엔진", "공유하고 싶은 결과물 → 자연 바이럴,\n공식 채널엔 없는 차별점."),
        ("유료 옵션 · 데이터 자산", "안심 패키지 포함 또는 프리미엄,\n성향 베이스라인이 쌓입니다."),
    ]
    for i, (h, d) in enumerate(grad_why):
        y = 2.45 + i * 1.2
        runs = [(h, 13, INK, True, 2)] + [(t, 11, GRAY, False, 2) for t in d.split("\n")]
        text(s, 8.9, y, 3.7, 1.1, runs)
    text(s, 4.95, 6.35, 7.65, 0.6, [("P1 일일 CareReport의 연장 → Stay 종합 리포트는 P1 후반~P2. 행동 수치는 검증된 지표 중심, 의료 진단이 아닙니다.", 11, GRAY, False)])

    # Journey
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 3 · PET-Aeye", "고객 여정마다 PET-Aeye가 붙는 지점")
    steps = [
        ("예약", "룸 타입 · 기간\n옵션 접수", "Stay 사전 생성"),
        ("체크인", "건강 문진\n동의서 서명", "룸 · 카메라 배정\n보호자 링크 발송"),
        ("투숙 중", "급식 · 산책\n청소 · 순찰", "룸 그리드 관제\n이상 행동 알림"),
        ("매일 저녁", "케어 메모\n작성", "CareReport\n자동 생성 · 발송"),
        ("체크아웃", "인계 · 결제", "링크 만료\n하이라이트 클립"),
        ("이후", "재방문 안내", "Stay 이력\n성향 기록"),
    ]
    lx, colw = MX + 1.45, (CW - 1.45) / len(steps)
    text(s, MX, 2.75, 1.3, 0.4, [("호텔 업무", 12, GRAY, True)])
    text(s, MX, 4.35, 1.3, 0.4, [("PET-Aeye", 12, ACCENT, True)])
    hline(s, MX, 2.45, CW, INK, 0.02)
    hline(s, MX, 4.1, CW)
    box(s, lx, 4.15, CW - 1.45, 1.5, ACCENT_WASH)
    for i, (name, hotel, pt) in enumerate(steps):
        x = lx + i * colw
        text(s, x + 0.1, 2.0, colw - 0.2, 0.4, [(name, 15, INK, True)])
        text(s, x + 0.1, 2.75, colw - 0.2, 1.2, [(t, 12, INK, False, 2) for t in hotel.split("\n")])
        text(s, x + 0.1, 4.35, colw - 0.2, 1.2, [(t, 12, INK, True, 2) for t in pt.split("\n")])
        if i:
            vline(s, x, 2.6, 3.05)
    text(s, MX, 6.0, 11.9, 0.6, [("모든 기록은 Stay(위탁 1건)에 묶여, 호텔 업무 단위와 PET-Aeye 데이터 단위가 같아집니다.", 12, GRAY, False)])

    # Camera layout
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 3 · PET-Aeye", "카메라 배치 기준")
    cols = [("구역", 2.3), ("층", 0.9), ("수량 기준", 2.6), ("목적", 2.9), ("보호자 노출", 3.23)]
    rows = [
        ("소형 · 중형 객실", "2F", "86실 · 객실당 1대", "위탁 본체 관제", "배정 룸 라이브"),
        ("대형 · 패밀리 객실", "3F", "26실 · 객실당 1대 이상", "중대형 관제 · 우선 설치", "배정 룸 라이브"),
        ("라운지 · 플레이존", "2–3F", "구역당 1대 (PTZ)", "놀이 시간 관찰", "하이라이트 클립"),
        ("옥상 · 넓은 플레이", "옥상·실외", "카메라 + BLE 태그", "개체 ID · 구역 체류", "위치 요약 · 하이라이트"),
        ("복도 · 이중문", "2–3F", "출입구별 1대", "탈출 방지 · 보안", "비노출"),
        ("프런트 · 스파 · 미용", "1F", "구역당 1대", "체크인 · 서비스 기록", "선택 노출"),
    ]
    table(s, MX, 1.75, cols, rows, 0.55, body=12)
    text(s, MX, 5.55, 11.9, 1.2, [
        ("함께 갖출 인프라", 13, ACCENT, True, 6),
        ("PoE 스위치 · 녹화 스토리지 · 관제실 모니터 · 이중화 회선 · UPS · (넓은 공간) BLE 게이트웨이 PoE", 13, INK, False, 4),
        ("넓은 공간 BLE: Minew MWB01 + MOKO MKGW1-BW — 다음 슬라이드 · 문서 PET-Aeye_넓은공간_BLE개체추적_초안.md", 11, GRAY, False),
    ])

    # BLE outdoor tracking
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 3 · PET-Aeye", "넓은 공간 BLE 개체 추적 — MWB01 + MKGW1-BW")
    cols = [("구분", 2.0), ("제품", 3.2), ("역할", 6.73)]
    rows = [
        ("목줄 태그", "Minew MWB01", "목줄 관통·몸쪽 밀착 실리콘 케이스 · IP67 · 개체 ID"),
        ("게이트웨이", "MOKO MKGW1-BW", "BLE 스캔 → MQTT/HTTP · PoE · 야외는 방수함"),
        ("카메라", "NPU / 실외 CCTV", "행동 · 이상행동 · 보안 녹화 (비전)"),
        ("PET-Aeye", "수집 · 바인딩", "태그↔Stay 조인 · 구역 체류 · 이탈 알림"),
    ]
    table(s, MX, 1.7, cols, rows, 0.48, body=12)
    try:
        s.shapes.add_picture(BLE_ASSETS + r"\ble_playground_gateway_plan.jpg", I(MX), I(4.0), width=I(3.9))
        s.shapes.add_picture(BLE_ASSETS + r"\ble_rooftop_gateway_plan.jpg", I(4.85), I(4.0), width=I(3.9))
        s.shapes.add_picture(BLE_ASSETS + r"\ble_collar_slide_on_silicone_case.png", I(9.0), I(4.0), width=I(3.63))
    except OSError:
        text(s, MX, 4.2, CW, 0.4, [("배치도 · 목줄 케이스: assets/ble_tracking/", 12, GRAY, False)])
    text(s, MX, 6.55, CW, 0.35, [
        ("케이스: 목줄에 끼워 몸쪽 밀착(매달림·키링 금지 · 상대견 물어뜯김). 상세: BLE 초안 v0.2.", 11, GRAY, False),
    ])

    # Event -> action
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 3 · PET-Aeye", "이벤트가 생기면 누가 무엇을 하는가")
    cols = [("PET-Aeye 신호", 3.4), ("스태프 액션", 4.4), ("보호자 노출", 4.13)]
    rows = [
        ("장시간 무움직임", "현장 확인 · 필요 시 병원 연계", "리포트 기재 · 선택 시 알림"),
        ("과도한 반복 이동", "산책 · 놀이 추가 · 성향 기록", "일일 리포트"),
        ("비인가 인원 검출", "보안 점검 · 출입 기록 확인", "비노출"),
        ("카메라 연결 끊김", "즉시 점검 · 대체 순찰", "비노출"),
        ("Stay 종료", "링크 만료 · 영상 보존 정책 적용", "하이라이트 제공"),
    ]
    table(s, MX, 1.9, cols, rows, 0.62, body=13)
    box(s, MX, 5.45, CW, 1.1, SAND)
    text(s, MX + 0.35, 5.6, 11.3, 0.9, [
        ("알림은 정확도가 확인된 규칙부터 켭니다.", 14, INK, True, 4),
        ("보호자에게는 스태프가 확인한 내용만 공유합니다. 규칙과 기준값은 오픈 후 30일 데이터로 조정합니다.", 12, GRAY, False),
    ])

    # Data
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 3 · PET-Aeye", "데이터는 Stay 하나로 연결합니다")
    chain_a = [("Guardian · Pet", "보호자 · 반려견"), ("Stay", "위탁 1건"), ("Room", "객실"), ("Camera", "카메라")]
    chain_b = [("PlayZone", "플레이 · 루프탑"), ("BLE Tag", "MWB01"), ("Gateway", "MKGW1-BW"), ("Stay 조인", "동일 ID")]
    chain_c = [("Camera", "영상 · 검출"), ("PetEvent", "행동 · 알림"), ("CareReport", "일일 요약"), ("Guardian Link", "보호자 열람")]
    bw, bg = 1.38, 0.28
    for row, chain in enumerate((chain_a, chain_b, chain_c)):
        y = 1.85 + row * 1.15
        for i, (name, sub) in enumerate(chain):
            x = MX + i * (bw + bg)
            hot = name in ("Stay", "CareReport", "Stay 조인")
            box(s, x, y, bw, 0.9, ACCENT if hot else WHITE)
            text(s, x, y, bw, 0.9, [(name, 11, WHITE if hot else INK, True, 2), (sub, 9, ACCENT_DIM if hot else GRAY, False)], PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
            if i < len(chain) - 1:
                text(s, x + bw, y + 0.25, bg, 0.4, [("→", 12, GRAY, True)], PP_ALIGN.CENTER)
    text(s, MX, 5.45, 6.3, 1.1, [
        ("체크인 때 카메라 트랙을, 플레이존 입장 때 BLE 태그를 같은 Stay에 연결합니다.", 12, INK, False, 3),
        ("이후 이벤트 · 리포트 · 열람이 모두 같은 Stay에 쌓입니다.", 12, INK, False),
    ])
    vline(s, 7.35, 1.85, 4.7)
    text(s, 7.7, 1.85, 4.9, 0.35, [("호텔 시스템과 엮는 연동 작업", 13, ACCENT, True)])
    links = [
        ("예약 → Stay", "예약 확정 건으로 Stay 자동 생성"),
        ("플레이존 BLE", "입장 시 MWB01 바인딩 · 퇴장 회수"),
        ("구역(Zone) 규칙", "게이트 · 플레이존 · 이탈 알림"),
        ("열람 감사 로그", "보호자 · 스태프 영상 열람 기록"),
        ("결제 → 옵션", "안심 서비스 시 보호자 링크 활성화"),
    ]
    for i, (h, d) in enumerate(links):
        y = 2.3 + i * 0.78
        text(s, 7.7, y, 4.9, 0.7, [(h, 12, INK, True, 2), (d, 11, GRAY, False)])
        hline(s, 7.7, y + 0.68, 4.93)

    # Feature map summary (from 기능맵)
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 3 · PET-Aeye", "기능맵 요약 — P0부터 플랫폼까지")
    cols = [("우선순위", 2.0), ("초점", 2.6), ("핵심 기능", 4.13), ("화면 · API", 3.2)]
    rows = [
        ("P0 현장 관제", "스태프", "룸 모니터 그리드 · 검출 오버레이 · 이벤트 타임라인 · PTZ", "관리자 웹 · /rooms /cameras /events"),
        ("P1 보호자 안심", "보호자", "Stay 체크인/아웃 · 기간 한정 링크 · 일일 CareReport", "보호자 웹 · /stays /access-token"),
        ("P2 운영 · 연동", "운영 효율", "예약→Stay · Zone 규칙 · 케어 체크리스트 · 감사 로그", "예약 웹훅 · /guardian/:token"),
        ("P3 플랫폼(SaaS)", "다점포 · B2B", "멀티테넌트 · 역할 권한 · 외부 API · 사용량 과금", "외부 API · 웹훅"),
    ]
    table(s, MX, 1.95, cols, rows, 0.78, body=12)
    text(s, MX, 5.6, 11.9, 0.9, [
        ("코어 원칙", 12, ACCENT, True, 4),
        ("예약·결제 풀스택을 PET-Aeye에 다 넣지 않습니다. 코어 = 투숙 중인 반려견을 보고 · 알리고 · 요약한다. 상세: 본 문서 '기능 스펙' 편.", 12, GRAY, False),
    ])

    # ========================= PART 4 · 라이다 바이탈 =========================
    page += 1
    section_divider(prs, "PART 4 · 라이다 바이탈 확장", "보이는 안심에서, 느껴지는 안심으로",
                    ["CCTV에 FMCW 라이다를 결합한 융합 센서",
                     "영상 없이 호흡 · 활동 · 수면 · 낙상을 비접촉으로",
                     "기반 기술은 확보, 융합 폼팩터는 PoC · 로드맵 항목입니다"])

    # Why lidar
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 4 · 라이다 바이탈", "카메라가 못 보는 곳을, 라이다가 채웁니다")
    box(s, MX, 1.95, 5.75, 4.5, WHITE)
    box(s, 6.85, 1.95, 5.78, 4.5, ACCENT_WASH)
    text(s, MX + 0.35, 2.25, 5.1, 4.0, [
        ("지금 PET-Aeye", 13, ACCENT, True, 8), ("카메라 + AI 행동 검출", 15, INK, True, 2), ("무엇을 하고 있는지 '봅니다'", 12, GRAY, False, 12),
        ("한계", 13, GRAY, True, 6), ("· 소등된 야간에는 약합니다", 13, INK, False, 4), ("· 거리·속도 같은 물리량은 직접 못 읽습니다", 13, INK, False, 4), ("· 영상 노출에 민감한 보호자가 있습니다", 13, INK, False, 0),
    ])
    text(s, 7.2, 2.25, 5.1, 4.0, [
        ("더하는 것 · FMCW 라이다", 13, ACCENT, True, 8), ("거리·속도·3D 비접촉 센싱", 15, INK, True, 2), ("'괜찮은 상태인지'를 느낍니다", 12, GRAY, False, 12),
        ("강점", 13, GRAY, True, 6), ("· 빛이 없어도 호흡·재실 확인", 13, INK, False, 4), ("· μm급 변위로 미세 움직임 포착", 13, INK, False, 4), ("· 영상이 아닌 데이터 → 프라이버시", 13, INK, False, 0),
    ])

    # Wavedyne tech
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 4 · 라이다 바이탈", "검증된 FMCW 라이다 반도체 기술 위에 올립니다")
    cards = [("WD-FMCW 4세대", "거리·속도·재질 동시 (6D)\nμm급 · 1,000만 포인트"), ("솔리드스테이트", "KTN + 메타렌즈\n기계 구동부 0 · 소형"), ("카메라 융합", "LiDAR + Camera Fusion\n멀티모달 AI SoC 내장"), ("비접촉 바이탈", "흉곽 μm 변위 · 도플러\n호흡·미동·재실")]
    for i, (h, b) in enumerate(cards):
        x = MX + i * 3.0
        hline(s, x, 2.0, 2.75, INK, 0.02)
        text(s, x, 2.2, 2.7, 0.5, [(h, 16, INK, True)])
        text(s, x, 2.95, 2.7, 1.2, [(t, 12, GRAY, False, 3) for t in b.split("\n")])
    box(s, MX, 4.6, CW, 1.85, SAND)
    text(s, MX + 0.35, 4.85, 11.3, 1.4, [
        ("전제", 13, ACCENT, True, 6),
        ("FMCW 라이다 반도체의 기반 기술은 이미 확보되어 있습니다. CCTV에 결합하는 융합 폼팩터만 설계하면 됩니다.", 14, INK, False, 6),
        ("따라서 바이탈은 '지금 운영 기능'이 아니라, 저희 일정에 맞춘 PoC·로드맵으로 단계 검증합니다.", 13, GRAY, False),
    ])

    # Vitals
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 4 · 라이다 바이탈", "비접촉으로 읽는 개체 상태")
    cols = [("항목", 3.2), ("방식", 5.2), ("도입 단계 · 신뢰도", 3.53)]
    rows = [
        ("호흡수 · 호흡 패턴", "흉곽 미세 변위(μm) 측정", "1차 · 높음"),
        ("미동 · 활동량", "순간 속도(도플러)로 움직임", "1차 · 높음"),
        ("재실 · 자세 · 낙상", "3D 포인트 위치·높이 변화", "1차 · 높음"),
        ("수면 · 휴식 깊이", "호흡·미동의 규칙성 추정", "2차 · 중간"),
        ("체형 · 대략 체중", "3D 스캔 부피 추정", "2차 · 중간(보정)"),
        ("심박 추정", "미세 진동 성분 분리", "검증 후 · 조건부"),
    ]
    table(s, MX, 1.95, cols, rows, 0.6, body=13)
    text(s, MX, 5.95, CW, 0.5, [("의료 진단이 아니라 '웰니스·안심' 지표로 포지셔닝합니다. 이상 소견은 수의 상담 권유로 연결합니다.", 12, GRAY, False)])

    # Form factor
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 4 · 라이다 바이탈", "CCTV + 라이다 융합 센서 한 대")
    parts2 = [("카메라 모듈", "영상 · AI 행동 검출", "현재 PET-Aeye", SAND), ("FMCW 라이다", "거리 · 속도 · 3D", "호흡·미동·재실·낙상", ACCENT), ("엣지 AI 퓨전", "센서 융합 → 상태 요약", "멀티모달 AI SoC", INK)]
    for i, (h, b, c, color) in enumerate(parts2):
        x = MX + i * 4.1
        box(s, x, 2.1, 3.6, 2.5, color)
        fg = INK if color == SAND else WHITE
        sub = GRAY if color == SAND else (ACCENT_DIM if color == ACCENT else NIGHT_GRAY)
        text(s, x + 0.3, 2.4, 3.0, 1.9, [(h, 18, fg, True, 6), (b, 13, fg, False, 4), (c, 11, sub, False)])
        if i < 2:
            text(s, x + 3.6, 3.1, 0.5, 0.5, [("+", 24, GRAY, True)], PP_ALIGN.CENTER)
    box(s, MX, 4.95, CW, 1.5, ACCENT_WASH)
    text(s, MX + 0.35, 5.15, 11.3, 1.2, [
        ("1실 1센서 · 기존 PET-Aeye 네트워크(관제실·녹화·관리자 웹)에 바이탈 채널만 추가합니다.", 14, INK, True, 6),
        ("우선 적용: 3F 중대형·패밀리 26실, 격리실·노령견 객실부터 단계 적용합니다.", 12, GRAY, False),
    ])

    # Report vital
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 4 · 라이다 바이탈", "보호자 리포트에 바이탈을 더합니다")
    cols = [("리포트 블록", 2.8), ("기존", 4.0), ("추가 (라이다)", 5.13)]
    rows = [
        ("활동", "산책 횟수·거리", "시간대별 활동량 그래프"),
        ("휴식", "낮잠·야간 숙면(정성)", "호흡수 추이 · 수면 안정도(정량)"),
        ("안심", "이상 행동 알림", "호흡 급변 · 장시간 무미동 · 낙상 조기 알림"),
        ("요약", "스태프 메모", "'오늘 호흡·휴식 안정' 상태 한 줄 요약"),
    ]
    table(s, MX, 1.95, cols, rows, 0.72, body=13)
    box(s, MX, 5.35, CW, 1.1, SAND)
    text(s, MX + 0.35, 5.5, 11.3, 0.9, [
        ("확장성", 14, INK, True, 4),
        ("시니어·메디컬 케어, 야간·사각 보완, 낙상·발작 조기경보, 객실 환경 최적화, 3D 체형 기록, SaaS Vital 티어로 넓힙니다.", 12, GRAY, False),
    ])

    # Lidar roadmap
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 4 · 라이다 바이탈", "단계로 나눠 검증하고 상품화합니다")
    phases = [
        ("P0 · PoC 설계", ["측정 항목·리포트 정의", "1실 실증 설계"], "센서 사양 확정"),
        ("P1 · 단일 객실 실증", ["호흡·활동·재실 정확도", "반려견 대상 검증"], "융합 모듈 시작"),
        ("P2 · 융합 폼팩터", ["CCTV+라이다 센서 제작", "3F·격리실 적용"], "현장 적용 확대"),
        ("P3 · 상품화", ["바이탈 CareReport 정식", "SaaS Vital 티어"], "정식 상품 · SaaS"),
    ]
    hline(s, MX, 2.35, CW, INK, 0.02)
    for i, (name, items, gate) in enumerate(phases):
        x = MX + i * 3.05
        dot(s, x + 0.12, 2.36, 0.24, ACCENT if i <= 1 else INK)
        text(s, x, 2.6, 2.85, 0.45, [(name, 15, INK, True)])
        text(s, x, 3.2, 2.85, 1.6, [(f"·  {t}", 13, INK, False, 6) for t in items])
        box(s, x, 4.9, 2.85, 0.75, SAND)
        text(s, x + 0.15, 4.9, 2.6, 0.75, [(gate, 12, INK, True)], PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    text(s, MX, 6.0, CW, 0.9, [
        ("유의", 12, ACCENT, True, 4),
        ("반려견은 털·체격·품종 편차가 커 검증이 더 필요합니다. 심박은 검증 후 조건부. 의료기기 아님 — 웰니스 지표로 포지셔닝.", 12, GRAY, False),
    ])

    # ========================= PART 5 · 비즈니스 & 확장 =========================
    page += 1
    section_divider(prs, "PART 5 · 비즈니스 & 확장", "한 번에 하나씩, 순서대로 켭니다",
                    ["NOW 위탁 숙박 · NEXT PET-Aeye 안심 옵션 · LATER PET-Aeye SaaS",
                     "본관 숙박에 유치원 · 미용(위탁) · 리테일 · 카페 · 이벤트를 더합니다",
                     "영종을 쇼룸으로, PET-Aeye를 다른 시설(카메라당 구독)과 가정(홈서비스)에 공급합니다"])

    # Business model
    page += 1
    s = new_slide(prs)
    frame(s, page, "BUSINESS MODEL", "매출원은 한 번에 하나씩, 순서대로 켭니다")
    engines = [
        ("NOW", "위탁 숙박 + 생활권", "체중별 객실 · 유치원\n미용(위탁 RS) · 리테일 · 카페", "가동률 · 부문 매출"),
        ("NEXT", "PET-Aeye 안심 옵션", "실시간 열람 + AI 리포트\n1박당 부가 · VIP 객실 포함", "옵션 선택률 · 재이용"),
        ("LATER", "PET-Aeye SaaS · 2차", "타 펫호텔·유치원 구독\nB1F 데이케어 · 나동", "외부 고객 · 확장 판단"),
    ]
    for i, (tag, name, desc, kpi) in enumerate(engines):
        x = MX + i * 4.05
        top = 2.0 + (2 - i) * 0.35
        hgt = 4.3 - (2 - i) * 0.35
        box(s, x, top, 3.8, hgt, ACCENT if i == 0 else (INK if i == 1 else SAND))
        fg = WHITE if i < 2 else INK
        sub = ACCENT_DIM if i == 0 else (NIGHT_GRAY if i == 1 else GRAY)
        text(s, x + 0.3, top + 0.3, 3.3, 0.3, [(tag, 11, sub, True)])
        text(s, x + 0.3, top + 0.7, 3.3, 0.5, [(name, 20, fg, True)])
        text(s, x + 0.3, top + 1.4, 3.3, 1.4, [(d, 13, fg, False, 3) for d in desc.split("\n")])
        text(s, x + 0.3, top + hgt - 0.6, 3.3, 0.35, [(f"KPI  {kpi}", 12, sub, True)])

    # Unit economics (portfolio)
    page += 1
    s = new_slide(prs)
    frame(s, page, "UNIT ECONOMICS", f"부문별 연매출 — 다각화로 기준 시나리오 약 {pf_totals[1]:.0f}억 원")
    data = CategoryChartData()
    data.categories = ["보수", "기준", "공격"]
    data.add_series("연매출 합계", [round(t, 1) for t in pf_totals])
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, I(MX), I(1.95), I(5.5), I(4.0), data)
    style_chart(gf.chart, '0"억 원"', [SAND, ACCENT, SAND])
    text(s, MX, 6.0, 5.5, 0.9, [
        ("전 사업부문 합계 · 매출 기준 · 비용 미반영 · 실사 전 가정", 11, GRAY, False, 3),
        (f"본관 호텔은 가동률 30 · 45 · 60% 기준(약 {revenues[0]:.1f} · {revenues[1]:.1f} · {revenues[2]:.1f}억), 별관·캠퍼스는 부문 가정치입니다.", 10, GRAY, False),
    ])
    cols = [("사업 부문", 3.1), ("보수", 0.95), ("기준", 0.95), ("공격", 0.95)]
    rows = [(name, f"{v[0]:.1f}", f"{v[1]:.1f}", f"{v[2]:.1f}") for name, v in pf_lines]
    rows.append(("합계 (억 원)", f"{pf_totals[0]:.1f}", f"{pf_totals[1]:.1f}", f"{pf_totals[2]:.1f}"))
    table(s, 6.6, 1.9, cols, rows, 0.4, body=10, head_gap=0.4)
    text(s, 6.6, 6.55, 5.95, 0.6, [("* 미용은 위탁 RS 30% · 동물병원은 임대+제휴 · 하드웨어는 구독+B2B(양산 후) · 리테일은 매출 기준(마진 별도).", 9, GRAY, False)])

    # 인력 · 고정비
    page += 1
    s = new_slide(prs)
    frame(s, page, "COST STRUCTURE", "인력 · 고정비 — 안정기 기준 (실사 전 가정)")
    text(s, MX, 1.9, 5.6, 0.4, [("인력 규모 (FTE)", 13, ACCENT, True)])
    hc_cols = [("부문", 3.0), ("개업", 0.9), ("안정기", 1.0)]
    hc_rows = [
        ("본관 호텔 케어 (24h)", "6", "9"),
        ("관제 · 프런트", "2", "3"),
        ("펫유치원", "2", "3"),
        ("훈련사 (행동)", "위탁", "1"),
        ("리테일 · 카페", "2", "3"),
        ("픽업 · 시설", "1", "2"),
        ("경영 · 지원", "2", "3"),
        ("합계 (명)", "15", "24"),
    ]
    table(s, MX, 2.35, hc_cols, hc_rows, 0.43, body=11, head_gap=0.4)
    text(s, MX, 6.3, 5.6, 0.7, [
        ("· 24h 케어 3교대 상주 · 미용 = 위탁 · 병원 = 입점 수의사 별도.", 10, GRAY, False, 2),
        ("· 훈련사는 개업 위탁 → 안정기 정규 1명(유치원 겸직).", 10, GRAY, False),
    ])
    text(s, 6.9, 1.9, 5.7, 0.4, [("월 고정 · 준고정비 (만원/월)", 13, ACCENT, True)])
    fc_cols = [("항목", 3.7), ("월 (만원)", 1.8)]
    fc_rows = [
        ("인건비 (4대보험 포함)", "8,450"),
        ("수도광열 (24h 냉난방·환기)", "1,200"),
        ("자산 금융비 (인수 조달)", "2,000"),
        ("사료 · 소모품 · 위생", "600"),
        ("보험 · 세금 · 공과", "400"),
        ("마케팅", "700"),
        ("유지보수 · 보안 · IT", "800"),
        ("합계 (월)", "14,150"),
    ]
    table(s, 6.9, 2.35, fc_cols, fc_rows, 0.43, body=11, head_gap=0.4)
    text(s, 6.9, 6.3, 5.7, 0.7, [
        ("· 연환산 약 17.0억 원. 금융비는 인수가 · 조달 구조 가정치.", 10, GRAY, False, 2),
        ("· 리테일 매입 · 결제수수료 등 변동비와 위탁 정산은 별도.", 10, GRAY, False),
    ])

    # SaaS targets
    page += 1
    s = new_slide(prs)
    frame(s, page, "SaaS", "타깃 고객 — 반려견을 맡아 두는 모든 시설")
    segs = [("01 · 핵심", "위탁형 펫호텔", "보호자 문의 응대 부담\n야간 관제 인력 부족", "Plus"), ("02", "유치원 · 데이케어", "등원 중 보호자 확인 요구\n놀이 · 사회화 기록", "Plus"), ("03", "동물병원 입원실", "입원견 상태 관찰\n보호자 면회 대체", "Basic → Plus"), ("04", "위탁 훈련소", "장기 위탁 중\n훈련 진행 공유", "Plus")]
    for i, (tag, name, need, pkg) in enumerate(segs):
        x = MX + i * 3.03
        hline(s, x, 2.0, 2.8, ACCENT if i == 0 else INK, 0.03)
        text(s, x, 2.2, 2.8, 0.3, [(tag, 11, ACCENT, True)])
        text(s, x, 2.55, 2.8, 0.5, [(name, 18, INK, True)])
        text(s, x, 3.3, 2.8, 0.3, [("필요", 11, GRAY, True)])
        text(s, x, 3.65, 2.8, 1.0, [(t, 13, INK, False, 3) for t in need.split("\n")])
        text(s, x, 4.75, 2.8, 0.3, [("추천 패키지", 11, GRAY, True)])
        text(s, x, 5.1, 2.8, 0.4, [(pkg, 15, ACCENT if i == 0 else INK, True)])
    text(s, MX, 6.2, 11.9, 0.5, [("첫 판매 대상은 영종과 운영 방식이 같은 위탁형 펫호텔입니다. 나머지는 파일럿 결과를 보고 순서를 정합니다.", 12, GRAY, False)])

    # SaaS packages
    page += 1
    s = new_slide(prs)
    frame(s, page, "SaaS", "패키지 구성 — Basic · Plus · Pro (+Vital)")
    pkgs = [("BASIC", "스태프 관제", ["카메라 등록 · 룸 매핑", "룸 그리드 라이브", "AI 검출 · 이벤트", "녹화 · 보관", "스태프 알림"], SAND), ("PLUS", "보호자 안심", ["Basic 전체", "Stay 관리", "보호자 기간 한정 링크", "일일 CareReport · 하이라이트", "Stay 졸업 리포트", "시설 로고 · 이름"], ACCENT), ("PRO", "다지점 · 연동", ["Plus 전체", "다지점 통합 관제", "예약 API · 웹훅", "권한 · 열람 감사 로그", "전담 온보딩"], INK)]
    for i, (tag, name, items, color) in enumerate(pkgs):
        x = MX + i * 4.05
        box(s, x, 1.95, 3.8, 3.5, color)
        fg = INK if color == SAND else WHITE
        sub = GRAY if color == SAND else (ACCENT_DIM if color == ACCENT else NIGHT_GRAY)
        text(s, x + 0.3, 2.2, 3.3, 0.3, [(tag, 11, sub, True)])
        text(s, x + 0.3, 2.55, 3.3, 0.5, [(name, 20, fg, True)])
        text(s, x + 0.3, 3.25, 3.3, 2.1, [(f"·  {t}", 13, fg, False, 5) for t in items])
    box(s, MX, 5.65, CW, 0.9, ACCENT_WASH)
    text(s, MX + 0.35, 5.78, 11.3, 0.7, [
        ("상위 티어 VITAL — 라이다 융합 센서 + 바이탈 리포트 번들 (PART 4, PoC 이후)", 14, INK, True, 4),
        ("과금(안): 카메라 1대당 월 — Basic 1.5만 · Plus 2.5만 · Pro 3.0만 · Vital 4.5만 원(잠정) · VAT 별도 + 설치 · 온보딩 1회. 근거는 다음 장.", 11, GRAY, False),
    ])

    # SaaS pricing
    page += 1
    s = new_slide(prs)
    frame(s, page, "SaaS PRICING", "카메라 1대당 월 구독 — 주력 Plus 2.5만 원")
    tiers = [("BASIC", "15,000원", "공용 카메라 · 관제만"), ("PLUS", "25,000원", "객실 카메라 · 보호자 안심"), ("PRO", "30,000원", "체인 · 다지점 · 연동"), ("VITAL", "45,000원", "바이탈 센서 렌탈 (잠정)")]
    for i, (tag, price, sub) in enumerate(tiers):
        x = MX + i * 3.03
        hot = tag == "PLUS"
        box(s, x, 1.85, 2.85, 1.35, ACCENT if hot else SAND)
        fg = WHITE if hot else INK
        text(s, x + 0.25, 1.98, 2.5, 0.3, [(tag, 11, ACCENT_DIM if hot else GRAY, True)])
        text(s, x + 0.25, 2.28, 2.5, 0.5, [(price, 22, fg, True)])
        text(s, x + 0.25, 2.8, 2.5, 0.3, [(sub, 11, fg, False)])
    cols3 = [
        ("원가", "직접 원가 9,300원 / 대 · 월", ["엣지 박스 감가 1,500 · 클라우드 4,000", "메시지 1,000 · 원격 지원 2,300 · A/S 500", "총이익률 약 63% → 규모 확대 시 65~70%"]),
        ("고객 가치", "30실 펫호텔 = 월 84만 원", ["객실 30대 Plus + 공용 6대 Basic", "안심 옵션 추가 매출 월 약 176만 원 (가정)", "선택률 약 19%면 회수 — 보호자 5명 중 1명"]),
        ("시장 수준", "AI 분석이 가격을 만듭니다", ["사업장 CCTV 클라우드 녹화 월 1만 원 안팎", "AI 영상 분석 B2B 채널당 월 2~5만 원", "미국 펫호텔: 보호자 라이브는 이미 표준"]),
    ]
    for i, (k, h, items) in enumerate(cols3):
        x = MX + i * 4.05
        hline(s, x, 3.5, 3.8, INK, 0.02)
        text(s, x, 3.65, 3.8, 0.3, [(k, 11, ACCENT, True)])
        text(s, x, 3.95, 3.8, 0.45, [(h, 15, INK, True)])
        text(s, x, 4.5, 3.8, 1.6, [(f"·  {t}", 11.5, INK, False, 5) for t in items])
    box(s, MX, 5.9, CW, 0.75, ACCENT_WASH)
    text(s, MX + 0.3, 6.0, CW - 0.6, 0.6, [
        ("과금 규칙: 객실 = Plus · 공용 = Basic 혼합 · 같은 객실 두 번째 카메라 50% · 36개월 약정 기준(12개월 +10% · 무약정 +20%)", 11, INK, True, 2),
        ("초기 설치 · 온보딩 150만 원(엣지 박스 포함) + 카메라당 3만 원 · 시설당 최소 월 30만 원 · 첫 파일럿 2~3곳 6개월 50% 할인", 11, GRAY, False),
    ])

    # Deployment models
    page += 1
    s = new_slide(prs)
    frame(s, page, "DEPLOYMENT", "같은 소프트웨어, 세 가지 설치 형태")
    deps = [
        ("영종 직영", "관제실 서버", ["카메라 156대 (객실 116 · 공용 40)", "GPU 서버 2 · 앱/DB 1 · 녹화 약 160TB", "구축 약 1.66억 원 (1.12~2.44억)", "운영 월 약 425만 원 · 1박당 약 3,000원"], INK),
        ("외부 시설 · SaaS", "엣지 박스", ["GPU 소형 서버 약 350만 원 · 카메라 약 40대", "기존 카메라 · 녹화기 그대로 재사용", "구독료에 렌탈 포함 · 설치비로 일부 회수", "클라우드로 나가는 연결만 (방화벽 개방 없음)"], ACCENT),
        ("가정 · 홈서비스", "NPU 카메라", ["AI 칩 내장 — 카메라 안에서 검출", "기기 원가 약 4~14만 원 (등급별)", "클라우드는 알림 · 클립 · 앱만", "36개월 약정 시 기기 무료"], SAND),
    ]
    for i, (h, kind, items, c) in enumerate(deps):
        x = MX + i * 4.05
        box(s, x, 1.85, 3.8, 0.95, c)
        fg = INK if c == SAND else WHITE
        text(s, x + 0.3, 1.95, 3.3, 0.3, [(h, 11, GRAY if c == SAND else (ACCENT_DIM if c == ACCENT else NIGHT_GRAY), True)])
        text(s, x + 0.3, 2.25, 3.3, 0.45, [(kind, 19, fg, True)])
        for j, t in enumerate(items):
            yy = 3.0 + j * 0.58
            text(s, x, yy, 3.8, 0.45, [(t, 12, INK, False)])
            hline(s, x, yy + 0.47, 3.8)
    box(s, MX, 5.5, CW, 1.05, SAND)
    text(s, MX + 0.3, 5.62, CW - 0.6, 0.9, [
        ("공통", 12, ACCENT, True, 4),
        ("이벤트 엔진 규칙 · 클라우드 알림 · 보호자 앱(Flutter 한 코드로 Android 우선 · iOS · Web) · 관리자 웹(React)을 함께 씁니다.", 12, INK, False, 3),
        ("원본 영상은 현장 밖으로 나가지 않고, 보호자에게는 배정 객실 라이브와 승인된 리포트만 전달합니다.", 11, GRAY, False),
    ])

    # SaaS requirements
    page += 1
    s = new_slide(prs)
    frame(s, page, "SaaS", "다른 시설에 팔기 위해 갖출 제품 요건")
    reqs = [
        ("멀티테넌트 · 권한", "시설별 데이터 분리\n운영자·매니저·스태프·보호자 역할"), ("온보딩", "카메라 자동 검색(ONVIF)\n룸 매핑 마법사 · 설치 가이드"), ("배포", "클라우드 기본\n회선 약한 시설은 엣지 장비"),
        ("과금 · 계측", "카메라 · Stay 사용량 집계\n구독 결제 · 청구서"), ("보안 · 개인정보", "영상 열람 기록 · 보존 기간\n처리위탁 계약 양식"), ("운영 지원", "카메라 끊김 감지 · 원격 점검\n무중단 업데이트"),
    ]
    for i, (h, d) in enumerate(reqs):
        cx = MX + (i % 3) * 4.05
        cy = 1.95 + (i // 3) * 2.2
        hline(s, cx, cy, 3.75, INK, 0.02)
        text(s, cx, cy + 0.18, 3.7, 0.4, [(h, 16, INK, True)])
        text(s, cx, cy + 0.7, 3.7, 1.2, [(t, 13, GRAY, False, 4) for t in d.split("\n")])
    text(s, MX, 6.45, 11.9, 0.35, [("영종 운영 기간(S0)에는 단일 시설로 쓰고, 파일럿(S1)부터 멀티테넌트 구조로 전환합니다.", 11, GRAY, False)])

    # SaaS roadmap + GTM combined rows
    page += 1
    s = new_slide(prs)
    frame(s, page, "SaaS", "SaaS 로드맵과 영업 채널")
    phases = [("S0 · 영종 내부", "오픈~6개월", "전 객실 가동 · 원가 측정"), ("S1 · 파일럿", "6~12개월", "외부 2~3곳 · 멀티테넌트"), ("S2 · 정식 판매", "12개월~", "요금제 · 설치 파트너"), ("S3 · 채널 확장", "이후", "예약 연동 · 패키지 확장")]
    hline(s, MX, 2.35, CW, INK, 0.02)
    for i, (name, when, it) in enumerate(phases):
        x = MX + i * 3.05
        dot(s, x + 0.12, 2.36, 0.24, ACCENT if i == 0 else INK)
        text(s, x, 1.85, 2.8, 0.35, [(when, 12, ACCENT if i == 0 else GRAY, True)])
        text(s, x, 2.7, 2.85, 0.45, [(name, 15, INK, True)])
        text(s, x, 3.3, 2.85, 0.8, [(it, 12, GRAY, False)])
    cols = [("영업 채널", 2.4), ("방법", 5.6), ("준비물", 3.93)]
    rows = [
        ("직접 영업", "공항 권역 펫호텔 방문, 영종 견학 · 라이브 데모", "데모 계정 · 운영 사례"),
        ("설치 파트너", "CCTV 시공 업체 제휴, 설치 시 PET-Aeye 제안", "설치 가이드 · 수수료"),
        ("업계 행사 · 연동", "박람회 · 세미나, 예약 · 결제 플랫폼 연동", "소개서 · API 문서"),
    ]
    table(s, MX, 4.3, cols, rows, 0.6, body=12)
    text(s, MX, 6.5, 11.9, 0.3, [("가장 강한 영업 도구는 영종 현장입니다. 보호자 동의를 받은 화면만 사용합니다.", 10, GRAY, False)])

    # 하드웨어 제품화 · B2B
    page += 1
    s = new_slide(prs)
    frame(s, page, "HARDWARE × B2B", "바이탈 CCTV 제품화 — 리테일 데모 → 통신사 납품")
    hw_cols = [("구분", 2.6), ("기존 반려 CCTV", 4.35), ("PET-Aeye 바이탈 CCTV", 4.35)]
    hw_rows = [
        ("기능", "사람 · 펫 · 소리 감지 · 추적", "+ 비접촉 바이탈 (호흡 · 미동 · 재실)"),
        ("센서", "카메라", "카메라 + FMCW 레이더 (폼팩터 내장)"),
        ("판매 모델", "설치무료 · 구독 · 약정 (검증됨)", "동일 모델 + 프리미엄 상위 티어"),
    ]
    table(s, MX, 1.95, hw_cols, hw_rows, 0.5, body=11)
    text(s, MX, 4.1, 6, 0.3, [("제품화 3단계", 13, ACCENT, True)])
    steps = [
        ("1 · 리테일 데모 · DTC 구독", "별관 샵에서 실연 → 설치무료 · 구독 · 약정 자체 판매. 레퍼런스 · 바이탈 성능 데이터 · 후기 확보.", ACCENT_WASH),
        ("2 · 양산 · 인증", "EMS 양산 파트너 · KC/전파 인증 · 영상 보안(통신사 요구 수준) · 소규모 양산.", SAND),
        ("3 · B2B 납품", "통신사(LG U+ 등) 화이트라벨 · ODM 또는 AI SW 레이어 공급. 동물병원 · 펫샵 체인 병행.", SAND),
    ]
    for i, (h, b, c) in enumerate(steps):
        x = MX + i * 3.98
        box(s, x, 4.5, 3.8, 1.65, c)
        text(s, x + 0.25, 4.65, 3.35, 1.4, [(h, 12.5, INK, True, 5), (b, 11, INK, False)])
    text(s, MX, 6.4, CW, 0.6, [
        ("· 역할: 견주 앱 = 자체 개발 / AI · 바이탈 = PET-Aeye / 양산 = EMS 파트너.", 10, GRAY, False, 2),
        ("· '바이탈'은 웰니스 · 호흡 · 활동 모니터링으로 표기(비의료). 가정 영상 보안 · FMCW 성능 PoC 선행.", 10, GRAY, False),
    ])

    # 홈서비스 (B2C)
    page += 1
    s = new_slide(prs)
    frame(s, page, "HOME SERVICE", "홈서비스 — 호텔에서 집으로 이어지는 안심")
    cols = [("구분", 2.2), ("호텔 (B2B)", 4.85), ("홈 (B2C)", 4.88)]
    rows = [
        ("AI 분석 위치", "관제실 서버 · 엣지 박스", "카메라 내장 NPU (파일럿은 클라우드)"),
        ("알림 받는 사람", "스태프 확인 → 매니저 승인 → 보호자", "보호자가 바로 — 긴급만 즉시 · 나머지 하루 요약"),
        ("주요 이벤트", "장시간 무움직임 · 활동 · 이탈 · 장비", "분리불안 · 무움직임 · 밥 · 물 · 위험 구역 · 컨디션"),
        ("과금", "시설 · 카메라 단위 월 구독", "가구 단위 월 구독 · 36개월 약정 시 기기 무료"),
    ]
    table(s, MX, 1.8, cols, rows, 0.48, body=11)
    plans = [
        ("기본", "6,900원", "AI 알림 · 하루 요약 · 클립 30일 · 해킹 보상 보험", "총이익률 약 43~58% · 입구 상품", SAND),
        ("헬스 (주력)", "12,900원", "기본 + 컨디션 신호 · 주간 리포트 · 호텔 비교", "총이익률 약 58~66%", ACCENT),
        ("바이탈", "19,900원", "헬스 + 호흡 웰니스 · 수면 호흡 추세 (PoC 후)", "총이익률 약 65~70%", INK),
    ]
    for i, (name, price, inc, gm, c) in enumerate(plans):
        x = MX + i * 4.05
        box(s, x, 4.45, 3.8, 1.75, c)
        fg = INK if c == SAND else WHITE
        sub = GRAY if c == SAND else (ACCENT_DIM if c == ACCENT else NIGHT_GRAY)
        text(s, x + 0.25, 4.57, 3.3, 0.3, [(name, 11, sub, True)])
        text(s, x + 0.25, 4.85, 3.3, 0.45, [(f"월 {price}", 20, fg, True)])
        text(s, x + 0.25, 5.38, 3.35, 0.8, [(inc, 11, fg, False, 3), (gm, 10, sub, True)])
    text(s, MX, 6.4, CW, 0.5, [
        ("· 기본 플랜은 통신사 입문형 홈캠(월 5,500원) 근처에 두고 헬스 · 바이탈에서 수익을 냅니다. 핵심 지표: 기본 → 헬스 전환율.", 10, GRAY, False, 2),
        ("· 호텔에 묵었던 반려견의 기준값 · 졸업 리포트를 집에서 이어 봅니다. 컨디션 · 호흡은 웰니스 참고값(비의료).", 10, GRAY, False),
    ])

    # NPU 카메라 원가
    page += 1
    s = new_slide(prs)
    frame(s, page, "HOME SERVICE", "NPU 카메라 — 등급별 원가와 추진 순서")
    cols = [("등급", 1.9), ("AI 칩 (NPU)", 3.6), ("할 수 있는 일", 3.9), ("대당 원가", 2.53)]
    rows = [
        ("기본형", "0.5~1 TOPS급 (RV1106 · T41 계열)", "반려견 검출 · 활동 · 무움직임 · 짖음", "약 4~4.5만 원"),
        ("표준형 (추천)", "2~3 TOPS급 (RV1126B 계열)", "+ 자세 기반 행동 분석 · 여러 마리 추적", "약 7~7.7만 원"),
        ("바이탈형", "표준형 + FMCW 모듈", "+ 호흡 · 미동 웰니스", "약 10.5~14만 원"),
    ]
    table(s, MX, 1.8, cols, rows, 0.58, body=12)
    box(s, MX, 4.25, 5.85, 2.2, SAND)
    text(s, MX + 0.3, 4.4, 5.3, 2.0, [
        ("초기 비용 (1회)", 12, ACCENT, True, 6),
        ("ODM (기존 설계 + 자체 펌웨어 · AI) — 약 3,000~7,000만 원 · 6~9개월", 11.5, INK, False, 4),
        ("자체 설계 (디자인 · 금형 · 회로) — 약 2~4억 원 · 바이탈 일체형", 11.5, INK, False, 4),
        ("인증 (KC 전파 · 전자파 · IoT 보안인증) — 모델당 약 1,000~3,000만 원", 11.5, INK, False, 4),
        ("칩 원산지는 통신사 납품 보안 심사 조건을 먼저 확인", 10.5, GRAY, False),
    ])
    steps = [("H0 · 파일럿", "시판 카메라 + 클라우드 AI · 호텔 재방문 30~50가구"), ("H1 · 표준형 출시", "ODM 표준형 · NPU 모델 이식 · 인증 · 별관 리테일 데모"), ("H2 · 바이탈형 · 납품", "자체 설계 바이탈형 · 통신사 화이트라벨 / AI SW 공급")]
    for i, (h, d) in enumerate(steps):
        y = 4.25 + i * 0.75
        dot(s, 6.95, y + 0.17, 0.22, ACCENT if i == 0 else INK)
        text(s, 7.25, y, 5.4, 0.7, [(h, 13, INK, True, 2), (d, 11, GRAY, False)])
    text(s, MX, 6.6, CW, 0.3, [("* 원가 = 부품 + 조립 · 물류 · 관세 · 불량(약 15%) · 1,000~3,000대 기준 · 환율 1,400원/달러 · 가정치(ODM 견적으로 확정). 바이탈 모듈은 자체 원가 미정.", 10, GRAY, False)])

    # 시장 · 경쟁
    page += 1
    s = new_slide(prs)
    frame(s, page, "COMPETITION", "비슷한 제품은 있지만, 반려견용 '카메라 + 비접촉 바이탈'은 아직 없습니다")
    cols = [("구분", 2.1), ("제품", 3.3), ("내용", 4.53), ("바이탈", 2.0)]
    rows = [
        ("국내 AI 펫캠", "킨포라 (림피드 · 2026.07)", "21가지 행동 인식 · 5대 건강 신호 · 영양 연결", "없음"),
        ("국내 통신사", "LG유플러스 홈캠 Lite (2026.09)", "감지 · 클라우드 · 해킹 보상 보험 · 월 5,500원", "없음"),
        ("해외 펫캠", "Furbo · Tapo · Petcube", "AI 행동 알림 · 하루 요약 · 월 약 $4~10", "없음"),
        ("아기 모니터", "Momcozy BM08 · 맘아이(국내)", "카메라 + mmWave · 60GHz 레이더", "호흡 (아기용)"),
        ("반려 바이탈 기기", "Invoxia · REx Sense · ITRI", "목걸이 · 센서 · 방석 (카메라 아님)", "호흡 · 심박"),
        ("펫호텔 B2B (미국)", "CareCam · Animal Friends OS", "Stay 기간 보호자 라이브 · 예약 연동", "없음"),
    ]
    table(s, MX, 1.8, cols, rows, 0.52, body=11)
    box(s, MX, 5.5, CW, 1.2, ACCENT_WASH)
    text(s, MX + 0.3, 5.62, CW - 0.6, 1.0, [
        ("시사점", 12, ACCENT, True, 4),
        ("'카메라 + 레이더'는 아기용으로 이미 있습니다. 반려견 전용 알고리즘(털 · 체격 · 품종) · 호텔 데이터 · B2B + 홈 구조로 차별화합니다.", 11.5, INK, False, 3),
        ("기본 기능 가격은 통신사가 정했고(월 5,500원), 행동 건강 신호는 킨포라가 먼저 나왔습니다 → 헬스 · 바이탈 · 호텔 연계로 위치를 잡고 출시 속도를 높입니다.", 11, GRAY, False),
    ])

    # 확장 레이어 (Growth layers)
    page += 1
    s = new_slide(prs)
    frame(s, page, "GROWTH LAYERS", "코어 위에 올리는 3개 성장 레이어")
    stack = [
        ("③ 프랜차이즈 · 위탁운영", SAND, INK),
        ("② 헬스데이터 · 인슈어테크", ACCENT_DIM, INK),
        ("① 멤버십 · 구독 OS", ACCENT, WHITE),
        ("코어 · 영종 캠퍼스 × PET-Aeye", INK, WHITE),
    ]
    for i, (lab, fill, fg) in enumerate(stack):
        y = 2.1 + i * 1.1
        box(s, MX, y, 5.5, 0.95, fill)
        text(s, MX, y + 0.26, 5.5, 0.5, [(lab, 15, fg, True)], PP_ALIGN.CENTER)
    desc = [
        ("① 멤버십 · 구독 OS", "전 사업을 월 구독 · 지갑 · 포인트로 통합 → LTV↑ · CAC↓.", "자체 앱 + PET-Aeye 데이터 · 수익: 구독 ARPU · 교차판매 · 선결제"),
        ("② 헬스데이터 · 인슈어테크", "바이탈 · 행동 데이터로 펫보험 제휴 · 건강 구독.", "동물병원 임상 접점 · 수익: 제휴 수수료 · 데이터 · 건강 구독"),
        ("③ 프랜차이즈 · 위탁운영", "브랜드 + SOP + PET-Aeye 패키지로 캠퍼스 복제(자본 효율).", "수익: 가맹비 · 로열티 · SaaS · 물류"),
    ]
    for i, (h, b, c) in enumerate(desc):
        y = 2.2 + i * 1.35
        text(s, 6.9, y, 5.7, 1.2, [(h, 15, ACCENT, True, 4), (b, 12.5, INK, False, 3), (c, 11, GRAY, False)])
    text(s, MX, 6.55, CW, 0.3, [("* 멤버십이 데이터 레이어의 스파인입니다. 확장 레이어는 로드맵 항목으로 연매출엔 미반영.", 10, GRAY, False)])

    # 확장 로드맵 (Growth roadmap)
    page += 1
    s = new_slide(prs)
    frame(s, page, "GROWTH ROADMAP", "코어 검증 → 레이어를 순차로 켭니다")
    gphases = [
        ("개업~", "① 멤버십 · 구독 OS", "구독 · 지갑 · 포인트로 전 사업 통합 · 현금흐름 확보"),
        ("안정기~", "② 헬스데이터 · 인슈어테크", "건강 스코어 · 펫보험 제휴 파일럿 (동물병원 접점)"),
        ("레퍼런스 후", "③ 프랜차이즈 · 위탁운영", "표준 패키지(브랜드 · SOP · PET-Aeye)로 2호점 · MC"),
        ("확장", "데이터 moat 본격화", "데이터 · SaaS · 인슈어테크 수익 비중 확대"),
    ]
    hline(s, MX, 2.6, CW, INK, 0.02)
    for i, (when, name, it) in enumerate(gphases):
        x = MX + i * 3.05
        dot(s, x + 0.12, 2.61, 0.24, ACCENT if i == 0 else INK)
        text(s, x, 2.05, 2.9, 0.35, [(when, 12, ACCENT if i == 0 else GRAY, True)])
        text(s, x, 2.95, 2.9, 0.5, [(name, 15, INK, True)])
        text(s, x, 3.6, 2.9, 1.1, [(it, 12, GRAY, False)])
    box(s, MX, 5.1, CW, 1.2, SAND)
    text(s, MX + 0.35, 5.35, CW - 0.7, 0.8, [
        ("순서 원칙", 13, ACCENT, True, 5),
        ("멤버십으로 데이터 · 현금흐름을 모으고 → 데이터로 보험 · 헬스를 수익화하고 → 검증된 모델을 복제합니다.", 14, INK, False),
    ])
    text(s, MX, 6.55, CW, 0.3, [("* 확장 레이어는 로드맵 항목입니다. 연매출(기준 약 24억)에는 아직 반영하지 않았습니다.", 10, GRAY, False)])

    # Ask (IR)
    page += 1
    s = new_slide(prs)
    frame(s, page, "THE ASK", "투자금은 오픈과 '보이는 안심' 가동에 씁니다")
    box(s, MX, 1.95, 5.2, 4.5, INK)
    text(s, MX + 0.4, 2.25, 4.5, 0.3, [("라운드 · 금액 · 지분", 12, NIGHT_GRAY, True)])
    text(s, MX + 0.4, 2.7, 4.5, 0.9, [("TBD", 54, ACCENT, True)])
    text(s, MX + 0.4, 3.85, 4.5, 2.4, [
        ("자금 용도(안)", 12, NIGHT_GRAY, True, 8),
        ("오픈 준비 · 초기 인력", 14, WHITE, False, 6),
        (f"{total_rooms}실 카메라 · PET-Aeye 설치 (약 1.7억)", 14, WHITE, False, 6),
        ("공항 샌딩 차량 · 사전 마케팅", 14, WHITE, False, 6),
        ("운전자본 · 예비비", 14, WHITE, False, 6),
    ])
    text(s, 6.4, 1.95, 6.2, 0.35, [("투자 후 90일 안에 보여드릴 것", 13, ACCENT, True)])
    proofs = [("그랜드 오픈 · 영업 개시", "위탁관리업 등록 완료 상태"), ("PET-Aeye 전 객실 가동", f"{total_rooms}실 × 카메라 연결"), ("공항 안심 보딩 첫 판매", "샌딩 포함 패키지"), ("PET-Aeye 안심 옵션 판매 개시", "유료 선택률 첫 측정")]
    for i, (h, b) in enumerate(proofs):
        y = 2.5 + i * 0.95
        text(s, 6.4, y, 0.6, 0.6, [(f"{i + 1}", 26, ACCENT, True)])
        text(s, 7.1, y + 0.05, 5.5, 0.8, [(h, 16, INK, True, 2), (b, 12, GRAY, False)])
        hline(s, 6.4, y + 0.82, 6.2)

    # ========================= PART 6 · 관리 =========================
    page += 1
    section_divider(prs, "PART 6 · 관리", "지표로 보고, 단계로 넘어갑니다",
                    ["호텔 · PET-Aeye · SaaS별 핵심 지표",
                     "가설이 틀릴 수 있는 지점과 확인 방법",
                     "오픈 준비 워크스트림과 단계별 게이트"])

    # KPI
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 6 · 관리", "핵심 지표")
    kpis = [("HOTEL", "호텔 운영", ["타입별 가동률", "평균 객단가", "재이용률", "공항 유입 비중", "부가 매출 비중"]), ("PET-Aeye", "호텔 안 PET-Aeye", ["보호자 링크 열람률", "리포트 열람률", "안심 서비스 선택률", "알림 정확도 (오탐률)", "이벤트 대응 시간"]), ("SaaS", "SaaS 사업", ["활성 시설 수", "연결 카메라 수", "월 반복 매출 (MRR)", "이탈률", "온보딩 소요일"])]
    for i, (tag, name, items) in enumerate(kpis):
        x = MX + i * 4.05
        hline(s, x, 2.0, 3.75, ACCENT if i == 1 else INK, 0.03)
        text(s, x, 2.2, 3.7, 0.3, [(tag, 11, ACCENT, True)])
        text(s, x, 2.55, 3.7, 0.5, [(name, 20, INK, True)])
        for j, t in enumerate(items):
            yy = 3.35 + j * 0.56
            text(s, x, yy, 3.7, 0.4, [(t, 13, INK, False)])
            hline(s, x, yy + 0.45, 3.75)
    text(s, MX, 6.45, 11.9, 0.35, [("목표값은 D+30 첫 리뷰에서 실제 데이터를 보고 정합니다.", 11, GRAY, False)])

    # Risks
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 6 · 관리", "리스크와 대응")
    cols = [("리스크", 3.9), ("영향", 2.4), ("대응", 5.63)]
    rows = [
        (f"{total_rooms}실 초기 가동률 저조", "고정비 부담", "3F 중대형 · 공항 패키지 우선 판매, 층별 단계 운영"),
        ("알림 오탐 · 과알림", "스태프 피로 · 신뢰 하락", "검증된 규칙만 사용, 스태프 확인 후 공유"),
        ("영상 개인정보 문제", "민원 · 법적 리스크", "고지 · 동의, 배정 룸만 열람, 열람 기록 · 보존 기간"),
        ("네트워크 · 카메라 장애", "관제 공백", "끊김 알림, 대체 순찰 SOP, 현장 녹화"),
        ("라이다 바이탈 정확도 · 성숙도", "상품화 지연", "단계적 PoC로 검증, 웰니스 지표로 한정"),
        ("호텔 운영과 SaaS 자원 충돌", "둘 다 지연", "S0에는 호텔 운영 우선, SaaS 기능은 S1부터"),
    ]
    table(s, MX, 1.9, cols, rows, 0.72, body=13)

    # Decisions
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 6 · 관리", "결정이 필요한 사항")
    cols = [("항목", 2.9), ("선택지", 7.0), ("결정 시점", 2.03)]
    rows = [
        ("안심 서비스 요금", "전 객실 기본 포함  /  1박당 부가  /  대형 · 패밀리만 포함", "D-45"),
        ("보호자 화면", "Flutter 한 코드로 링크형 웹 + 앱 (Android 우선)", "결정 ✓"),
        ("라이브 범위", "상시 라이브  /  정해진 시간 · 하이라이트 위주", "D-45"),
        ("영상 보존 기간", "7일  /  30일  /  Stay 종료 후 일정 기간", "D-45"),
        ("라이다 바이탈 PoC", "센서 공급 · 실증 객실 범위", "S0 중"),
        ("SaaS 브랜드", "PET-Aeye 단독  /  파우코리아 공동 표기", "S1 전"),
    ]
    table(s, MX, 1.9, cols, rows, 0.72, body=13)

    # Open prep roadmap
    page += 1
    s = new_slide(prs)
    frame(s, page, "PART 6 · 관리", "오픈 준비 — 단계마다 확인하고 넘어갑니다")
    phases = [
        ("지금", "Phase 0 · 오픈 준비", ["위탁관리업 등록 완료 ✓", "인력 채용 · 운영 매뉴얼", f"{total_rooms}실 카메라 · PET-Aeye 설치"], "확인  전 객실 관제 연결"),
        ("~90일", "Phase 1 · 오픈", ["D-30 사전 마케팅 · 제휴", "그랜드 오픈", "공항 안심 보딩 출시"], "확인  첫 안심 Stay"),
        ("~6개월", "Phase 2 · 정착", ["안심 옵션 요금화", "예약 → Stay 연동", "생활권 멤버십"], "확인  가동률 · 재이용"),
        ("12개월+", "Phase 3 · 확장", ["PET-Aeye 외부 판매", "라이다 바이탈 PoC", "2차 개발 여부 판단"], "확인  외부 고객 1곳"),
    ]
    hline(s, MX, 2.35, CW, INK, 0.02)
    for i, (when, name, items, gate) in enumerate(phases):
        x = MX + i * 3.05
        dot(s, x + 0.12, 2.36, 0.24, ACCENT if i <= 1 else INK)
        text(s, x, 1.85, 2.8, 0.35, [(when, 13, ACCENT if i <= 1 else GRAY, True)])
        text(s, x, 2.7, 2.85, 0.45, [(name, 15, INK, True)])
        text(s, x, 3.3, 2.85, 1.8, [(f"·  {t}", 13, INK, False, 6) for t in items])
        box(s, x, 5.3, 2.8, 0.55, SAND)
        text(s, x + 0.18, 5.3, 2.6, 0.55, [(gate, 11, INK, True)], anchor=MSO_ANCHOR.MIDDLE)
    text(s, MX, 6.15, 11.9, 0.5, [("사전 마케팅 제휴 후보: 여행사 · 카드사 · 숙박 앱 · 국내 호텔 · 반려견 훈련기관 · 관련 학과 · 지자체", 11, GRAY, False)])

    # Appendix references
    page += 1
    s = new_slide(prs)
    frame(s, page, "APPENDIX", "참고 자료")
    left = [
        ("시설", 13, ACCENT, True, 6),
        ("원 사업계획서(구칭 리조이스 · PETEL 영종) — 객실 구성 · 평면 · 2차 계획 · 마케팅", 12, INK, False, 14),
        ("입지 · 채널", 13, ACCENT, True, 6),
        ("인천국제공항공사 보도자료 2024.3 · 2024.11 (호텔링 · 펫라운지)", 12, INK, False, 4),
        ("인천공항 영문 안내 — 호텔링 약 13kg 이하", 12, INK, False, 4),
        ("인스파이어 리조트 이용약관 · FAQ — 반려동물 입실 불가", 12, INK, False, 14),
        ("기술", 13, ACCENT, True, 6),
        ("FMCW 라이다 반도체 — 비접촉 바이탈 센싱(기반 기술 확보)", 12, INK, False, 14),
        ("경쟁 조사 (2026.10)", 13, ACCENT, True, 6),
        ("킨포라 · LG유플러스 홈캠 Lite · Furbo · Momcozy · 맘아이 · Invoxia", 12, INK, False, 4),
    ]
    right = [
        ("시장 · 수요", 13, ACCENT, True, 6),
        ("KB금융지주 경영연구소 — 펫테크 기기 사용 이유", 12, INK, False, 4),
        ("Grand View Horizon — South Korea Pet Boarding Services", 12, INK, False, 4),
        ("독독 공개 요금(5.5~11만 원/박), 더우프앤·앤드 공개 정보", 12, INK, False, 14),
        ("내부 문서", 13, ACCENT, True, 6),
        ("프로젝트_범위_확장_초안.md — 전체 사업 범위(펫장례 포함)", 12, INK, False, 4),
        ("peti-mvp — PET-Aeye 구현 코드 레포", 12, INK, False, 4),
        ("CCTV · 서버 비용 · 관제 SW 구성 · 구독 요금 · 홈서비스 기획 (doc/*.md)", 12, INK, False, 14),
        ("요금 · 체중 기준 · 일정은 가정이며, 현장 실측과 운영 데이터로 갱신합니다. 바이탈은 PoC·로드맵 항목입니다.", 10, GRAY, False),
    ]
    text(s, MX, 2.0, 5.8, 4.6, left)
    text(s, 6.9, 2.0, 5.8, 4.6, right)

    prs.save(OUT)
    print(f"saved: {OUT}  slides={len(prs.slides)}  rooms={total_rooms}  adr={adr:,.0f}  revenues={[round(r, 1) for r in revenues]}")


if __name__ == "__main__":
    build()
