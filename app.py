"""
app.py  —  AI 지역 거시환경 자동 분석 시스템
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
통계청 KOSIS + 네이버 트렌드 + Claude AI 종합 분석
영업기획팀

실행: streamlit run app.py
"""

import random
import pandas as pd
import streamlit as st
from datetime import datetime

from data_collector import (
    get_sido_data, get_all_sido_summary,
    SAMPLE_DB, KOSIS_KEY, NAVER_ID, ANTHROPIC_KEY, SIDO_CODE,
)
from ai_analyzer import get_ai_analysis

# ── 페이지 설정 ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI 지역분석 시스템 | 영업기획팀",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
*{box-sizing:border-box}
html,body,[class*="css"]{font-family:'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif}

[data-testid="stSidebar"]{background:#0f2d52!important}
[data-testid="stSidebar"] *{color:rgba(255,255,255,.85)!important}
[data-testid="stSidebarContent"] hr{border-color:rgba(255,255,255,.12)!important}

[data-testid="metric-container"]{
  background:#f0f6ff;border:1px solid #dde5f0;
  border-radius:10px;padding:12px 14px}
[data-testid="metric-container"] [data-testid="stMetricLabel"]{font-size:11px;color:#64748b}
[data-testid="metric-container"] [data-testid="stMetricValue"]{font-size:20px;font-weight:700;color:#0f2d52}

.cover{background:linear-gradient(135deg,#0f2d52,#1a4a8a);border-radius:12px;padding:24px 28px;margin-bottom:18px}
.cover h1{font-size:22px;font-weight:700;color:#fff;margin:0 0 5px}
.cover p{font-size:12px;color:rgba(255,255,255,.5);margin:0 0 14px}
.cmeta{display:flex;gap:20px;flex-wrap:wrap}
.cml{font-size:10px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.07em}
.cmv{font-size:12px;color:rgba(255,255,255,.9);font-weight:500;margin-top:2px}

.card{background:#fff;border:1px solid #dde5f0;border-radius:10px;padding:14px;margin-bottom:8px}
.cb{border-left:4px solid #2e7dd4;background:#f4f8fe}
.cg{border-left:4px solid #1b6e3a;background:#f0faf5}
.ca{border-left:4px solid #c47a00;background:#fffbf0}
.cr{border-left:4px solid #9b1c1c;background:#fff5f5}

.tag{display:inline-block;font-size:11px;font-weight:500;padding:2px 8px;border-radius:20px;margin:2px}
.tb{background:#e8f2fd;color:#1a56a0}
.tg{background:#e6f4ec;color:#1b6e3a}
.ta{background:#fff4e0;color:#7c4a00}
.tr{background:#fdecea;color:#9b1c1c}
.tgr{background:#f1f0ec;color:#5f5e5a}

.krow{display:flex;align-items:center;gap:7px;padding:5px 0;border-bottom:1px solid #f5f7fb}
.krow:last-child{border:none}
.knum{font-size:10px;font-weight:700;color:#cbd5e1;width:14px;text-align:center}
.ktext{font-size:12px;color:#1a2332;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kb{font-size:9px;padding:1px 5px;border-radius:20px;font-weight:500;flex-shrink:0}
.kh{background:#fff4e0;color:#c45900}
.kn2{background:#fdecea;color:#9b1c1c}
.ku{background:#e6f4ec;color:#1b6e3a}
.ks{background:#e8f2fd;color:#1a56a0}

.nrow{padding:5px 0;border-bottom:1px solid #f5f7fb;display:flex;gap:7px;align-items:flex-start}
.nrow:last-child{border:none}
.ndot{width:5px;height:5px;border-radius:50%;background:#2e7dd4;flex-shrink:0;margin-top:5px}
.ntitle{font-size:12px;color:#1a2332;line-height:1.5;flex:1}
.ndate{font-size:10px;color:#94a3b8;flex-shrink:0}

.src-badge{display:inline-flex;align-items:center;gap:3px;font-size:10px;padding:2px 7px;border-radius:20px;font-weight:500;margin:2px}
.src-live{background:#e6f4ec;color:#1b6e3a}
.src-samp{background:#f1f0ec;color:#5f5e5a}
.src-dot{width:5px;height:5px;border-radius:50%}
.sdl{background:#1b6e3a}
.sds{background:#94a3b8}

.ai-head{background:#0f2d52;border-radius:10px 10px 0 0;padding:12px 16px;display:flex;align-items:center;gap:10px}
.ai-ic{width:30px;height:30px;border-radius:7px;background:rgba(106,180,255,.18);border:1px solid rgba(106,180,255,.28);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#6ab4ff;flex-shrink:0}
.ai-ht h3{font-size:13px;font-weight:500;color:#fff;margin:0 0 1px}
.ai-ht p{font-size:10px;color:rgba(255,255,255,.45);margin:0}
.ascore{text-align:center;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);border-radius:7px;padding:5px 12px}
.ascore .sv{font-size:19px;font-weight:700;color:#fff;line-height:1}
.ascore .sl{font-size:9px;color:rgba(255,255,255,.45);margin-top:1px}
.ai-body{display:grid;grid-template-columns:1fr 1fr;border:1px solid #dde5f0;border-top:none;border-radius:0 0 10px 10px;background:#fff}
.ai-col{padding:12px 14px}
.ai-col:first-child{border-right:1px solid #f0f4f8}
.ai-sec{font-size:10px;font-weight:500;color:#94a3b8;letter-spacing:.05em;text-transform:uppercase;margin-bottom:7px}
.irow{display:flex;gap:8px;align-items:flex-start;padding:7px 0;border-bottom:1px solid #f5f7fb}
.irow:last-child{border:none}
.iic{width:24px;height:24px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0}
.ib{background:#e8f2fd;color:#1a56a0}
.ig{background:#e6f4ec;color:#1b6e3a}
.ia{background:#fff4e0;color:#c45900}
.ir{background:#fdecea;color:#9b1c1c}
.ih{font-size:12px;font-weight:500;color:#0f2d52;margin-bottom:2px}
.id{font-size:11px;color:#4a5568;line-height:1.5}
.rrow{display:flex;gap:7px;padding:6px 0;border-bottom:1px solid #f5f7fb;align-items:flex-start}
.rrow:last-child{border:none}
.rnum{font-size:12px;font-weight:700;color:#2e7dd4;width:16px;flex-shrink:0}
.rtext{font-size:12px;color:#1a2332;flex:1;line-height:1.4}
.rtag{font-size:9px;padding:1px 6px;border-radius:20px;font-weight:500;flex-shrink:0;margin-top:2px}
.rth{background:#fdecea;color:#9b1c1c}
.rtm{background:#fff4e0;color:#7c4a00}
.rtl{background:#e6f4ec;color:#1b6e3a}
.ai-sum{border-top:1px solid #dde5f0;background:#fafbfc;padding:10px 14px;font-size:12px;color:#4a5568;line-height:1.6;border-radius:0 0 10px 10px}
.hl{background:#e8f2fd;border-left:3px solid #2e7dd4;border-radius:0 7px 7px 0;padding:9px 13px;font-size:12px;color:#1a56a0;margin:10px 0;font-style:italic}
.map-bg{background:#eef5fb;border-radius:8px;padding:6px}
</style>
""", unsafe_allow_html=True)


# ── 세션 상태 ──────────────────────────────────────────────────────────────
if "sel_sido" not in st.session_state:
    st.session_state.sel_sido = None


# ── 데이터 캐시 ────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(sido: str) -> dict:
    return get_sido_data(sido)

@st.cache_data(ttl=7200, show_spinner=False)
def load_summary() -> list:
    return get_all_sido_summary()


# ── 헬퍼 렌더러 ───────────────────────────────────────────────────────────
_TAG_CLS  = ["tb","tg","ta","tgr"]
_KB_CYCLE = ["kh","ku","kn2","ks","kh","ku"]
_KB_LBL   = {"kh":"급등","ku":"상승","kn2":"신규","ks":"유지"}

def r_tags(kws: list):
    rng = random.Random(42)
    h = '<div style="display:flex;flex-wrap:wrap;gap:3px;margin:7px 0">'
    for kw in kws:
        h += f'<span class="tag {rng.choice(_TAG_CLS)}">{kw}</span>'
    h += '</div>'
    st.markdown(h, unsafe_allow_html=True)

def r_kw_rank(kws: list):
    h = ""
    for i, kw in enumerate(kws[:6]):
        cls = _KB_CYCLE[i % len(_KB_CYCLE)]
        h += (f'<div class="krow"><span class="knum">{i+1}</span>'
              f'<span class="ktext">{kw}</span>'
              f'<span class="kb {cls}">{_KB_LBL[cls]}</span></div>')
    st.markdown(h, unsafe_allow_html=True)

def r_news(items: list):
    h = ""
    for n in items[:6]:
        title = n.get("title","")[:52]
        date  = n.get("pubDate","")[:10]
        link  = n.get("link","#")
        h += (f'<div class="nrow"><div class="ndot"></div>'
              f'<div class="ntitle"><a href="{link}" style="color:#1a2332;text-decoration:none">{title}</a></div>'
              f'<div class="ndate">{date}</div></div>')
    st.markdown(h, unsafe_allow_html=True)

def r_sources(sources: dict):
    lbl = {"pop":"인구","retail":"소매판매지수","grdp":"GRDP",
           "unemployment":"실업률","keywords":"키워드","news":"뉴스"}
    h = '<div style="display:flex;flex-wrap:wrap;gap:4px;margin:6px 0 12px">'
    for key, name in lbl.items():
        src     = sources.get(key,"sample")
        is_live = any(x in str(src) for x in ["KOSIS","NAVER","RSS"])
        cls     = "src-live" if is_live else "src-samp"
        dot_cls = "sdl"      if is_live else "sds"
        label   = src.split("(")[0].strip() if is_live else "샘플"
        h += (f'<span class="src-badge {cls}">'
              f'<div class="src-dot {dot_cls}"></div>'
              f'{name}: {label}</span>')
    h += '</div>'
    st.markdown(h, unsafe_allow_html=True)

def r_retail_chart(series: dict):
    df = pd.DataFrame({"월": series["labels"], "소매판매지수": series["values"]}).set_index("월")
    st.line_chart(df, height=145, use_container_width=True)

def r_age_chart(dist: dict):
    df = pd.DataFrame({"연령대": dist["labels"], "비율(%)": dist["values"]}).set_index("연령대")
    st.bar_chart(df, height=145, use_container_width=True)

def r_ai(analysis: dict, sido: str):
    scores  = analysis.get("scores", {})
    source  = analysis.get("_source","sample")
    src_lbl = "Claude AI" if source == "claude" else "샘플 데이터"
    src_cls = "src-live"  if source == "claude" else "src-samp"
    src_dot = "sdl"       if source == "claude" else "sds"
    sc_keys = [("market_potential","상권잠재력"),("growth_momentum","성장모멘텀"),("entry_fit","입점적합도")]

    # 헤더
    sc_html = "".join(
        f'<div class="ascore"><div class="sv">{scores.get(k,"—")}</div>'
        f'<div class="sl">{lbl}</div></div>'
        for k, lbl in sc_keys
    )
    st.markdown(
        f'<div class="ai-head">'
        f'<div class="ai-ic">AI</div>'
        f'<div class="ai-ht"><h3>{sido} AI 종합 상권 분석</h3>'
        f'<p>거시경제 · 인구 · 키워드 · 뉴스 종합</p></div>'
        f'<div style="display:flex;gap:5px;margin-left:auto">{sc_html}</div>'
        f'<span class="src-badge {src_cls}" style="margin-left:8px">'
        f'<div class="src-dot {src_dot}"></div>{src_lbl}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 인사이트 + 제언
    ins_map = {"opportunity":("ig","↑"), "caution":("ir","!")}
    p_map   = {"high":("rth","최우선"), "medium":("rtm","중요"), "low":("rtl","참고")}

    ins_html = '<div class="ai-sec">핵심 인사이트</div>'
    for ins in analysis.get("insights",[]):
        ic, icon = ins_map.get(ins.get("type","opportunity"), ("ib","·"))
        ins_html += (f'<div class="irow"><div class="iic {ic}">{icon}</div>'
                     f'<div><div class="ih">{ins.get("title","")}</div>'
                     f'<div class="id">{ins.get("body","")}</div></div></div>')

    rec_html = '<div class="ai-sec">전략적 제언</div>'
    for i, rec in enumerate(analysis.get("recommendations",[])):
        cls, lbl = p_map.get(rec.get("priority","medium"), ("rtm","중요"))
        rec_html += (f'<div class="rrow"><span class="rnum">{i+1}</span>'
                     f'<span class="rtext">{rec.get("action","")}</span>'
                     f'<span class="rtag {cls}">{lbl}</span></div>')

    st.markdown(
        f'<div class="ai-body">'
        f'<div class="ai-col">{ins_html}</div>'
        f'<div class="ai-col">{rec_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if analysis.get("summary"):
        st.markdown(f'<div class="ai-sum">{analysis["summary"]}</div>', unsafe_allow_html=True)


def draw_korea_svg(selected: str = "") -> str:
    """한국 시·도 SVG 지도 — 소매판매지수 히트맵."""
    summary = load_summary()
    r_map   = {s["sido"]: s["retail_index"] for s in summary}
    vals    = list(r_map.values())
    mn, mx  = min(vals), max(vals)

    def color(t):
        r = int(180 + (26 - 180) * t)
        g = int(200 + (126 - 200) * t)
        b = int(230 + (58 - 230) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    regions = [
        {"id":"경기", "x":108,"y":148,"w":54,"h":60,"rx":8},
        {"id":"강원", "x":166,"y":118,"w":58,"h":74,"rx":8},
        {"id":"충북", "x":152,"y":194,"w":38,"h":40,"rx":6},
        {"id":"충남", "x":104,"y":200,"w":46,"h":44,"rx":6},
        {"id":"경북", "x":162,"y":196,"w":54,"h":68,"rx":8},
        {"id":"전북", "x":108,"y":248,"w":44,"h":40,"rx":6},
        {"id":"경남", "x":152,"y":276,"w":68,"h":50,"rx":8},
        {"id":"전남", "x": 98,"y":290,"w":56,"h":60,"rx":8},
        {"id":"제주", "x":114,"y":358,"w":50,"h":28,"rx":8},
        {"id":"서울", "x":118,"y":155,"w":24,"h":18,"rx":6},
        {"id":"인천", "x": 88,"y":172,"w":28,"h":20,"rx":6},
        {"id":"대전", "x":150,"y":232,"w":22,"h":18,"rx":6},
        {"id":"세종", "x":136,"y":224,"w":16,"h":14,"rx":4},
        {"id":"광주", "x":130,"y":290,"w":22,"h":18,"rx":6},
        {"id":"대구", "x":188,"y":253,"w":24,"h":18,"rx":6},
        {"id":"울산", "x":214,"y":264,"w":20,"h":18,"rx":6},
        {"id":"부산", "x":200,"y":295,"w":26,"h":20,"rx":6},
    ]

    parts = []
    for r in regions:
        rid  = r["id"]
        ok   = rid in SAMPLE_DB
        sel  = rid == selected
        rv   = r_map.get(rid, mn)
        t    = (rv - mn) / max(mx - mn, 1)
        fill = "#e08020" if sel else (color(t) if ok else "#c8d8e8")
        sw   = "2.5" if sel else "1.2"
        sc   = "#0f2d52" if sel else "#fff"
        cur  = "pointer" if ok else "default"
        fs   = 10 if r["w"] > 36 else 9
        fw   = "700" if sel else "500"
        tc   = "#fff" if sel else "#334155"
        cx, cy = r["x"] + r["w"]//2, r["y"] + r["h"]//2
        parts.append(
            f'<rect x="{r["x"]}" y="{r["y"]}" width="{r["w"]}" height="{r["h"]}" '
            f'rx="{r["rx"]}" fill="{fill}" stroke="{sc}" stroke-width="{sw}" '
            f'style="cursor:{cur}" data-sido="{rid}"/>'
            f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" '
            f'fill="{tc}" font-size="{fs}" font-weight="{fw}" '
            f'font-family="Apple SD Gothic Neo,Malgun Gothic,sans-serif" '
            f'pointer-events="none">{rid}</text>'
        )

    return (
        '<svg viewBox="78 108 166 288" xmlns="http://www.w3.org/2000/svg" '
        'width="100%" style="background:#eef5ff;border-radius:8px">'
        '<rect x="78" y="108" width="166" height="288" fill="#eef5ff"/>'
        + "".join(parts) + "</svg>"
    )


# ══════════════════════════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div style="padding:12px 0 8px">'
        '<div style="font-size:15px;font-weight:700;color:#fff;margin-bottom:3px">📊 AI 지역분석 시스템</div>'
        '<div style="font-size:10px;color:rgba(255,255,255,.4)">영업기획팀 · Regional Intelligence</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    page = st.radio("메뉴", [
        "🗺  지역 분석 대시보드",
        "📋  기획서 개요",
        "⚙️  시스템 설정",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown(
        '<div style="font-size:10px;color:rgba(255,255,255,.4);margin-bottom:5px;'
        'text-transform:uppercase;letter-spacing:.06em">API 연동 상태</div>',
        unsafe_allow_html=True,
    )
    for name, key in [
        (f"KOSIS ({KOSIS_KEY[:8]}...)" if KOSIS_KEY else "KOSIS 통계청", KOSIS_KEY),
        ("네이버 트렌드",  NAVER_ID),
        ("Claude AI",      ANTHROPIC_KEY),
    ]:
        dot = "🟢" if key else "⚪"
        st.markdown(
            f'<div style="font-size:11px;margin-bottom:3px">{dot} {name} '
            f'<span style="color:rgba(255,255,255,.35);font-size:10px">'
            f'{"연동" if key else "미연동(샘플)"}</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown("---")
    st.markdown(
        '<div style="font-size:10px;color:rgba(255,255,255,.3);line-height:1.6">'
        'API 미설정 시 샘플 데이터로 동작<br>.env 파일에 키 입력</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════
# 페이지: 지역 분석 대시보드
# ══════════════════════════════════════════════════════════════════════════
if "지역 분석" in page:

    now = datetime.now().strftime("%Y.%m.%d %H:%M")
    st.markdown(f"""
    <div class="cover">
      <h1>AI 지역 거시환경 자동 분석 시스템</h1>
      <p>통계청 KOSIS · 네이버 트렌드 · Claude AI 실시간 종합 분석</p>
      <div class="cmeta">
        <div><div class="cml">제공팀</div><div class="cmv">영업기획팀</div></div>
        <div><div class="cml">분석 기준</div><div class="cmv">{now}</div></div>
        <div><div class="cml">커버리지</div><div class="cmv">전국 7개 시·도</div></div>
        <div><div class="cml">자동 갱신</div><div class="cmv">3시간 캐시</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 레이아웃: 지도 | 지표+차트 ──
    map_col, right_col = st.columns([1, 2], gap="medium")

    with map_col:
        st.markdown("**지역 선택**")
        st.markdown(
            f'<div class="map-bg">{draw_korea_svg(st.session_state.sel_sido or "")}</div>',
            unsafe_allow_html=True,
        )
        # 버튼 그리드
        sido_list = list(SAMPLE_DB.keys())
        for row in [sido_list[i:i+4] for i in range(0, len(sido_list), 4)]:
            bcols = st.columns(len(row))
            for col, sido in zip(bcols, row):
                with col:
                    is_sel = st.session_state.sel_sido == sido
                    if st.button(sido, key=f"b_{sido}", use_container_width=True,
                                 type="primary" if is_sel else "secondary"):
                        st.session_state.sel_sido = sido
                        st.rerun()

    with right_col:
        sido = st.session_state.sel_sido

        if not sido:
            st.markdown(
                '<div style="background:#fff;border:1px solid #dde5f0;border-radius:10px;'
                'padding:36px 20px;text-align:center;color:#94a3b8">'
                '<div style="font-size:28px;margin-bottom:10px">🗺</div>'
                '<div style="font-size:14px;font-weight:500;color:#4a5568;margin-bottom:5px">지역을 선택하세요</div>'
                '<div style="font-size:12px;line-height:1.7">지도 하단 버튼을 클릭하면<br>'
                '거시경제 지표 · 트렌드 키워드 · 뉴스 · AI 종합 분석이 표시됩니다.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### 전국 시·도 현황 요약")
            summary = load_summary()
            df = pd.DataFrame(summary)
            df.columns = ["시·도","소매판매지수","소매판매증감(%)","인구","인구증감(%)"]
            df["인구"]           = df["인구"].apply(lambda x: f"{x/10000:.0f}만명")
            df["소매판매증감(%)"] = df["소매판매증감(%)"].apply(lambda x: f"{x:+.1f}%")
            df["인구증감(%)"]    = df["인구증감(%)"].apply(lambda x: f"{x:+.1f}%")
            st.dataframe(df.set_index("시·도"), use_container_width=True, height=280)

        else:
            with st.spinner(f"{sido} 데이터 수집 중..."):
                d = load_data(sido)

            pop_fmt = f"{d['pop']/10000:.0f}만명"
            st.markdown(
                f"#### {sido} &nbsp;"
                f"<span style='font-size:13px;color:#94a3b8;font-weight:400'>"
                f"인구 {pop_fmt} · GRDP {d['grdp']}조원 · 소비지출 {d['spend_per_capita']}만원/월"
                f"</span>",
                unsafe_allow_html=True,
            )

            # 지표 카드
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("인구수",        pop_fmt,                f"{d['pop_trend']:+.1f}% YoY")
            with c2: st.metric("소매판매지수",  str(d['retail_index']), f"{d['retail_trend']:+.1f}%")
            with c3: st.metric("1인당 소비지출",f"{d['spend_per_capita']}만원")
            with c4: st.metric("GRDP",          f"{d['grdp']}조원")

            # 데이터 출처 배지
            if d.get("sources"):
                r_sources(d["sources"])

            # 차트
            ch1, ch2 = st.columns(2)
            with ch1:
                st.markdown("**소매판매지수 추이 (6개월)**")
                r_retail_chart(d["retail_series"])
            with ch2:
                st.markdown("**연령대별 인구 비중**")
                r_age_chart(d["age_distribution"])

    # ── 하단: 키워드 + 뉴스 ──
    if st.session_state.sel_sido:
        sido = st.session_state.sel_sido
        d    = load_data(sido)
        st.markdown("---")
        k_col, n_col = st.columns(2, gap="medium")

        with k_col:
            st.markdown("**이슈 키워드 · 검색 트렌드**")
            src_badge = "NAVER API" if d.get("sources",{}).get("keywords") == "NAVER" else "샘플"
            st.caption(f"출처: {src_badge}")
            r_tags(d.get("keywords",[]))
            st.markdown("---")
            r_kw_rank(d.get("keywords",[]))

        with n_col:
            st.markdown("**최신 뉴스 · 이슈 동향**")
            st.caption("출처: Google News RSS")
            r_news(d.get("news_items",[]))

        # ── AI 종합 분석 ──
        st.markdown("---")
        with st.spinner(f"{sido} AI 분석 중..."):
            analysis = get_ai_analysis(d)
        r_ai(analysis, sido)

        # 액션 버튼
        st.markdown("")
        ac1, ac2, _ = st.columns([1, 1, 4])
        with ac1:
            if st.button("🔄 데이터 새로고침", use_container_width=True):
                load_data.clear()
                st.rerun()
        with ac2:
            if st.button("🤖 AI 재분석", use_container_width=True):
                load_data.clear()
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# 페이지: 기획서 개요
# ══════════════════════════════════════════════════════════════════════════
elif "기획서" in page:
    st.markdown("""
    <div class="cover">
      <h1>AI 지역 거시환경 자동 분석 시스템 기획서</h1>
      <p>영업기획팀 AI 효율화 프로젝트 — 주 36시간 수작업 → AI 자동화</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    cards = [
        ("cr","문제","36h","#9b1c1c","1인당 주 4시간 이상 수작업 수집·분석. 팀 전체 주 36시간 낭비."),
        ("cb","솔루션","3단계","#1a56a0","AI가 KOSIS·트렌드·뉴스를 자동 수집. 드릴다운 대시보드 제공."),
        ("cg","기대효과","↓90%","#1b6e3a","분석 소요시간 90% 단축, 전국 17개 광역시도 커버."),
    ]
    for col, (cls, lbl, num, color, txt) in zip([c1,c2,c3], cards):
        with col:
            st.markdown(
                f'<div class="card {cls}">'
                f'<div style="font-size:10px;font-weight:700;color:{color};'
                f'text-transform:uppercase;letter-spacing:.08em;margin-bottom:5px">{lbl}</div>'
                f'<div style="font-size:30px;font-weight:700;color:{color};line-height:1;margin-bottom:7px">{num}</div>'
                f'<div style="font-size:12px;color:#1a2332;line-height:1.6">{txt}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("#### KPI 목표")
    kpi = [
        ("분석 소요시간 절감","1인 주 4시간","1인 주 24분 (↓90%)","팀원 작업일지"),
        ("팀 전체 절감 시간","주 36시간","주 3.6시간 (32.4h 절감)","시스템 로그"),
        ("업데이트 주기","주 1~2회 수작업","매일 자동 갱신","스케줄러 로그"),
        ("분석 커버 지역","2~3개/담당","전국 17개 광역시도","대시보드 탭"),
        ("보고서 작성 시간","보고서당 3시간","보고서당 1시간 이내","착수~완료 측정"),
    ]
    st.dataframe(
        pd.DataFrame(kpi, columns=["KPI","현재","목표","측정방식"]).set_index("KPI"),
        use_container_width=True,
    )

    st.markdown("#### 8주 실행 계획")
    ms = [
        ("1–2주차","기반 설계","#2e7dd4",["요구사항 정의","데이터 소스 확정","API 검증","와이어프레임"]),
        ("3–4주차","MVP 개발","#1b6e3a",["KOSIS API 수집","AI 키워드 추출","대시보드 프로토타입","파일럿"]),
        ("5–6주차","고도화","#c47a00",  ["전국 확대","트렌드 연동","드릴다운 완성","검증"]),
        ("7–8주차","운영 전환","#7c3aed",["팀 교육","기존 방식 전환","KPI 측정","개선"]),
    ]
    for col, (week, title, color, items) in zip(st.columns(4), ms):
        with col:
            li = "".join(f"<li style='padding:3px 0;border-bottom:1px solid #f0f4f8;font-size:12px;color:#64748b'>{it}</li>" for it in items)
            st.markdown(
                f'<div class="card" style="border-top:3px solid {color}">'
                f'<div style="font-size:10px;font-weight:700;color:{color};'
                f'text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">{week}</div>'
                f'<div style="font-size:13px;font-weight:700;color:#0f2d52;margin-bottom:7px">{title}</div>'
                f'<ul style="list-style:none;padding:0;margin:0">{li}</ul></div>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════
# 페이지: 시스템 설정
# ══════════════════════════════════════════════════════════════════════════
elif "설정" in page:
    st.markdown("""
    <div class="cover">
      <h1>시스템 설정</h1>
      <p>API 키 관리 · 캐시 · 데이터 수집 스케줄</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### API 연동 현황")
    api_info = [
        ("KOSIS 통계청 Open API", KOSIS_KEY,   "https://kosis.kr/openapi/",          "인구·소매판매·GRDP·실업률"),
        ("네이버 데이터랩 트렌드", NAVER_ID,   "https://developers.naver.com/",       "검색 트렌드 키워드 순위"),
        ("Anthropic Claude API",  ANTHROPIC_KEY,"https://console.anthropic.com/",    "AI 종합 상권 분석 생성"),
    ]
    for name, key, url, desc in api_info:
        status = "✅ 연동됨" if key else "⚪ 미연동"
        color  = "#1b6e3a" if key else "#94a3b8"
        st.markdown(
            f'<div class="card">'
            f'<div style="display:flex;align-items:center;justify-content:space-between">'
            f'<div><div style="font-size:13px;font-weight:500;color:#0f2d52">{name}</div>'
            f'<div style="font-size:11px;color:#64748b;margin-top:2px">{desc}</div></div>'
            f'<div style="font-size:12px;font-weight:500;color:{color}">{status}</div></div>'
            f'<div style="font-size:11px;color:#94a3b8;margin-top:7px">발급: <a href="{url}" style="color:#2e7dd4">{url}</a></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("#### .env 설정")
    st.markdown('<div class="hl">프로젝트 루트에 .env 파일을 생성하고 아래와 같이 입력하세요.</div>', unsafe_allow_html=True)
    st.code("""KOSIS_API_KEY=MzM5MjgyYTRlNWVlMGFiMjY1MmRmNGMxZmJiZjAwMDk=
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_secret
CACHE_TTL_SECONDS=10800""", language="bash")

    st.markdown("#### 캐시 관리")
    cc1, cc2 = st.columns(2)
    with cc1:
        if st.button("🗑️ 전체 캐시 삭제", use_container_width=True):
            load_data.clear()
            st.success("캐시가 삭제되었습니다.")
    with cc2:
        from pathlib import Path
        n = len(list(Path(".cache").glob("*.json"))) if Path(".cache").exists() else 0
        st.info(f"현재 캐시 파일: {n}개")

    st.markdown("#### 자동 갱신 스케줄러")
    st.code("""# scheduler.py — 매일 새벽 3시 자동 갱신
import schedule, time
from data_collector import get_sido_data, SAMPLE_DB

def refresh_all():
    print(f"갱신 시작: {__import__('datetime').datetime.now()}")
    for sido in SAMPLE_DB.keys():
        get_sido_data(sido)
        print(f"  ✅ {sido}")

schedule.every().day.at("03:00").do(refresh_all)
while True:
    schedule.run_pending()
    time.sleep(60)""", language="python")
