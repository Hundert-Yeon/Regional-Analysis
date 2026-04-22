"""
data_collector.py  —  통계청 KOSIS API + 네이버 트렌드 + 뉴스 RSS 수집 모듈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
연동 통계표  (KOSIS API)
  DT_1B04005N  주민등록인구현황   orgId=101  prdSe=M
  DT_1KA3010   소매판매액지수     orgId=101  prdSe=M
  DT_1C65      지역내총생산GRDP  orgId=101  prdSe=Y
  DT_1DE7107S  고용통계 실업률    orgId=101  prdSe=M

KOSIS API 키 미설정 또는 네트워크 오류 시 샘플 데이터로 자동 폴백.
"""

import os, json, time, hashlib, random, requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── 환경변수 ──────────────────────────────────────────────────────────────
KOSIS_KEY  = os.getenv("KOSIS_API_KEY",        "")
NAVER_ID   = os.getenv("NAVER_CLIENT_ID",       "")
NAVER_SEC  = os.getenv("NAVER_CLIENT_SECRET",   "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY",  "")
CACHE_TTL  = int(os.getenv("CACHE_TTL_SECONDS", "10800"))

KOSIS_BASE = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
CACHE_DIR  = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

# ── 시도 코드 ──────────────────────────────────────────────────────────────
SIDO_CODE = {
    "서울":"11","부산":"21","대구":"22","인천":"23","광주":"24",
    "대전":"25","울산":"26","세종":"29","경기":"31","강원":"32",
    "충북":"33","충남":"34","전북":"35","전남":"36","경북":"37",
    "경남":"38","제주":"39",
}

# ── 캐시 ──────────────────────────────────────────────────────────────────
def _cp(key):
    return CACHE_DIR / f"{hashlib.md5(key.encode()).hexdigest()}.json"

def _cget(key):
    p = _cp(key)
    if not p.exists(): return None
    try:
        d = json.loads(p.read_text("utf-8"))
        if time.time() - d["ts"] < CACHE_TTL: return d["payload"]
    except: pass
    return None

def _cset(key, payload):
    _cp(key).write_text(
        json.dumps({"ts": time.time(), "payload": payload}, ensure_ascii=False), "utf-8")

# ── KOSIS 공통 호출 ───────────────────────────────────────────────────────
def _kosis(extra: dict, cache_key: str) -> Optional[list]:
    cached = _cget(cache_key)
    if cached is not None: return cached
    if not KOSIS_KEY: return None
    try:
        r = requests.get(KOSIS_BASE, params={
            "method":"getList","apiKey":KOSIS_KEY,"format":"json","jsonVD":"Y",**extra
        }, timeout=10)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and ("err" in data or "errMsg" in data): return None
        if isinstance(data, list) and data:
            _cset(cache_key, data)
            return data
    except: pass
    return None

def _period(months: int = 7):
    e = datetime.now(); s = e - timedelta(days=30*months)
    return s.strftime("%Y%m"), e.strftime("%Y%m")

# ── ① 인구 ───────────────────────────────────────────────────────────────
def fetch_population(sido: str) -> Optional[dict]:
    code = SIDO_CODE.get(sido)
    if not code: return None
    s, e = _period(14)
    data = _kosis({"orgId":"101","tblId":"DT_1B04005N","itmId":"T2",
                   "objL1":code,"prdSe":"M","startPrdDe":s,"endPrdDe":e},
                  f"pop_{sido}_{e}")
    if not data: return None
    try:
        rows = sorted(data, key=lambda x: x.get("PRD_DE",""))
        lat  = rows[-1]
        now  = int(float(lat.get("DT",0)))
        prd  = lat.get("PRD_DE","")
        ppr  = str(int(prd[:4])-1)+prd[4:]
        prev_r = [r for r in rows if r.get("PRD_DE")==ppr]
        prev = int(float(prev_r[0].get("DT",now))) if prev_r else now
        trend = round((now-prev)/max(prev,1)*100,2)
        monthly = [{"period":r.get("PRD_DE",""),"value":int(float(r.get("DT",0)))}
                   for r in rows if r.get("DT")][-7:]
        return {"population":now,"pop_trend":trend,"monthly":monthly,"period":prd,"source":"KOSIS"}
    except: return None

# ── ② 소매판매지수 ────────────────────────────────────────────────────────
def fetch_retail(sido: str) -> Optional[dict]:
    code = SIDO_CODE.get(sido,"23")
    s, e = _period(8)
    data = _kosis({"orgId":"101","tblId":"DT_1KA3010","itmId":"T",
                   "objL1":code,"prdSe":"M","startPrdDe":s,"endPrdDe":e},
                  f"retail_{sido}_{e}")
    if not data:  # 전국 폴백
        data = _kosis({"orgId":"101","tblId":"DT_1KA3010","itmId":"T",
                       "objL1":"0","prdSe":"M","startPrdDe":s,"endPrdDe":e},
                      f"retail_national_{e}")
    if not data: return None
    try:
        rows  = sorted(data, key=lambda x: x.get("PRD_DE",""))
        lat   = rows[-1]
        cur   = float(lat.get("DT",0))
        prev  = float(rows[-2].get("DT",cur)) if len(rows)>=2 else cur
        trend = round((cur-prev)/max(prev,1)*100,2)
        monthly = [{"period":r.get("PRD_DE",""),"value":round(float(r.get("DT",0)),1)}
                   for r in rows if r.get("DT")][-7:]
        return {"retail_index":round(cur,1),"retail_trend":trend,
                "monthly":monthly,"period":lat.get("PRD_DE",""),"source":"KOSIS"}
    except: return None

# ── ③ GRDP ───────────────────────────────────────────────────────────────
def fetch_grdp(sido: str) -> Optional[dict]:
    code = SIDO_CODE.get(sido)
    if not code: return None
    yr = datetime.now().year
    data = _kosis({"orgId":"101","tblId":"DT_1C65","itmId":"TQ",
                   "objL1":code,"prdSe":"Y",
                   "startPrdDe":str(yr-4),"endPrdDe":str(yr-1)},
                  f"grdp_{sido}_{yr}")
    if not data: return None
    try:
        lat = sorted(data, key=lambda x: x.get("PRD_DE",""))[-1]
        return {"grdp":round(float(lat.get("DT",0))/1000,1),
                "year":lat.get("PRD_DE",""),"source":"KOSIS"}
    except: return None

# ── ④ 실업률 ─────────────────────────────────────────────────────────────
def fetch_unemployment(sido: str) -> Optional[dict]:
    code = SIDO_CODE.get(sido)
    if not code: return None
    s, e = _period(4)
    data = _kosis({"orgId":"101","tblId":"DT_1DE7107S","itmId":"T10",
                   "objL1":code,"prdSe":"M","startPrdDe":s,"endPrdDe":e},
                  f"unemp_{sido}_{e}")
    if not data: return None
    try:
        lat = sorted(data, key=lambda x: x.get("PRD_DE",""))[-1]
        return {"unemployment":round(float(lat.get("DT",0)),1),
                "period":lat.get("PRD_DE",""),"source":"KOSIS"}
    except: return None

# ── 네이버 트렌드 ─────────────────────────────────────────────────────────
def fetch_naver_trends(keywords: list, sido: str) -> Optional[dict]:
    if not (NAVER_ID and NAVER_SEC): return None
    ck = f"naver_{sido}_{'_'.join(keywords[:3])}"
    cached = _cget(ck)
    if cached: return cached
    try:
        e = datetime.now().strftime("%Y-%m-%d")
        s = (datetime.now()-timedelta(days=90)).strftime("%Y-%m-%d")
        r = requests.post("https://openapi.naver.com/v1/datalab/search",
            json={"startDate":s,"endDate":e,"timeUnit":"week",
                  "keywordGroups":[{"groupName":kw,"keywords":[kw]} for kw in keywords[:5]]},
            headers={"X-Naver-Client-Id":NAVER_ID,"X-Naver-Client-Secret":NAVER_SEC,
                     "Content-Type":"application/json"},timeout=8)
        r.raise_for_status()
        result = r.json()
        _cset(ck, result)
        return result
    except: return None

# ── 뉴스 RSS ─────────────────────────────────────────────────────────────
def fetch_news_rss(sido: str) -> list:
    ck = f"news_{sido}"
    cached = _cget(ck)
    if cached: return cached
    articles = []
    for q in [f"{sido}+소비+상권", f"{sido}+경제+개발"]:
        try:
            r = requests.get(
                f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko",
                timeout=6, headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.content)
                for item in root.findall(".//item")[:5]:
                    t = item.findtext("title","")
                    if t:
                        articles.append({"title":t,
                                         "pubDate":item.findtext("pubDate","")[:16],
                                         "link":item.findtext("link","#")})
        except: pass
    if articles: _cset(ck, articles)
    return articles

# ── 샘플 데이터 ───────────────────────────────────────────────────────────
SAMPLE_DB = {
    "서울": {"pop":9_410_000,"pop_trend":-0.4,"grdp":480.0,
             "retail_index":118.7,"retail_trend":+1.5,
             "spend_per_capita":234,"unemployment":3.1,
             "keywords":["성수 팝업","강남 명품","2030 소비회복","외국인 관광객","한남 플래그십"],
             "news_topics":["성수동 상권 급성장","강남 럭셔리 소비 확대","MZ 팝업 트렌드 지속"]},
    "인천": {"pop":2_990_000,"pop_trend":+0.8,"grdp":89.2,
             "retail_index":112.4,"retail_trend":+2.1,
             "spend_per_capita":198,"unemployment":3.4,
             "keywords":["크루즈 관광객","인천공항 면세","송도 팝업","외국인 소비↑","오마카세 급부상"],
             "news_topics":["인천 크루즈 기항 증가","송도 국제도시 상권 성장","인천공항 면세점 확장"]},
    "부산": {"pop":3_320_000,"pop_trend":-0.6,"grdp":98.5,
             "retail_index":108.3,"retail_trend":-0.8,
             "spend_per_capita":186,"unemployment":3.8,
             "keywords":["해운대 관광시즌","북항 재개발","서면 상권 회복","전포 카페거리","씨푸드 관광"],
             "news_topics":["해운대 관광객 증가","북항 재개발 착공","전포 MZ 상권 부상"]},
    "대구": {"pop":2_360_000,"pop_trend":-0.9,"grdp":56.2,
             "retail_index":104.1,"retail_trend":+0.5,
             "spend_per_capita":172,"unemployment":4.1,
             "keywords":["동성로 상권 부활","수성못 카페","청년 창업↑","섬유산업 침체","학군 수요"],
             "news_topics":["동성로 팝업 문화 확산","수성구 프리미엄 소비 증가","대구 청년 창업 지원"]},
    "광주": {"pop":1_430_000,"pop_trend":-0.3,"grdp":38.7,
             "retail_index":106.8,"retail_trend":+1.2,
             "spend_per_capita":168,"unemployment":3.6,
             "keywords":["비엔날레 시즌","양림동 카페","친환경 소비↑","문화예술 행사","로컬 감성"],
             "news_topics":["광주 비엔날레 관광객 증가","양림동 카페거리 전국 인지도","국립아시아문화전당 행사"]},
    "대전": {"pop":1_460_000,"pop_trend":-0.1,"grdp":39.4,
             "retail_index":109.2,"retail_trend":+1.4,
             "spend_per_capita":182,"unemployment":3.3,
             "keywords":["대덕특구 R&D","궁동 카페거리","청년 스타트업","은행동 상권","충청권 허브"],
             "news_topics":["대덕특구 R&D 투자 확대","대전 KTX 역세권 개발","청년 창업 클러스터"]},
    "경기": {"pop":13_800_000,"pop_trend":+0.9,"grdp":532.0,
             "retail_index":115.2,"retail_trend":+2.3,
             "spend_per_capita":218,"unemployment":3.0,
             "keywords":["GTX 개통 효과","판교 IT 클러스터","신도시 소비","수도권 확장","MZ 카페 급증"],
             "news_topics":["GTX-A 개통 역세권 상권 활성화","판교 테크노밸리 소비 증가","신도시 생활 인프라"]},
}

def _series(sido, base):
    rng = random.Random(sum(ord(c) for c in sido)+1)
    m   = ["10월","11월","12월","1월","2월","3월","4월"]
    v   = [round(base-4+i*0.85+(rng.random()-.5)*1.2,1) for i in range(7)]
    return {"labels":m,"values":v}

def _age(sido):
    bm = {"서울":[10,18,26,26,20],"인천":[12,15,28,24,21],"부산":[11,14,22,26,27],
          "대구":[11,13,21,27,28],"광주":[12,15,23,26,24],"대전":[12,16,25,26,21],
          "경기":[13,16,28,24,19]}
    rng  = random.Random(sum(ord(c) for c in sido)+2)
    base = bm.get(sido,[12,15,25,26,22])
    n    = [max(1,v+rng.randint(-1,1)) for v in base]
    t    = sum(n)
    return {"labels":["10대","20대","30대","40대","50대+"],
            "values":[round(v/t*100,1) for v in n]}

# ── 메인 수집 ─────────────────────────────────────────────────────────────
def get_sido_data(sido: str) -> dict:
    base   = SAMPLE_DB.get(sido, SAMPLE_DB["인천"]).copy()
    result = base.copy()
    src    = {}

    # 인구
    pd = fetch_population(sido)
    if pd:
        result["pop"]       = pd["population"]
        result["pop_trend"] = pd["pop_trend"]
        src["pop"]          = f"KOSIS ({pd.get('period','')})"
        if pd.get("monthly"):
            km = ["10월","11월","12월","1월","2월","3월","4월"]
            m  = pd["monthly"][-7:]
            result["pop_series"] = {"labels":[km[i] if i<7 else d["period"] for i,d in enumerate(m)],
                                    "values":[d["value"] for d in m]}
    else:
        src["pop"] = "sample"

    # 소매판매지수
    rd = fetch_retail(sido)
    if rd:
        result["retail_index"] = rd["retail_index"]
        result["retail_trend"] = rd["retail_trend"]
        src["retail"]          = f"KOSIS ({rd.get('period','')})"
        if rd.get("monthly") and len(rd["monthly"])>=3:
            km = ["10월","11월","12월","1월","2월","3월","4월"]
            m  = rd["monthly"][-7:]
            result["retail_series"] = {"labels":[km[i] if i<7 else d["period"] for i,d in enumerate(m)],
                                       "values":[d["value"] for d in m]}
    else:
        src["retail"] = "sample"

    # GRDP
    gd = fetch_grdp(sido)
    if gd:
        result["grdp"] = gd["grdp"]
        src["grdp"]    = f"KOSIS ({gd.get('year','')})"
    else:
        src["grdp"] = "sample"

    # 실업률
    ud = fetch_unemployment(sido)
    if ud:
        result["unemployment"] = ud["unemployment"]
        src["unemployment"]    = f"KOSIS ({ud.get('period','')})"
    else:
        src["unemployment"] = "sample"

    # 네이버 트렌드
    nv = fetch_naver_trends(base.get("keywords",[])[:5], sido)
    if nv and nv.get("results"):
        try:
            ranked = sorted(nv["results"],
                           key=lambda x: sum(p.get("ratio",0) for p in x.get("data",[])),
                           reverse=True)
            result["keywords"] = [r["title"] for r in ranked]
            src["keywords"]    = "NAVER"
        except:
            src["keywords"] = "sample"
    else:
        src["keywords"] = "sample"

    # 뉴스
    news = fetch_news_rss(sido)
    if news:
        result["news_items"] = news[:6]
        src["news"]          = "Google RSS"
    else:
        result["news_items"] = [{"title":t,"pubDate":"","link":"#"}
                                for t in base.get("news_topics",[])]
        src["news"] = "sample"

    # 보조 데이터
    if "retail_series" not in result:
        result["retail_series"] = _series(sido, result["retail_index"])
    result["age_distribution"] = _age(sido)
    result["sources"]          = src
    result["updated_at"]       = datetime.now().strftime("%Y-%m-%d %H:%M")
    result["sido"]             = sido
    return result

def get_all_sido_summary() -> list:
    return [{"sido":s,"retail_index":d["retail_index"],"retail_trend":d["retail_trend"],
             "pop":d["pop"],"pop_trend":d["pop_trend"]} for s,d in SAMPLE_DB.items()]
