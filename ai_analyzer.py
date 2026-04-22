"""
ai_analyzer.py  —  Claude AI 상권 분석 모듈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTHROPIC_API_KEY 설정 시 → Claude 실시간 분석
미설정 시 → 시도별 사전 작성 샘플 분석 반환
"""

import os, json
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY","")

# ── 프롬프트 빌더 ─────────────────────────────────────────────────────────
def _build_prompt(data: dict) -> str:
    sido    = data.get("sido","")
    pop     = data.get("pop", 0)
    pop_t   = data.get("pop_trend", 0)
    grdp    = data.get("grdp", 0)
    retail  = data.get("retail_index", 0)
    rt      = data.get("retail_trend", 0)
    spend   = data.get("spend_per_capita", 0)
    unemp   = data.get("unemployment", 0)
    kws     = data.get("keywords", [])
    news    = data.get("news_items", [])
    age     = data.get("age_distribution", {})

    age_str = ""
    if age:
        pairs   = list(zip(age.get("labels",[]), age.get("values",[])))
        dom     = max(pairs, key=lambda x: x[1]) if pairs else ("",0)
        age_str = f"연령대 분포: {', '.join(f'{l} {v}%' for l,v in pairs)}. 주 소비층: {dom[0]} ({dom[1]}%)"

    news_str = "\n".join(f"- {n['title']}" for n in news[:5]) if news else "없음"
    kw_str   = ", ".join(kws[:6]) if kws else "없음"

    return f"""당신은 대형 유통백화점 MD 전략 전문 AI입니다.
아래 {sido} 지역 데이터를 분석해 상권 분석 보고서를 JSON으로만 작성하세요.
JSON 외 다른 텍스트는 절대 포함하지 마세요.

## 입력 데이터
- 인구: {pop:,}명 (YoY {pop_t:+.1f}%)
- GRDP: {grdp}조원
- 소매판매지수: {retail} (전월 대비 {rt:+.1f}%)
- 1인당 소비지출: {spend}만원/월
- 실업률: {unemp}%
- {age_str}
- 검색 트렌드: {kw_str}
- 최신 뉴스:
{news_str}

## 출력 형식 (JSON만)
{{
  "scores": {{
    "market_potential": "A+",
    "growth_momentum": "B+",
    "entry_fit": "A"
  }},
  "insights": [
    {{"type":"opportunity","title":"제목(15자이내)","body":"내용(80자이내,수치포함)"}},
    {{"type":"caution",   "title":"제목","body":"내용"}},
    {{"type":"opportunity","title":"제목","body":"내용"}},
    {{"type":"caution",   "title":"제목","body":"내용"}}
  ],
  "recommendations": [
    {{"priority":"high",  "action":"전략(40자이내)"}},
    {{"priority":"high",  "action":"전략"}},
    {{"priority":"medium","action":"전략"}},
    {{"priority":"low",   "action":"전략"}}
  ],
  "summary": "종합 요약 (150자이내, 핵심 3가지 포함)"
}}

scores 등급: S > A+ > A > B+ > B > B- > C
type: opportunity(기회) / caution(주의)
priority: high(최우선) / medium(중요) / low(참고)"""


def analyze_with_claude(data: dict) -> Optional[dict]:
    if not ANTHROPIC_KEY:
        return None
    import urllib.request, urllib.error
    payload = json.dumps({
        "model":      "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages":   [{"role":"user","content":_build_prompt(data)}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={"Content-Type":"application/json",
                 "x-api-key":ANTHROPIC_KEY,
                 "anthropic-version":"2023-06-01"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            text   = result["content"][0]["text"].strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"): text = text[4:]
                text = text.strip()
            return json.loads(text)
    except:
        return None


# ── 샘플 분석 ─────────────────────────────────────────────────────────────
_SAMPLE = {
    "서울": {
        "scores":{"market_potential":"S","growth_momentum":"A+","entry_fit":"A+"},
        "insights":[
            {"type":"opportunity","title":"팝업 성지 집객력 최고",
             "body":"성수·한남 상권 팝업 전환율 전국 1위. 단기 팝업 ROI가 장기 매장 대비 2.3배 높음."},
            {"type":"opportunity","title":"강남 명품 소비 재개",
             "body":"외국인 관광객 회복·강남 소비층 명품 지출 재개로 고단가 MD 확충 적기."},
            {"type":"caution","title":"인구 감소 지속",
             "body":"서울 인구 -0.4% 지속. 교통 연계성·접근성이 입점 성패 핵심 변수."},
            {"type":"caution","title":"상권 밀도 경쟁 심화",
             "body":"동일 상권 내 브랜드 과밀화로 차별화 포인트 없는 입점은 수익성 확보 어려움."},
        ],
        "recommendations":[
            {"priority":"high",  "action":"성수·한남 팝업 스토어 우선 입점 (브랜드 인지도 극대화)"},
            {"priority":"high",  "action":"강남구 명품·고단가 MD 라인업 강화"},
            {"priority":"medium","action":"홍대·마포 MZ 특화 체험형 공간 기획"},
            {"priority":"low",   "action":"인구 감소 대비 집객력 높은 거점 상권 집중"},
        ],
        "summary":"서울은 성수·한남·강남 3대 핵심 상권이 각각 MZ 팝업, 명품 소비, 고단가 F&B 주도. 팝업 중심 경험 마케팅과 플래그십 브랜드 위상 강화 병행으로 단기 집객과 장기 충성 고객을 동시 확보해야 합니다.",
    },
    "인천": {
        "scores":{"market_potential":"A+","growth_momentum":"B+","entry_fit":"A"},
        "insights":[
            {"type":"opportunity","title":"프리미엄 F&B 수요 급증",
             "body":"외국인 거주율 증가(+0.9%p)·국제업무지구 직장인 유입으로 오마카세 검색 전월 대비 38% 급등."},
            {"type":"opportunity","title":"크루즈 집객 연계 기회",
             "body":"2026년 인천항 크루즈 기항 80회 이상 예정. 외국인 쇼핑 수요 포착 위한 면세 연계 MD 시급."},
            {"type":"caution","title":"구도심 양극화 심화",
             "body":"부평·미추홀 구도심 소매판매지수 하락 지속. 신도시 집중과 균형 전략 필요."},
            {"type":"caution","title":"외국인 의존도 리스크",
             "body":"외국인 관광객 변동성 높아 내국인 로컬 소비 기반도 병행 육성해야 수익 안정성 확보."},
        ],
        "recommendations":[
            {"priority":"high",  "action":"파인다이닝·오마카세 MD 확충 (연수구 우선)"},
            {"priority":"high",  "action":"크루즈 시즌 연계 외국인 특화 팝업 기획"},
            {"priority":"medium","action":"청라·송도 신규 입점 우선 검토"},
            {"priority":"low",   "action":"구도심 재생 팝업으로 상권 균형 유지"},
        ],
        "summary":"인천은 국제업무지구 확장·크루즈 관광 급증으로 프리미엄 소비 시장 빠르게 형성 중. 연수구·서구 신도시권의 30대 소비층과 외국인 수요를 동시 공략하는 이중 전략이 핵심 과제입니다.",
    },
    "부산": {
        "scores":{"market_potential":"B+","growth_momentum":"B","entry_fit":"B+"},
        "insights":[
            {"type":"opportunity","title":"해운대·북항 집객 인프라",
             "body":"북항 재개발 완료 시 연간 관광객 1,500만 명 이상 기대. F&B·라이프스타일 MD 집중 유치 유효."},
            {"type":"opportunity","title":"전포 카페거리 SNS 집객",
             "body":"전포카페거리 SNS 노출 전국 3위권. 20~30대 팝업·체험형 매장 바이럴 효과 극대화."},
            {"type":"caution","title":"인구 감소 가속화",
             "body":"부산 인구 -0.6% 지속. 로컬 소비 기반 약화로 관광객 소비 대체 전략 전환 시급."},
            {"type":"caution","title":"고령화 심화",
             "body":"50대 이상 27%로 주요 도시 중 최고. 고가 MD 진입 시 초기 반응이 수도권 대비 느림."},
        ],
        "recommendations":[
            {"priority":"high",  "action":"해운대·북항 관광 특화 F&B MD 우선 입점"},
            {"priority":"medium","action":"전포·서면 MZ 팝업으로 브랜드 인지도 확보"},
            {"priority":"medium","action":"씨푸드 컨셉 글로벌 관광객 특화 메뉴 개발"},
            {"priority":"low",   "action":"고령층 친화 서비스·MD 라인 병행 구성"},
        ],
        "summary":"부산은 관광 거점으로 해운대·북항 대규모 집객 인프라 확장 중. 인구 감소 리스크를 관광·크루즈 외래 소비로 상쇄하고 MZ·고령층 이중 MD 구성이 필요합니다.",
    },
    "대구": {
        "scores":{"market_potential":"B","growth_momentum":"B-","entry_fit":"B"},
        "insights":[
            {"type":"opportunity","title":"동성로 MZ 팝업 부활",
             "body":"청년 창업 증가·SNS 팝업 문화 확산으로 동성로 상권 서서히 회복. 저비용 테스트 입점 적기."},
            {"type":"opportunity","title":"수성구 고소득층 집중",
             "body":"수성구 평균 가처분소득 전국 상위권. 프리미엄 카페·파인다이닝 수요 실재."},
            {"type":"caution","title":"인구 감소 가장 빠른 도시",
             "body":"인구 감소율 -0.9%로 주요 도시 중 최고. 단기 수익 전략이 현실적."},
            {"type":"caution","title":"섬유산업 침체 연계 위축",
             "body":"전통 섬유 산업 구조조정으로 40~50대 중산층 소비 여력 감소."},
        ],
        "recommendations":[
            {"priority":"medium","action":"동성로 단기 팝업 테스트 후 반응 기반 입점 결정"},
            {"priority":"medium","action":"수성구 프리미엄 카페·파인다이닝 선점 입점"},
            {"priority":"low",   "action":"섬유·패션 특화 로컬 콜라보 브랜드 기획"},
            {"priority":"low",   "action":"고령층 친화 서비스 중심 MD 구성 검토"},
        ],
        "summary":"대구는 도시 구조 전환기로 단기 팝업·소규모 테스트 입점이 안전한 전략. 수성구 고소득 소비층 타깃 프리미엄과 동성로 MZ 팝업을 이중 활용하는 접근이 효과적입니다.",
    },
    "광주": {
        "scores":{"market_potential":"B","growth_momentum":"B","entry_fit":"B-"},
        "insights":[
            {"type":"opportunity","title":"비엔날레 문화 관광 집객",
             "body":"국립아시아문화전당·비엔날레로 연간 관광객 지속 유입. 문화·예술 컨셉 매장 화제성 높음."},
            {"type":"opportunity","title":"양림동 전국 인지도 급상승",
             "body":"양림동 역사 카페거리 SNS 노출 전년 대비 40% 증가. 로컬 감성 팝업 효과 검증."},
            {"type":"caution","title":"절대 인구 소규모",
             "body":"143만 명 규모로 프리미엄 MD 수익성 확보에 시간 필요."},
            {"type":"caution","title":"소비 인프라 한계",
             "body":"고단가 소비 인프라 부족으로 입점 초기 고객 접점 확보에 시간 소요."},
        ],
        "recommendations":[
            {"priority":"high",  "action":"국립아시아문화전당 연계 문화·예술 팝업 기획"},
            {"priority":"medium","action":"양림동 역사 카페 감성 콜라보 팝업"},
            {"priority":"medium","action":"친환경·로컬 컨셉 브랜드 테스트베드 활용"},
            {"priority":"low",   "action":"광주·전남 광역 상권 허브 입점 추진"},
        ],
        "summary":"광주는 문화·예술 도시 정체성 활용 차별화 전략이 유효. 비엔날레·양림동 로컬 감성 상권의 전국 확산 모멘텀을 활용한 브랜드 테스트베드 가치가 높습니다.",
    },
    "대전": {
        "scores":{"market_potential":"B+","growth_momentum":"B+","entry_fit":"B"},
        "insights":[
            {"type":"opportunity","title":"R&D 특구 기반 고학력 소비",
             "body":"대덕특구 연구원·고학력 직장인 밀집. 스마트·기능성 소비 성향 강해 IT·라이프스타일 MD 적합."},
            {"type":"opportunity","title":"충청권 광역 허브 잠재력",
             "body":"세종·충남·충북 아우르는 충청권 중심 도시. KTX 역세권 상권 선점이 중장기 핵심 과제."},
            {"type":"caution","title":"절대 규모 소규모",
             "body":"146만 명 규모. 세종·충청권 광역 전략으로 접근 시 수익성 확보 가능."},
            {"type":"caution","title":"수도권 쏠림 현상",
             "body":"고학력 인재의 수도권 이직 증가로 핵심 소비층 이탈 리스크 존재."},
        ],
        "recommendations":[
            {"priority":"high",  "action":"KTX 역세권 중심 충청권 허브 입점 검토"},
            {"priority":"medium","action":"R&D 특구 연계 IT·라이프스타일 MD 특화"},
            {"priority":"medium","action":"궁동 대학가 MZ 팝업 브랜드 테스트"},
            {"priority":"low",   "action":"세종·충남 광역 연계 마케팅 전략 수립"},
        ],
        "summary":"대전은 대덕특구 R&D 기반과 충청권 허브 위상 결합한 전략적 요충지. KTX 역세권과 IT·라이프스타일 융합 MD를 중심으로 충청권 전체를 아우르는 광역 입점 전략이 필요합니다.",
    },
    "경기": {
        "scores":{"market_potential":"A","growth_momentum":"A","entry_fit":"A"},
        "insights":[
            {"type":"opportunity","title":"GTX 역세권 신상권 선점",
             "body":"GTX-A·B·C 개통으로 수도권 30분 생활권 확장. 동탄·수원·일산 역세권 선점 ROI 극대화."},
            {"type":"opportunity","title":"판교 IT 직장인 프리미엄",
             "body":"판교 테크노밸리 연평균 소득 상위권 직장인 집중. 고단가 F&B·라이프스타일 수요 검증 완료."},
            {"type":"caution","title":"광역 범위 집중 어려움",
             "body":"1,380만 명이나 지역별 편차 극심. 판교·수원·일산 3대 거점 집중 전략 필요."},
            {"type":"caution","title":"경쟁 포화 신도시 주의",
             "body":"일부 신도시는 입점 포화 상태 접근 중. 선도 입점 타이밍 이미 지난 지역 존재."},
        ],
        "recommendations":[
            {"priority":"high",  "action":"GTX 역세권 신상권 선점 입점 (동탄·수원·일산)"},
            {"priority":"high",  "action":"판교 IT 직장인 프리미엄 F&B·라이프스타일 확충"},
            {"priority":"medium","action":"신도시 MZ 타깃 팝업 마케팅 선공략"},
            {"priority":"low",   "action":"3대 거점(판교·수원·일산) 집중 전략으로 분산 방지"},
        ],
        "summary":"경기는 GTX 개통·신도시 성숙화라는 두 대형 상권 변화가 동시 작용하는 국내 최대 기회 시장. 판교·수원·일산 3대 거점 중심으로 역세권 선점과 IT 직장인 프리미엄 소비 공략이 최우선입니다.",
    },
}

def get_ai_analysis(data: dict) -> dict:
    sido = data.get("sido","")
    if ANTHROPIC_KEY:
        result = analyze_with_claude(data)
        if result:
            result["_source"] = "claude"
            return result
    result = _SAMPLE.get(sido, _SAMPLE["인천"]).copy()
    result["_source"] = "sample"
    return result
