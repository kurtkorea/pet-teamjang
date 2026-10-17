# -*- coding: utf-8 -*-
"""BAEUNG Pet Funeral IR Deck — investor-grade rebuild."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

# ── Palette (cool slate + deep teal; memorial / premium, not AI defaults)
SLATE = RGBColor(0x0F, 0x17, 0x2A)
INK = RGBColor(0x1E, 0x29, 0x3B)
MUTED = RGBColor(0x64, 0x74, 0x8B)
TEAL = RGBColor(0x0F, 0x76, 0x6E)
TEAL_SOFT = RGBColor(0xCC, 0xFB, 0xF1)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BG = RGBColor(0xF8, 0xFA, 0xFC)
CARD = RGBColor(0xFF, 0xFF, 0xFF)
LINE = RGBColor(0xE2, 0xE8, 0xF0)
SOFT = RGBColor(0xF1, 0xF5, 0xF9)
AMBER = RGBColor(0xB4, 0x53, 0x09)

W = Inches(13.333)
H = Inches(7.5)
ML = Inches(0.65)  # margin left
FONT = "Malgun Gothic"
TOTAL = 16


def _ea(run, font=FONT):
    run.font.name = font
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = etree.SubElement(rPr, qn("a:ea"))
    ea.set("typeface", font)
    latin = rPr.find(qn("a:latin"))
    if latin is None:
        latin = etree.SubElement(rPr, qn("a:latin"))
    latin.set("typeface", font)


def run_style(run, size=14, bold=False, color=INK):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    _ea(run)


def rect(slide, l, t, w, h, fill, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
    return sh


def round_rect(slide, l, t, w, h, fill, line=LINE):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line:
        sh.line.color.rgb = line
    else:
        sh.line.fill.background()
    try:
        sh.adjustments[0] = 0.08
    except Exception:
        pass
    return sh


def send_back(slide, shape):
    spTree = slide.shapes._spTree
    sp = shape._element
    spTree.remove(sp)
    spTree.insert(2, sp)


def tb(slide, l, t, w, h):
    box = slide.shapes.add_textbox(l, t, w, h)
    box.text_frame.word_wrap = True
    return box


def put(box_or_tf, text, size=14, bold=False, color=INK, align=PP_ALIGN.LEFT, space_after=6, clear=False):
    tf = box_or_tf if hasattr(box_or_tf, "paragraphs") else box_or_tf.text_frame
    if clear:
        tf.clear()
        p = tf.paragraphs[0]
    else:
        if tf.paragraphs[0].text == "" and len(tf.paragraphs) == 1 and not tf.paragraphs[0].runs:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space_after)
    r = p.add_run()
    r.text = text
    run_style(r, size, bold, color)
    return p


def lines(slide, l, t, w, h, items, size=14, color=INK, bold_first=False, gap=8):
    box = tb(slide, l, t, w, h)
    tf = box.text_frame
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        r = p.add_run()
        r.text = item
        run_style(r, size, bold_first and i == 0, color)
    return box


def blank(prs, dark=False):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = rect(s, 0, 0, W, H, SLATE if dark else BG)
    send_back(s, bg)
    return s


def chrome(slide, page, section=""):
    """Left accent + top rule + footer."""
    rect(slide, 0, 0, Inches(0.08), H, TEAL)
    rect(slide, ML, Inches(7.05), Inches(12.0), Inches(0.01), LINE)
    foot = tb(slide, ML, Inches(7.12), Inches(10), Inches(0.28))
    put(foot, f"BAEUNG  ·  Pet Funeral IR  ·  Confidential", 9, False, MUTED, clear=True)
    num = tb(slide, Inches(11.6), Inches(7.12), Inches(1.2), Inches(0.28))
    put(num, f"{page:02d} / {TOTAL:02d}", 9, False, MUTED, PP_ALIGN.RIGHT, clear=True)


def header(slide, eyebrow, title, subtitle=None):
    eb = tb(slide, ML, Inches(0.32), Inches(12), Inches(0.28))
    put(eb, eyebrow.upper(), 11, True, TEAL, clear=True)
    ti = tb(slide, ML, Inches(0.58), Inches(12), Inches(0.5))
    put(ti, title, 26, True, SLATE, clear=True)
    y = Inches(1.15)
    if subtitle:
        su = tb(slide, ML, Inches(1.05), Inches(12), Inches(0.35))
        put(su, subtitle, 13, False, MUTED, clear=True)
        y = Inches(1.45)
    return y


def kpi(slide, l, t, w, h, value, label, note=None):
    round_rect(slide, l, t, w, h, CARD, LINE)
    rect(slide, l, t, Inches(0.07), h, TEAL)
    v = tb(slide, l + Inches(0.25), t + Inches(0.28), w - Inches(0.4), Inches(0.55))
    put(v, value, 28, True, SLATE, clear=True)
    la = tb(slide, l + Inches(0.25), t + Inches(0.85), w - Inches(0.4), Inches(0.45))
    put(la, label, 12, False, MUTED, clear=True)
    if note:
        n = tb(slide, l + Inches(0.25), t + Inches(1.25), w - Inches(0.4), Inches(0.4))
        put(n, note, 11, False, INK, clear=True)


def card(slide, l, t, w, h, title, body, accent=True):
    round_rect(slide, l, t, w, h, CARD, LINE)
    if accent:
        rect(slide, l, t, w, Inches(0.06), TEAL)
    ti = tb(slide, l + Inches(0.22), t + Inches(0.22), w - Inches(0.4), Inches(0.35))
    put(ti, title, 14, True, SLATE, clear=True)
    if isinstance(body, str):
        body = [body]
    lines(slide, l + Inches(0.22), t + Inches(0.6), w - Inches(0.4), h - Inches(0.75), body, 12, INK, gap=5)


def build():
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H
    p = 0

    # ════════════════════════════════════════
    # 01 COVER
    # ════════════════════════════════════════
    p += 1
    s = blank(prs, dark=True)
    rect(s, 0, 0, Inches(0.18), H, TEAL)
    # soft panel
    rect(s, Inches(8.8), 0, Inches(4.533), H, RGBColor(0x13, 0x1F, 0x35))
    lines(s, Inches(0.85), Inches(1.6), Inches(7.5), Inches(0.35), ["PET FUNERAL  ·  INVESTOR DECK"], 12, TEAL)
    lines(s, Inches(0.85), Inches(2.15), Inches(7.5), Inches(0.9), ["배웅"], 54, WHITE, True)
    lines(s, Inches(0.85), Inches(3.0), Inches(7.5), Inches(0.4), ["BAEUNG"], 20, TEAL_SOFT)
    rect(s, Inches(0.85), Inches(3.55), Inches(1.4), Inches(0.05), TEAL)
    lines(
        s,
        Inches(0.85),
        Inches(3.85),
        Inches(7.2),
        Inches(1.2),
        [
            "인천·경기 서부 합법 펫장례 허브",
            "찾아가는 의전  ×  디지털 메모리얼",
        ],
        18,
        RGBColor(0xCB, 0xD5, 0xE1),
        gap=10,
    )
    lines(
        s,
        Inches(0.85),
        Inches(6.4),
        Inches(7.2),
        Inches(0.5),
        ["Summit Farewell Park  ·  을왕동  ·  v0.3 · 장묘업 인가 확인"],
        11,
        MUTED,
    )
    # right rail facts
    lines(s, Inches(9.15), Inches(1.8), Inches(3.8), Inches(0.3), ["AT A GLANCE"], 11, TEAL, True)
    facts = [
        ("인가 完", "동물장묘업 인가 확인"),
        ("~734억", "코어 장묘 시장(기본)"),
        ("10~15억", "배웅 기본 매출 밴드"),
        ("500+", "고팀장 의전 인력"),
    ]
    for i, (v, lab) in enumerate(facts):
        top = Inches(2.3) + i * Inches(1.05)
        lines(s, Inches(9.15), top, Inches(3.8), Inches(0.4), [v], 22, WHITE, True)
        lines(s, Inches(9.15), top + Inches(0.4), Inches(3.8), Inches(0.3), [lab], 12, MUTED)

    # ════════════════════════════════════════
    # 02 AGENDA
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "01  Agenda", "오늘 이야기할 것", "펫장례(배웅) 중심 · 호텔은 업사이드로만")
    agenda = [
        ("01", "기회", "수요 전환과 합법 공급 공백"),
        ("02", "해법", "허브 × 의전망 × 메모리얼"),
        ("03", "시장·숫자", "Bottom-up 밴드와 상권 매출"),
        ("04", "실행", "제품 · GTM · 경쟁 · 로드맵"),
        ("05", "실행·리스크", "인가 확보 이후 잔여 실사와 Ask"),
    ]
    for i, (n, t, d) in enumerate(agenda):
        top = Inches(1.55) + i * Inches(0.95)
        round_rect(s, ML, top, Inches(12.0), Inches(0.82), CARD, LINE)
        rect(s, ML, top, Inches(0.08), Inches(0.82), TEAL)
        lines(s, ML + Inches(0.35), top + Inches(0.2), Inches(0.8), Inches(0.4), [n], 18, TEAL, True)
        lines(s, ML + Inches(1.3), top + Inches(0.18), Inches(2.5), Inches(0.45), [t], 18, SLATE, True)
        lines(s, ML + Inches(4.0), top + Inches(0.22), Inches(7.5), Inches(0.45), [d], 14, MUTED)

    # ════════════════════════════════════════
    # 03 ONE-LINER / VISION
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "02  Vision", "한 줄로 정의하면")
    # quote panel
    round_rect(s, ML, Inches(1.4), Inches(12.0), Inches(1.7), SLATE, None)
    lines(
        s,
        ML + Inches(0.45),
        Inches(1.75),
        Inches(11.2),
        Inches(1.1),
        ["이별의 순간을 합법·투명하게 받고,", "기억을 일상 추모로 이어 주는 펫장례 허브."],
        22,
        WHITE,
        gap=8,
    )
    layers = [
        ("허브", "을왕 합법 화장·추모\n봉안·자연장·스톤"),
        ("의전", "병원·자택 픽업\n인증 지도사 배차"),
        ("신뢰", "허가·개별화장\n기본/선택 가격 공개"),
        ("락인", "웹 접수 →\n앱 메모리얼"),
    ]
    for i, (t, b) in enumerate(layers):
        card(s, ML + i * Inches(3.1), Inches(3.5), Inches(2.95), Inches(2.7), t, b.split("\n"))

    # ════════════════════════════════════════
    # 04 PROBLEM
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "03  Problem", "수요는 커지고, 합법 공급은 따라가지 못한다")
    probs = [
        ("의례화", "직접 매장\n58.7% → 31~36%", "개별 화장·스톤·자택 보관이 표준으로 이동"),
        ("인프라", "허가 업체\n전국 80~90곳", "서울·인천 서부 공백 → 원정 장례 고착"),
        ("신뢰", "무허가·불투명\n처리 vs 장례 혼동", "보호자는 허가·개별화장·가격을 요구"),
        ("접근", "검색광고 고단가\n시설만으로 한계", "실제 유입은 동물병원 추천이 핵심"),
    ]
    for i, (t, big, note) in enumerate(probs):
        left = ML + (i % 2) * Inches(6.2)
        top = Inches(1.5) + (i // 2) * Inches(2.55)
        round_rect(s, left, top, Inches(5.95), Inches(2.35), CARD, LINE)
        rect(s, left, top, Inches(0.08), Inches(2.35), TEAL)
        lines(s, left + Inches(0.3), top + Inches(0.25), Inches(5.3), Inches(0.35), [t], 13, TEAL, True)
        lines(s, left + Inches(0.3), top + Inches(0.65), Inches(5.3), Inches(0.9), big.split("\n"), 20, SLATE, True, gap=4)
        lines(s, left + Inches(0.3), top + Inches(1.7), Inches(5.3), Inches(0.45), [note], 12, MUTED)

    # ════════════════════════════════════════
    # 05 WHY NOW
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "04  Why Now", "규제와 자본이 합법 사업자에게 유리해지는 구간")
    kpi(s, ML, Inches(1.55), Inches(3.9), Inches(2.0), "591만", "반려가구", "전체 가구의 ~26.7%")
    kpi(s, ML + Inches(4.15), Inches(1.55), Inches(3.9), Inches(2.0), "1,500만", "반려인 규모", "인구의 약 30%")
    kpi(s, ML + Inches(8.3), Inches(1.55), Inches(3.9), Inches(2.0), "2023→", "장묘 허가제", "진입장벽↑ · 신뢰 프리미엄")
    cards = [
        ("정책", "가격게시제(2028)·자연장·도심 장례식장 완화 논의\n→ 투명·표준 사업자 유리"),
        ("자본", "상조·통신·라이프케어의 펫상조 진출\n→ 시설·직접 접수가 협상력"),
        ("문화", "평균 장례비 ~46만, 계획 지출 ~67만\n→ 패키지·추모 업셀 여력"),
    ]
    for i, (t, b) in enumerate(cards):
        card(s, ML + i * Inches(4.15), Inches(4.0), Inches(3.95), Inches(2.35), t, b.split("\n"))

    # ════════════════════════════════════════
    # 06 SOLUTION FLOW
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "05  Solution", "배웅 = 지역 허브 + 의전망 + 메모리얼")
    steps = [
        ("1", "유입", "병원 · 자택\n방문 · 상조"),
        ("2", "현장", "인증 의전 배차\n픽업 · 염습"),
        ("3", "허브", "개별 화장·추모\n봉안 · 스톤"),
        ("4", "사후", "웹 추모관\n앱 기일·앨범"),
    ]
    for i, (n, t, b) in enumerate(steps):
        left = ML + i * Inches(3.1)
        round_rect(s, left, Inches(1.55), Inches(2.9), Inches(2.55), CARD, LINE)
        circ = s.shapes.add_shape(MSO_SHAPE.OVAL, left + Inches(1.1), Inches(1.75), Inches(0.55), Inches(0.55))
        circ.fill.solid()
        circ.fill.fore_color.rgb = TEAL
        circ.line.fill.background()
        nt = tb(s, left + Inches(1.1), Inches(1.82), Inches(0.55), Inches(0.45))
        put(nt, n, 16, True, WHITE, PP_ALIGN.CENTER, clear=True)
        lines(s, left + Inches(0.2), Inches(2.45), Inches(2.5), Inches(0.35), [t], 16, SLATE, True)
        lines(s, left + Inches(0.2), Inches(2.9), Inches(2.5), Inches(0.9), b.split("\n"), 13, MUTED, gap=4)
        if i < 3:
            ar = tb(s, left + Inches(2.75), Inches(2.5), Inches(0.4), Inches(0.4))
            put(ar, "›", 22, True, TEAL, clear=True)

    takeaways = [
        ("인가", "동물장묘업 인가 확인 — 합법 본영업 가능"),
        ("인력", "고팀장 500명+ → 펫 인증 온콜 (공급 해자)"),
        ("제품", "응급은 웹 / 추모 습관은 앱"),
        ("구조", "상조는 선택 제휴 · 병원·자체 접수 병행"),
    ]
    for i, (t, b) in enumerate(takeaways):
        top = Inches(4.45) + (i // 2) * Inches(1.1)
        left = ML + (i % 2) * Inches(6.2)
        round_rect(s, left, top, Inches(5.95), Inches(0.95), SOFT, LINE)
        lines(s, left + Inches(0.25), top + Inches(0.15), Inches(1.4), Inches(0.6), [t], 14, TEAL, True)
        lines(s, left + Inches(1.8), top + Inches(0.28), Inches(3.9), Inches(0.5), [b], 13, INK)

    # ════════════════════════════════════════
    # 07 MARKET
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "06  Market", "광의 보도가 아니라, 검증 가능한 코어로 본다")
    # three columns
    cols = [
        ("광의 (참고)", "1,600~\n1,720억", "상조·부가 포함 가능\n매체별 정의 상이"),
        ("코어 기본 ★", "약 734억", "연 14.7만 건 × ASP 50만\n의사결정용 중심 밴드"),
        ("코어 낙관", "약 1,335억", "이용률·ASP 상승 시\n전국 상한에 근접"),
    ]
    for i, (t, v, n) in enumerate(cols):
        left = ML + i * Inches(4.15)
        round_rect(s, left, Inches(1.5), Inches(3.95), Inches(3.6), CARD if i != 1 else SLATE, LINE if i != 1 else None)
        tc = TEAL if i != 1 else TEAL_SOFT
        vc = SLATE if i != 1 else WHITE
        nc = MUTED if i != 1 else RGBColor(0x94, 0xA3, 0xB8)
        lines(s, left + Inches(0.3), Inches(1.75), Inches(3.4), Inches(0.35), [t], 13, tc, True)
        lines(s, left + Inches(0.3), Inches(2.3), Inches(3.4), Inches(1.1), v.split("\n"), 28, vc, True, gap=2)
        lines(s, left + Inches(0.3), Inches(3.7), Inches(3.4), Inches(1.1), n.split("\n"), 13, nc, gap=6)
    lines(
        s,
        ML,
        Inches(5.4),
        Inches(12),
        Inches(1.2),
        [
            "공식 단일 통계 없음  →  사망 마리(견묘÷수명) × 장묘 이용률 × ASP 로 Bottom-up 검증",
            "수도권 기본 ~7.6만 건 · ~0.38조  |  실제 평균 지출 ~46만 · 계획 ~67만 · 모델 ASP 50만",
        ],
        13,
        MUTED,
        gap=8,
    )

    # ════════════════════════════════════════
    # 08 BEACHHEAD REVENUE
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "07  Beachhead", "배웅이 먹는 시장 — 인천·경기 서부")
    # left market
    round_rect(s, ML, Inches(1.5), Inches(5.5), Inches(5.0), CARD, LINE)
    lines(s, ML + Inches(0.35), Inches(1.75), Inches(4.9), Inches(0.35), ["L2 상권 (주력)"], 14, TEAL, True)
    lines(s, ML + Inches(0.35), Inches(2.25), Inches(4.9), Inches(0.5), ["인천 + 경기 서부"], 22, SLATE, True)
    metrics = [
        ("잠재 장묘 건수", "약 17,400건 /년"),
        ("상권 규모", "약 87억 (ASP 50만)"),
        ("인천만 (L1)", "약 8,700건 /년"),
        ("서울 유입", "원정 수요 민감도 가산"),
    ]
    for i, (a, b) in enumerate(metrics):
        top = Inches(3.0) + i * Inches(0.7)
        lines(s, ML + Inches(0.35), top, Inches(2.3), Inches(0.4), [a], 13, MUTED)
        lines(s, ML + Inches(2.6), top, Inches(2.6), Inches(0.4), [b], 14, SLATE, True)

    # right scenarios
    lines(s, Inches(6.5), Inches(1.5), Inches(6.2), Inches(0.35), ["배웅 코어 매출 밴드"], 14, TEAL, True)
    scenarios = [
        ("보수", "5~8억", "점유 저조", False),
        ("기본", "10~15억", "L2 10~15% + 서울 소폭", True),
        ("낙관", "20~30억+", "이용률·ASP·점유·부가", False),
    ]
    for i, (name, val, note, hi) in enumerate(scenarios):
        top = Inches(2.0) + i * Inches(1.35)
        round_rect(s, Inches(6.5), top, Inches(6.15), Inches(1.2), SLATE if hi else CARD, None if hi else LINE)
        lines(s, Inches(6.75), top + Inches(0.2), Inches(1.5), Inches(0.35), [name], 13, TEAL_SOFT if hi else TEAL, True)
        lines(s, Inches(8.3), top + Inches(0.15), Inches(4.0), Inches(0.45), [val], 26, WHITE if hi else SLATE, True)
        lines(s, Inches(6.75), top + Inches(0.7), Inches(5.6), Inches(0.35), [note], 12, RGBColor(0x94, 0xA3, 0xB8) if hi else MUTED)
    lines(
        s,
        Inches(6.5),
        Inches(6.15),
        Inches(6.2),
        Inches(0.5),
        ["인가 확보 후 병목은 인지도 · 병원 제휴 · 픽업 대응"],
        12,
        MUTED,
    )

    # ════════════════════════════════════════
    # 09 UNIT ECONOMICS / OFFERING
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "08  Offering", "건수보다 믹스 — 기본은 낮게, 선택은 깊게")
    left_items = [
        ("엔트리", "기본 화장 20~30만"),
        ("주력", "패키지 70~150만"),
        ("프리미엄", "스톤·봉안 등 ~300만"),
        ("모델 ASP", "기본 시나리오 50만"),
    ]
    for i, (t, b) in enumerate(left_items):
        top = Inches(1.55) + i * Inches(1.15)
        round_rect(s, ML, top, Inches(5.6), Inches(1.0), CARD, LINE)
        lines(s, ML + Inches(0.3), top + Inches(0.28), Inches(1.8), Inches(0.4), [t], 14, TEAL, True)
        lines(s, ML + Inches(2.2), top + Inches(0.28), Inches(3.1), Inches(0.4), [b], 15, SLATE, True)

    card(
        s,
        Inches(6.6),
        Inches(1.55),
        Inches(6.05),
        Inches(2.4),
        "매출 구성",
        [
            "• 화장 패키지 · 추모실·참관·증명서",
            "• 픽업·운구 (병원/자택 접근성)",
            "• 봉안·수목·자연장 (거점 락인)",
            "• 스톤·굿즈 (고가 업셀)",
        ],
    )
    card(
        s,
        Inches(6.6),
        Inches(4.15),
        Inches(6.05),
        Inches(2.3),
        "가격·부가 전략",
        [
            "• 기본/선택 분리 → 2028 게시제 대비",
            "• 공개 ASP↓ · 실ASP는 선택 업셀",
            "• 업사이드: 추모 구독·커머스·상조 수수료",
        ],
    )

    # ════════════════════════════════════════
    # 10 PRODUCT
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "09  Product", "응급에는 웹, 기억에는 앱")
    # journey
    journey = [
        ("당일", "모바일 웹", "견적 · 픽업 · 예약\n카톡/병원 링크", TEAL),
        ("인도 후", "웹 추모관", "프로필 · 앨범\n방명록 · 공유", TEAL),
        ("습관화", "앱 유도", "기일 알림 · 케어\n멤버십 연결", SLATE),
    ]
    for i, (stage, ch, body, col) in enumerate(journey):
        left = ML + i * Inches(4.15)
        round_rect(s, left, Inches(1.5), Inches(3.95), Inches(2.8), CARD, LINE)
        rect(s, left, Inches(1.5), Inches(3.95), Inches(0.08), col)
        lines(s, left + Inches(0.25), Inches(1.75), Inches(3.5), Inches(0.3), [stage], 12, MUTED)
        lines(s, left + Inches(0.25), Inches(2.15), Inches(3.5), Inches(0.4), [ch], 20, SLATE, True)
        lines(s, left + Inches(0.25), Inches(2.75), Inches(3.5), Inches(1.2), body.split("\n"), 14, INK, gap=6)

    rows = [
        ("보호자", "웹 접수 → 선택적 앱", "설치 마찰 최소화"),
        ("의전 인력", "고팀장 네이티브", "배차·푸시·현장"),
        ("운영", "관리자 웹 OS", "케이스·정산·CRM"),
    ]
    for i, (a, b, c) in enumerate(rows):
        top = Inches(4.6) + i * Inches(0.7)
        round_rect(s, ML, top, Inches(12.0), Inches(0.6), SOFT if i % 2 == 0 else CARD, LINE)
        lines(s, ML + Inches(0.3), top + Inches(0.12), Inches(2.5), Inches(0.4), [a], 13, TEAL, True)
        lines(s, ML + Inches(3.0), top + Inches(0.12), Inches(5.0), Inches(0.4), [b], 13, SLATE)
        lines(s, ML + Inches(8.2), top + Inches(0.12), Inches(3.5), Inches(0.4), [c], 13, MUTED)

    # ════════════════════════════════════════
    # 11 GTM
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "10  Go-to-Market", "수요를 만드는 채널 ≠ 인력을 쓰는 방식")
    # demand
    lines(s, ML, Inches(1.45), Inches(7.5), Inches(0.35), ["수요 채널 (우선순위)"], 14, TEAL, True)
    demand = [
        ("1", "동물병원", "최대 건수 · 임종/안락사 접점"),
        ("2", "자택·방문", "24h 응급 · 브랜드 직접 예약"),
        ("3", "상조 본사", "캐파 제휴 · 하청화 방지"),
        ("4", "호텔 이관", "리조이스 CRM (중기 차별화)"),
    ]
    for i, (n, t, d) in enumerate(demand):
        top = Inches(1.9) + i * Inches(0.95)
        round_rect(s, ML, top, Inches(7.4), Inches(0.85), CARD, LINE)
        oval = s.shapes.add_shape(MSO_SHAPE.OVAL, ML + Inches(0.2), top + Inches(0.18), Inches(0.5), Inches(0.5))
        oval.fill.solid()
        oval.fill.fore_color.rgb = TEAL
        oval.line.fill.background()
        nt = tb(s, ML + Inches(0.2), top + Inches(0.25), Inches(0.5), Inches(0.4))
        put(nt, n, 14, True, WHITE, PP_ALIGN.CENTER, clear=True)
        lines(s, ML + Inches(0.9), top + Inches(0.22), Inches(2.2), Inches(0.4), [t], 15, SLATE, True)
        lines(s, ML + Inches(3.2), top + Inches(0.22), Inches(3.9), Inches(0.4), [d], 13, MUTED)

    # supply asset
    round_rect(s, Inches(8.4), Inches(1.45), Inches(4.3), Inches(5.1), SLATE, None)
    lines(s, Inches(8.7), Inches(1.75), Inches(3.8), Inches(0.35), ["SUPPLY ASSET"], 11, TEAL_SOFT, True)
    lines(s, Inches(8.7), Inches(2.2), Inches(3.8), Inches(0.9), ["고팀장", "500명+"], 26, WHITE, True, gap=2)
    lines(
        s,
        Inches(8.7),
        Inches(3.4),
        Inches(3.8),
        Inches(2.8),
        [
            "수요 풀이 아닙니다",
            "",
            "• 펫 인증 온콜 의전",
            "• 찾아가는 염습·픽업",
            "• Phase1 서부 30~50명",
            "• 채용 CAC ≈ 0",
            "• 상조 본사 소개 다리",
        ],
        13,
        RGBColor(0xCB, 0xD5, 0xE1),
        gap=5,
    )

    # ════════════════════════════════════════
    # 12 COMPETITION + MOAT
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "11  Competition & Moat", "시설을 가진 자가, 접수를 뺏기지 않는다")
    comps = [
        ("체인 장묘", "포포즈 등", "서부 허브 + 투명 UX"),
        ("상조 자본", "스카이펫 등", "선택 제휴, 자체 접수"),
        ("로컬·무허가", "가격 경쟁", "합법·모니터링 차별"),
    ]
    for i, (t, e, r) in enumerate(comps):
        card(s, ML + i * Inches(4.15), Inches(1.5), Inches(3.95), Inches(2.0), t, [e, r])

    moats = [
        ("인가", "동물장묘업 인가 확보"),
        ("입지", "을왕 · 서부·공항 동선"),
        ("인력", "고팀장 의전망"),
        ("신뢰", "허가번호·가격 공개"),
        ("제품", "웹→앱 메모리얼"),
        ("옵션", "리조이스 CRM"),
    ]
    for i, (t, b) in enumerate(moats):
        left = ML + (i % 3) * Inches(4.15)
        top = Inches(3.8) + (i // 3) * Inches(1.35)
        round_rect(s, left, top, Inches(3.95), Inches(1.2), SOFT, LINE)
        lines(s, left + Inches(0.25), top + Inches(0.25), Inches(3.5), Inches(0.3), [t], 13, TEAL, True)
        lines(s, left + Inches(0.25), top + Inches(0.6), Inches(3.5), Inches(0.4), [b], 14, SLATE)

    # ════════════════════════════════════════
    # 13 ROADMAP (인가 확보 반영)
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "12  Roadmap", "핵심 게이트 통과 — 가동 실행 단계로")
    # cleared gate
    round_rect(s, ML, Inches(1.45), Inches(12.0), Inches(1.55), TEAL_SOFT, TEAL)
    lines(s, ML + Inches(0.35), Inches(1.6), Inches(11.3), Inches(0.35), ["CLEARED  —  동물장묘업 인가 확보 확인"], 14, TEAL, True)
    lines(
        s,
        ML + Inches(0.35),
        Inches(2.05),
        Inches(11.3),
        Inches(0.7),
        [
            "영업 인가(동물장묘업)는 확인 완료. 합법 화장·장례 본영업의 전제 리스크가 해소되었다.",
            "잔여 실사: 건축 주용도·환경(화장로) 정합 · 면적 문서 대조 · 민원 이력 — 가동 병행 가능 항목.",
        ],
        13,
        INK,
        gap=4,
    )
    phases = [
        ("0", "정합", "용도·환경 대조\n브랜드·의전 선발"),
        ("1", "가동", "병원 GTM · 웹\nOS · 온콜 30~50"),
        ("2", "락인", "앱 메모리얼\nCRM · 선택 상조"),
        ("3", "확장", "다거점 · SaaS\n멤버십"),
    ]
    for i, (n, t, b) in enumerate(phases):
        left = ML + i * Inches(3.1)
        round_rect(s, left, Inches(3.4), Inches(2.95), Inches(3.0), CARD, LINE)
        lines(s, left + Inches(0.25), Inches(3.65), Inches(2.5), Inches(0.3), [f"PHASE {n}"], 11, TEAL, True)
        lines(s, left + Inches(0.25), Inches(4.05), Inches(2.5), Inches(0.4), [t], 20, SLATE, True)
        lines(s, left + Inches(0.25), Inches(4.65), Inches(2.5), Inches(1.3), b.split("\n"), 13, MUTED, gap=6)

    # ════════════════════════════════════════
    # 14 RISKS
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "13  Risks", "리스크를 숨기지 않는다")
    risks = [
        ("건축 용도·환경 정합", "인가와 대장·화장로 인허가 대조"),
        ("문서·면적 불일치", "실사로 필지·건축 확정"),
        ("상조 하청화", "병원·자체 웹 접수 병행"),
        ("시장 과대 추정", "Bottom-up 밴드만 사용"),
        ("점유·이용률 민감", "시나리오 표기 · 병원 KPI"),
        ("민원·님비", "입지·운영 SOP · 모니터링 공개"),
    ]
    for i, (r, m) in enumerate(risks):
        left = ML + (i % 2) * Inches(6.2)
        top = Inches(1.5) + (i // 2) * Inches(1.6)
        round_rect(s, left, top, Inches(5.95), Inches(1.4), CARD, LINE)
        lines(s, left + Inches(0.3), top + Inches(0.25), Inches(5.4), Inches(0.35), [r], 15, SLATE, True)
        lines(s, left + Inches(0.3), top + Inches(0.75), Inches(5.4), Inches(0.4), [f"완화  {m}"], 13, TEAL)

    # ════════════════════════════════════════
    # 15 HIGHLIGHTS + ASK
    # ════════════════════════════════════════
    p += 1
    s = blank(prs)
    chrome(s, p)
    header(s, "14  Ask", "투자 포인트와 다음 숫자")
    hs = [
        "장묘업 인가 확보 — 합법 본영업 전제 해소",
        "구조적 수요 — 고령화 · 매장↓ · 화장·추모↑",
        "공급 공백 — 인천·서부 합법 허브",
        "운영 인력 — 고팀장 500명+ 온콜 전환",
        "현실 밴드 — 가동 시 코어 연 10~15억",
        "제품 해자 — 웹 접근성 + 앱 메모리얼",
    ]
    for i, hline in enumerate(hs):
        top = Inches(1.5) + i * Inches(0.7)
        round_rect(s, ML, top, Inches(7.5), Inches(0.6), CARD, LINE)
        rect(s, ML, top, Inches(0.08), Inches(0.6), TEAL)
        lines(s, ML + Inches(0.3), top + Inches(0.12), Inches(7.0), Inches(0.4), [hline], 13, INK)

    round_rect(s, Inches(8.5), Inches(1.5), Inches(4.2), Inches(5.0), SLATE, None)
    lines(s, Inches(8.85), Inches(1.85), Inches(3.6), Inches(0.35), ["THE ASK"], 12, TEAL_SOFT, True)
    lines(s, Inches(8.85), Inches(2.4), Inches(3.6), Inches(0.8), ["라운드 · 금액 · 지분", "TBD"], 20, WHITE, True, gap=6)
    lines(
        s,
        Inches(8.85),
        Inches(3.6),
        Inches(3.6),
        Inches(2.5),
        [
            "자금 용도 (예정)",
            "· 자산 · 인허가 · 설비",
            "· 운영 · 병원 GTM",
            "· 웹 / OS / 메모리얼",
            "· 운전자본 · 예비",
            "",
            "실사·재무모델 후 기입",
        ],
        13,
        RGBColor(0xCB, 0xD5, 0xE1),
        gap=5,
    )

    # ════════════════════════════════════════
    # 16 CLOSE
    # ════════════════════════════════════════
    p += 1
    s = blank(prs, dark=True)
    rect(s, 0, 0, Inches(0.18), H, TEAL)
    lines(s, Inches(0.85), Inches(2.0), Inches(11), Inches(0.35), ["NEXT"], 12, TEAL, True)
    lines(s, Inches(0.85), Inches(2.5), Inches(11), Inches(0.8), ["배웅에서 시작해,", "라이프케어로 확장한다"], 28, WHITE, True, gap=8)
    rect(s, Inches(0.85), Inches(4.3), Inches(1.4), Inches(0.05), TEAL)
    lines(
        s,
        Inches(0.85),
        Inches(4.6),
        Inches(11),
        Inches(1.5),
        [
            "다음 자료: 리조이스(펫호텔) IR  ·  통합 CRM  ·  재무모델·Ask  ·  용도·환경 정합 체크",
            "근거: 산업분석 · 문화조사 · Bottom-up · 유입/기능맵 · 범위확장 초안",
            "",
            "본 자료는 논의용입니다. 투자 결정은 별도 실사와 자문을 전제로 합니다.",
        ],
        14,
        RGBColor(0x94, 0xA3, 0xB8),
        gap=6,
    )

    out = r"D:\dev_pawkorea\pet-teamjang\doc\IR_BAEUNG_pet_funeral_v0.3.pptx"
    prs.save(out)
    print(f"saved: {out}  slides={len(prs.slides)}")


if __name__ == "__main__":
    build()
