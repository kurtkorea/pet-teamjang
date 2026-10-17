# -*- coding: utf-8 -*-
"""PET-Aeye x WaveDyne LiDAR vital — contactless vital sensing expansion deck v0.1."""
from pptx import Presentation
from pptx.dml.color import RGBColor
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
OUT = r"D:\dev_pawkorea\pet-teamjang\doc\PLAN_PAWKOREA_PET-Aeye_LiDAR_vital_v0.1.pptx"


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
    text(slide, MX, 0.45, 9, 0.3, [(section, 11, ACCENT, True)])
    text(slide, MX, 0.8, 11.9, 1.0, [(title, 25, fg, True)])
    text(slide, MX, 7.0, 9, 0.25, [("PET-Aeye × WaveDyne · 라이다 비접촉 바이탈", 9, sub, False)])
    text(slide, 11.63, 7.0, 1.0, 0.25, [(f"{page:02d}", 9, sub, True)], PP_ALIGN.RIGHT)


def table(slide, x, y, cols, rows, row_h, body=13, head_gap=0.45):
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
            bold = ci == 0
            text(slide, cx, ry, w - 0.15, row_h - 0.05, [(t, body, INK, bold, 1) for t in cell.split("\n")])
            cx += w
        hline(slide, x, ry + row_h - 0.1, total_w)
        ry += row_h
    return ry


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    page = 0

    # 01 COVER
    page += 1
    s = new_slide(prs)
    box(s, 0, 0, 13.333, 0.12, ACCENT)
    text(s, MX, 0.7, 10, 0.3, [("PLANNING DOC  ·  2026.10  ·  v0.1  ·  PoC · 로드맵 제안", 11, GRAY, True)])
    text(
        s,
        MX,
        1.55,
        11.9,
        2.6,
        [
            ("보이는 안심에서,", 46, INK, True, 0),
            ("느껴지는 안심으로.", 46, ACCENT, True, 0),
        ],
    )
    text(
        s,
        MX,
        4.0,
        11.3,
        0.9,
        [
            ("PET-Aeye × WaveDyne FMCW 라이다 — 비접촉 바이탈", 18, INK, True, 4),
            ("CCTV에 라이다 반도체를 결합해, 영상 없이도 호흡·활동·수면을 읽고 보호자 리포트에 담습니다.", 14, GRAY, False),
        ],
    )
    hline(s, MX, 5.55, CW, INK, 0.02)
    facts = [
        ("6D 센싱", "거리·속도·재질 동시"),
        ("μm급", "미세 변위 → 호흡"),
        ("영상 아님", "거리·속도 데이터"),
        ("야간 OK", "빛 없어도 동작"),
    ]
    for i, (v, lab) in enumerate(facts):
        text(s, MX + i * 3.0, 5.8, 2.8, 0.5, [(v, 22, INK, True, 2), (lab, 12, GRAY, False)])

    # 02 WHY LIDAR
    page += 1
    s = new_slide(prs)
    frame(s, page, "WHY", "카메라가 못 보는 곳을, 라이다가 채웁니다")
    left = [
        ("지금 PET-Aeye", 13, ACCENT, True, 8),
        ("카메라 + AI 행동 검출", 15, INK, True, 2),
        ("무엇을 하고 있는지 '봅니다'", 12, GRAY, False, 12),
        ("한계", 13, GRAY, True, 6),
        ("· 소등된 야간에는 약합니다", 13, INK, False, 4),
        ("· 거리·속도 같은 물리량은 직접 못 읽습니다", 13, INK, False, 4),
        ("· 영상 노출에 민감한 보호자가 있습니다", 13, INK, False, 0),
    ]
    right = [
        ("더하는 것 · FMCW 라이다", 13, ACCENT, True, 8),
        ("거리·속도·3D 비접촉 센싱", 15, INK, True, 2),
        ("'괜찮은 상태인지'를 느낍니다", 12, GRAY, False, 12),
        ("강점", 13, GRAY, True, 6),
        ("· 빛이 없어도 호흡·재실 확인", 13, INK, False, 4),
        ("· μm급 변위로 미세 움직임 포착", 13, INK, False, 4),
        ("· 영상이 아닌 데이터 → 프라이버시", 13, INK, False, 0),
    ]
    box(s, MX, 1.95, 5.75, 4.5, WHITE)
    box(s, 6.85, 1.95, 5.78, 4.5, ACCENT_WASH)
    text(s, MX + 0.35, 2.25, 5.1, 4.0, left)
    text(s, 7.2, 2.25, 5.1, 4.0, right)

    # 03 WAVEDYNE TECH
    page += 1
    s = new_slide(prs)
    frame(s, page, "TECHNOLOGY · WaveDyne", "검증된 반도체 기술 위에 올립니다")
    cards = [
        ("WD-FMCW 4세대", "거리·속도·재질 동시 (6D)\nμm급 · 1,000만 포인트"),
        ("솔리드스테이트", "KTN + 메타렌즈\n기계 구동부 0 · 소형"),
        ("카메라 융합", "LiDAR + Camera Fusion\n멀티모달 AI SoC 내장"),
        ("가격", "양산 목표 50만원/대\nAEVA 대비 약 1/52"),
    ]
    for i, (h, b) in enumerate(cards):
        x = MX + i * 3.0
        hline(s, x, 2.0, 2.75, INK, 0.02)
        text(s, x, 2.2, 2.7, 0.5, [(h, 16, INK, True)])
        text(s, x, 2.95, 2.7, 1.2, [(t, 12, GRAY, False, 3) for t in b.split("\n")])
    box(s, MX, 4.6, CW, 1.85, SAND)
    text(
        s,
        MX + 0.35,
        4.8,
        11.3,
        1.5,
        [
            ("일정 전제", 13, ACCENT, True, 6),
            ("반도체 3종 FAB-in 2026.12 → First Silicon 2027.03 → FMCW 라이다 실증.", 14, INK, False, 6),
            ("따라서 바이탈은 '지금 운영 기능'이 아니라 WaveDyne 일정에 맞춘 PoC·로드맵입니다.", 13, GRAY, False, 6),
            ("출처: 웨이브다인 IR 2026.09.21 (공개 자료)", 10, GRAY, False),
        ],
    )

    # 04 BEE PRECEDENT
    page += 1
    s = new_slide(prs)
    frame(s, page, "PROOF POINT", "이미 '생명체'를 센서로 돌보고 있습니다 — 스마트 벌통")
    steps = [("환경 센서", "벌통 내부 데이터 수집"), ("엣지 AI 분석", "초저전력 온디바이스"), ("최적 환경·노동 절감", "꿀벌 성장 최적화")]
    y = 2.4
    for i, (h, b) in enumerate(steps):
        x = MX + i * 4.1
        box(s, x, y, 3.5, 1.3, ACCENT if i == 2 else WHITE)
        fg = WHITE if i == 2 else INK
        sub = ACCENT_DIM if i == 2 else GRAY
        text(s, x, y, 3.5, 1.3, [(h, 18, fg, True, 3), (b, 12, sub, False)], PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
        if i < 2:
            text(s, x + 3.5, y + 0.45, 0.6, 0.4, [("→", 22, GRAY, True)], PP_ALIGN.CENTER)
    box(s, MX, 4.35, CW, 2.05, ACCENT_WASH)
    text(
        s,
        MX + 0.35,
        4.55,
        11.3,
        1.75,
        [
            ("무엇을 증명하나", 13, ACCENT, True, 6),
            ("WaveDyne은 '센서 → 생체 상태 해석 → 환경/알림'을 자체 칩으로 매출 단계까지 올린 경험이 있습니다.", 14, INK, False, 6),
            ("대상만 꿀벌 → 반려견으로 바뀝니다. 벌통 환경 최적화 = 객실 환경 최적화 + 개체 바이탈 모니터링.", 14, INK, False, 6),
            ("근거: IR p15 스마트 벌통 AI(매출 0.7억·26.11 납품) · p25 '자체 칩 적용 예정' · p27 벌통 내부 환경 분석 · 1호 파트너 대동(정밀농업)", 10, GRAY, False),
        ],
    )

    # 05 VITALS
    page += 1
    s = new_slide(prs)
    frame(s, page, "WHAT WE MEASURE", "비접촉으로 읽는 개체 상태")
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

    # 06 FORM FACTOR
    page += 1
    s = new_slide(prs)
    frame(s, page, "FORM FACTOR", "CCTV + 라이다 융합 센서 한 대")
    parts = [
        ("카메라 모듈", "영상 · AI 행동 검출", "현재 PET-Aeye", SAND),
        ("WaveDyne 라이다", "거리 · 속도 · 3D", "호흡·미동·재실·낙상", ACCENT),
        ("엣지 AI 퓨전", "센서 융합 → 상태 요약", "WaveDyne 멀티모달 SoC", INK),
    ]
    for i, (h, b, c, color) in enumerate(parts):
        x = MX + i * 4.1
        box(s, x, 2.1, 3.6, 2.5, color)
        fg = INK if color == SAND else WHITE
        sub = GRAY if color == SAND else (ACCENT_DIM if color == ACCENT else NIGHT_GRAY)
        text(s, x + 0.3, 2.4, 3.0, 1.9, [(h, 18, fg, True, 6), (b, 13, fg, False, 4), (c, 11, sub, False)])
        if i < 2:
            text(s, x + 3.6, 3.1, 0.5, 0.5, [("+", 24, GRAY, True)], PP_ALIGN.CENTER)
    box(s, MX, 4.95, CW, 1.5, ACCENT_WASH)
    text(
        s,
        MX + 0.35,
        5.15,
        11.3,
        1.2,
        [
            ("1실 1센서 · 기존 PET-Aeye 네트워크(관제실·녹화·관리자 웹)에 바이탈 채널만 추가합니다.", 14, INK, True, 6),
            ("우선 적용: 3F 중대형·패밀리 26실, 격리실·노령견 객실부터. WaveDyne의 카메라 융합 전략과도 일치합니다.", 12, GRAY, False),
        ],
    )

    # 07 REPORT
    page += 1
    s = new_slide(prs)
    frame(s, page, "GUARDIAN REPORT", "보호자 리포트에 바이탈을 더합니다")
    cols = [("리포트 블록", 2.8), ("기존", 4.0), ("추가 (라이다)", 5.13)]
    rows = [
        ("활동", "산책 횟수·거리", "시간대별 활동량 그래프"),
        ("휴식", "낮잠·야간 숙면(정성)", "호흡수 추이 · 수면 안정도(정량)"),
        ("안심", "이상 행동 알림", "호흡 급변 · 장시간 무미동 · 낙상 조기 알림"),
        ("요약", "스태프 메모", "'오늘 호흡·휴식 안정' 상태 한 줄 요약"),
    ]
    table(s, MX, 1.95, cols, rows, 0.72, body=13)
    box(s, MX, 5.35, CW, 1.1, SAND)
    text(
        s,
        MX + 0.35,
        5.5,
        11.3,
        0.9,
        [
            ("알림은 고신뢰 규칙부터 켭니다.", 14, INK, True, 4),
            ("예: 재실 중 장시간 무미동 + 호흡 패턴 이상 동시 충족 → 스태프 확인 후 보호자 공유.", 12, GRAY, False),
        ],
    )

    # 08 HOTEL EXPANSION
    page += 1
    s = new_slide(prs)
    frame(s, page, "EXPANSION · 호텔", "이 센서로 호텔이 더 할 수 있는 것")
    items = [
        ("시니어·메디컬 객실", "노령·만성질환견 상시 모니터링"),
        ("야간·사각 보완", "소등 후 호흡·재실, 침대 밑 사각"),
        ("낙상·발작 조기경보", "자세 급변 + 미동 이상 포착"),
        ("객실 환경 최적화", "온습도·소음과 바이탈 상관 학습(벌통 응용)"),
        ("3D 체형·체중 기록", "입·퇴실 비접촉 기록 · 분쟁 예방"),
        ("분리불안 정량화", "활동·호흡 변동성으로 스트레스 지표"),
    ]
    for i, (h, d) in enumerate(items):
        cx = MX + (i % 3) * 4.05
        cy = 2.0 + (i // 3) * 1.55
        dot(s, cx + 0.12, cy + 0.16, 0.18, ACCENT)
        text(s, cx + 0.42, cy, 3.5, 1.3, [(h, 15, INK, True, 3), (d, 12, GRAY, False)])
    box(s, MX, 5.3, CW, 1.15, ACCENT_WASH)
    text(
        s,
        MX + 0.35,
        5.48,
        11.3,
        0.9,
        [
            ("나동 동물병원(2차)과 결합하면 입원견 비접촉 모니터링으로 면회를 대체할 수 있습니다.", 14, INK, True, 4),
            ("고령·의료 수요는 프리미엄 단가로 이어져, 객실 차별화의 축이 됩니다.", 12, GRAY, False),
        ],
    )

    # 09 SAAS / DATA
    page += 1
    s = new_slide(prs)
    frame(s, page, "EXPANSION · SaaS · 데이터", "제품과 데이터로 넓힙니다")
    cards = [
        ("Vital 티어", "SaaS 상위 플랜 신설\n(Basic · Plus · Pro 위)", "하드웨어(융합 센서) + 바이탈 리포트 번들"),
        ("데이터 자산", "품종·연령·체격별\n정상 바이탈 베이스라인", "이상 탐지 정확도↑ · 펫보험·병원 제휴 근거"),
        ("하드웨어 공급", "WaveDyne 부품·IP\nPET-Aeye 응용·운영", "양산 판가(목표 50만원/대) 전제 센서 공급"),
    ]
    for i, (h, b, c) in enumerate(cards):
        x = MX + i * 4.05
        box(s, x, 2.0, 3.8, 3.7, WHITE if i else ACCENT)
        fg = WHITE if i == 0 else INK
        sub = ACCENT_DIM if i == 0 else GRAY
        text(s, x + 0.3, 2.3, 3.2, 0.3, [("0" + str(i + 1), 11, sub, True)])
        text(s, x + 0.3, 2.7, 3.2, 0.8, [(h, 19, fg, True)])
        text(s, x + 0.3, 3.6, 3.2, 1.0, [(t, 13, fg, False, 3) for t in b.split("\n")])
        hline(s, x + 0.3, 4.65, 3.2, RULE if i else ACCENT_DIM)
        text(s, x + 0.3, 4.8, 3.2, 0.9, [(c, 12, sub if i == 0 else GRAY, False)])

    # 10 ROADMAP
    page += 1
    s = new_slide(prs)
    frame(s, page, "ROADMAP", "WaveDyne 일정에 맞춰 단계로 검증합니다")
    phases = [
        ("P0 · PoC 설계", ["측정 항목·리포트 정의", "1실 실증 설계"], "First Silicon 2027.03 전후"),
        ("P1 · 단일 객실 실증", ["호흡·활동·재실 정확도", "반려견 대상 검증"], "FMCW 라이다 실증"),
        ("P2 · 융합 폼팩터", ["CCTV+라이다 센서 제작", "3F·격리실 적용"], "반도체 3종 양산 셋업"),
        ("P3 · 상품화", ["바이탈 CareReport 정식", "SaaS Vital 티어"], "양산 판가 확보"),
    ]
    hline(s, MX, 2.35, CW, INK, 0.02)
    for i, (name, items, gate) in enumerate(phases):
        x = MX + i * 3.05
        dot(s, x + 0.12, 2.36, 0.24, ACCENT if i <= 1 else INK)
        text(s, x, 2.6, 2.85, 0.45, [(name, 15, INK, True)])
        text(s, x, 3.2, 2.85, 1.6, [(f"·  {t}", 13, INK, False, 6) for t in items])
        box(s, x, 4.9, 2.85, 0.75, SAND)
        text(s, x + 0.15, 4.9, 2.6, 0.75, [("WaveDyne  " + gate, 11, INK, True)], anchor=MSO_ANCHOR.MIDDLE)
    text(
        s,
        MX,
        6.0,
        CW,
        0.9,
        [
            ("유의", 12, ACCENT, True, 4),
            ("반려견은 털·체격·품종 편차가 커 검증이 더 필요합니다. 심박은 검증 후 조건부. 의료기기 아님 — 웰니스 지표로 포지셔닝.", 12, GRAY, False),
        ],
    )

    # 11 SUMMARY (dark)
    page += 1
    s = new_slide(prs, dark=True)
    text(s, MX, 0.45, 9, 0.3, [("SUMMARY", 11, ACCENT, True)])
    text(
        s,
        MX,
        1.7,
        11.8,
        2.4,
        [
            ("영상으로 보던 안심을,", 34, WHITE, True, 8),
            ("호흡과 심박으로 느끼게 합니다.", 34, ACCENT, True),
        ],
    )
    pts = [
        "CCTV에 WaveDyne FMCW 라이다를 결합한 융합 센서",
        "영상 없이 호흡·활동·수면·낙상을 비접촉으로 — 야간·프라이버시 강점",
        "보호자 CareReport에 개체 바이탈 섹션 추가",
        "시니어·메디컬·환경 최적화·SaaS Vital 티어로 확장",
    ]
    for i, t in enumerate(pts):
        y = 4.3 + i * 0.62
        dot(s, MX + 0.12, y + 0.12, 0.16, ACCENT)
        text(s, MX + 0.45, y, 11.2, 0.5, [(t, 15, WHITE, False)])
    text(s, 11.63, 7.0, 1.0, 0.25, [(f"{page:02d}", 9, NIGHT_GRAY, True)], PP_ALIGN.RIGHT)

    prs.save(OUT)
    print(f"saved: {OUT}  slides={len(prs.slides)}")


if __name__ == "__main__":
    build()
