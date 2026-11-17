# -*- coding: utf-8 -*-
"""Build ODM RFQ PDF (Korean) from key sections."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

FONT = "Malgun"
FONT_B = "MalgunBold"
# Windows Korean fonts
for path, name in [
    (r"C:\Windows\Fonts\malgun.ttf", FONT),
    (r"C:\Windows\Fonts\malgunbd.ttf", FONT_B),
]:
    if os.path.exists(path):
        pdfmetrics.registerFont(TTFont(name, path))

TEAL = HexColor("#0F766E")
SLATE = HexColor("#0F172A")
MUTED = HexColor("#64748B")
LINE = HexColor("#E2E8F0")
SOFT = HexColor("#F1F5F9")

OUT = r"D:\dev_pawkorea\pet-teamjang\doc\PET-Aeye_NPU카메라_ODM_견적요청서_v1.0.pdf"


def S(name, **kw):
    base = dict(fontName=FONT, fontSize=10, leading=15, textColor=SLATE)
    base.update(kw)
    return ParagraphStyle(name, **base)


def P(text, style):
    return Paragraph(text.replace("\n", "<br/>"), style)


def section(title):
    return [
        Spacer(1, 4 * mm),
        P(title, S("h", fontName=FONT_B, fontSize=13, textColor=TEAL, spaceAfter=3 * mm)),
        HRFlowable(width="100%", thickness=0.5, color=LINE, spaceAfter=3 * mm),
    ]


def kv_table(rows, col_widths=None):
    data = [[P(a, S("t", fontSize=9, fontName=FONT_B)), P(b, S("t", fontSize=9))] for a, b in rows]
    t = Table(data, colWidths=col_widths or [42 * mm, 138 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), SOFT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
            ]
        )
    )
    return t


def grid_table(header, rows, col_widths):
    styles_h = S("th", fontName=FONT_B, fontSize=8, textColor=white, leading=11)
    styles_c = S("td", fontSize=8, leading=11)
    data = [[P(h, styles_h) for h in header]]
    for r in rows:
        data.append([P(c, styles_c) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BOX", (0, 0), (-1, -1), 0.4, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, SOFT]),
    ]
    t.setStyle(TableStyle(style))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 10 * mm, "PAW-RFQ-CAM-2026-001  ·  Confidential  ·  파우코리아 PET-Aeye")
    canvas.drawRightString(192 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


def build():
    doc = SimpleDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
    )
    story = []

    # Cover block
    story.append(P("PET-Aeye NPU Camera", S("c1", fontName=FONT_B, fontSize=11, textColor=TEAL)))
    story.append(P("ODM 개발 · 양산 견적 요청서 (RFQ)", S("c2", fontName=FONT_B, fontSize=18, textColor=SLATE, spaceAfter=4 * mm)))
    story.append(
        kv_table(
            [
                ("문서번호", "PAW-RFQ-CAM-2026-001"),
                ("버전", "v1.0 (발송용)"),
                ("발주 예정", "파우코리아 (PET-Aeye 사업)"),
                ("회신 기한", "요청일로부터 15영업일"),
                ("통화", "USD 또는 KRW · VAT·관세·물류 항목 분리"),
                ("범위 외", "BLE 태그/GW · 서버 · 개발용 PC/노트북 — 별도 조달"),
            ]
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        P(
            "본 문서는 발주 확정이 아닙니다. 견적 유효기간·결제·MOQ·Incoterms를 명시해 주십시오. "
            "상세 BOM·도면은 상호 NDA 후 공유합니다.",
            S("note", fontSize=9, textColor=MUTED, leading=13),
        )
    )

    story += section("0. 요청 요약")
    story.append(
        P(
            "반려동물 호텔·리조트·가정에 동일 SKU로 공급할 "
            "<b>NPU 내장 IP 카메라(주력: 60GHz FMCW 바이탈 일체형)</b>의 ODM 개발·양산 견적을 요청합니다.",
            S("b", fontSize=10, spaceAfter=3 * mm),
        )
    )
    story.append(
        grid_table(
            ["항목", "내용"],
            [
                ["제품", "천장·벽 고정형 · 기기 내 NPU 추론"],
                ["연결", "Wi-Fi + 이더넷 + PoE(802.3af) 단일 제품"],
                ["SKU", "바이탈형 단일 · 1·2차 합 약 1,000대"],
                ["펌웨어", "발주처 AI 모델 · OTA 필수 · 결과·이벤트만 서버 전송"],
                ["채널", "영종 펫호텔 · 횡성 펫리조트 · 가정용 홈캠 (동일 기판)"],
                ["PoC 칩", "Axera AX630C / MaixCAM2 계열 · 동등 이상 제안 환영"],
            ],
            [32 * mm, 148 * mm],
        )
    )

    story += section("1. 수량 · 단계")
    story.append(
        grid_table(
            ["단계", "시기", "수량", "용도"],
            [
                ["EVT/DVT", "계약 후 협의", "바이탈 20~50대", "화각·야간·AI·OTA·레이더·API"],
                ["1차 양산", "2027", "약 500대 전량 바이탈", "영종 펫호텔 + 홈 초기"],
                ["2차 양산", "횡성 준공 전", "약 500대 전량 바이탈", "횡성 리조트 + 홈·예비"],
                ["합계", "", "약 1,000대", "동일 SKU · 동일 기판"],
            ],
            [32 * mm, 38 * mm, 48 * mm, 62 * mm],
        )
    )
    story.append(Spacer(1, 2 * mm))
    story.append(
        P(
            "단가: 로트 500대 / 누적 1,000대 / 3,000대를 각각 제시. "
            "1·2차 분할 납품(약 500+500)·누적 할인가 가능 여부 명시. "
            "표준형(레이더 미실장) 단가는 참고용만.",
            S("n", fontSize=9, textColor=MUTED),
        )
    )

    story += section("2. 하드웨어 요구 (요지)")
    story.append(
        grid_table(
            ["항목", "요구"],
            [
                ["AI SoC", "AX630C급 ≥약 3TOPS · RAM ≥1GB"],
                ["센서", "≥4MP · 1/1.8\"급 저조도 · IR 850nm + IR-Cut"],
                ["네트워크·전원", "Wi-Fi 6(+5↑) + 이더넷 · PoE 802.3af + DC 어댑터 둘 다"],
                ["기타", "마이크 · microSD · 물리 셔터(강력 희망) · 고정 브라켓"],
                ["목표 단가(참고)", "누적 1,000대 기준 도착 약 USD 85~110 / 12~15만원대 (VAT 별도)"],
            ],
            [40 * mm, 140 * mm],
        )
    )

    story += section("3. 펌웨어 · OTA · 바이탈 API")
    story.append(
        P(
            "<b>역할:</b> 발주처 = AI 모델·OTA 서버·관제/앱 · ODM = 런타임·스트림·OTA 에이전트·레이더 파싱. "
            "ODM 클라우드 강제 연동 불가.",
            S("b", fontSize=9, spaceAfter=2 * mm),
        )
    )
    story.append(
        P(
            "<b>P0:</b> 기기 NPU 다객체 탐지·포즈 · RTSP(H.265) 메인/서브 · 스마트 녹화 · microSD 버퍼 · "
            "기기 인증서 · SSH 상시 개방 금지 · QR/Wi-Fi 프로비저닝.",
            S("b", fontSize=9, spaceAfter=2 * mm),
        )
    )
    story.append(
        P(
            "<b>OTA:</b> 모델 OTA + 펌웨어 OTA · 서명 검증 · 실패 롤백 · /ota/check·report · DVT 시연 필수. "
            "포함/미포함 단가 분리.",
            S("b", fontSize=9, spaceAfter=2 * mm),
        )
    )
    story.append(
        P(
            "<b>바이탈(전량):</b> 60GHz FMCW · 재실·호흡 참고값(비의료) · UART/SPI · "
            "펌웨어가 MQTT/HTTPS JSON으로 발주처 서버에만 전송. "
            "ADC 원본 상시 업로드 금지.",
            S("b", fontSize=9, spaceAfter=2 * mm),
        )
    )

    story += section("4. 견적에 반드시 나눌 항목")
    story.append(
        P(
            "<b>NRE:</b> 금형 · Wi-Fi+PoE 기판 · 펌웨어 기본 · OTA 에이전트 · NPU 통합 · "
            "바이탈(FMCW+API) · (옵션) person 블러 · EVT/DVT 샘플 · KC(레이더 포함).",
            S("b", fontSize=9, spaceAfter=2 * mm),
        )
    )
    story.append(
        P(
            "<b>양산 단가:</b> 500 / 1,000 / 3,000대 · Incoterms · 옵션(셔터·스피커·PTZ·어댑터·브라켓).",
            S("b", fontSize=9, spaceAfter=2 * mm),
        )
    )
    story.append(
        P(
            "<b>유지보수:</b> 보증 기간 OTA 버그픽스 · 프로토콜 변경 공수 · 단종 사전 통보(권장 12개월).",
            S("b", fontSize=9),
        )
    )

    story += section("5. 일정 · 회신 패키지")
    story.append(
        grid_table(
            ["마일스톤", "목표", "산출물"],
            [
                ["킥오프", "계약 후 2주", "사양서 서명"],
                ["EVT", "+8~12주", "바이탈 샘플 · UART"],
                ["DVT", "+4~8주", "OTA 롤백 · JSON API 시연"],
                ["PVT·인증", "협의", "KC (레이더 포함)"],
                ["1차 양산", "2027", "바이탈 약 500대"],
                ["2차 양산", "협의", "바이탈 약 500대"],
            ],
            [36 * mm, 36 * mm, 108 * mm],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        P(
            "회신: ①실적 ②RFQ 대비표 ③§견적 ④MOQ·결제 ⑤일정 ⑥OTA 개요 "
            "⑦바이탈 모듈·API ⑧원산지·Longevity ⑨NDA 후 블록도·렌더.",
            S("b", fontSize=9),
        )
    )

    story += section("6. 연락 (발송 전 기입)")
    story.append(
        kv_table(
            [
                ("구매·총괄", "______________________________"),
                ("기술 문의", "______________________________"),
                ("샘플 수령지", "______________________________"),
                ("요청일", "______________________________"),
            ]
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(
        P(
            "상세 사양·JSON 예시·인수 테스트 목록은 동봉 Markdown "
            "(PET-Aeye_NPU카메라_ODM_견적요청서_v1.0.md)을 기준으로 합니다.",
            S("f", fontSize=8, textColor=MUTED),
        )
    )
    story.append(
        P(
            "※ 본 RFQ는 가정치·내부 기획 기반이며, 법무·구매 검토 후 발송합니다.",
            S("f", fontSize=8, textColor=MUTED),
        )
    )

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    build()
