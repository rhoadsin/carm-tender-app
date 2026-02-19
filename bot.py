import os
import requests
import google.generativeai as genai
from datetime import datetime

# 1. 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def fetch_ted_tenders():
    print("Fetching expanded data from TED API...")
    url = "https://ted.europa.eu/api/v3/notices/search"
    
    # 쿼리 수정: 2024년 이후의 모든 의료 영상 장비 공고 중 'arm' 관련 건 검색
    # PD (Publication Date) 범위를 넓혀 과거 데이터까지 가져옵니다.
    query = "(CPV_CODE IN (33111400, 33110000, 33111000) OR CONTENT ~ 'C-ARM') AND PD >= 20240101"
    
    payload = {
        "query": query,
        "limit": 50,  # 더 많은 데이터를 확인하기 위해 한도를 늘림
        "fields": ["publication-number", "content-list", "title", "dt-deadline", "oj-url"],
        "sort-by": ["PD DESC"] # 최신순 정렬
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get('notices', [])
    except Exception as e:
        print(f"Error fetching TED data: {e}")
        return []

def analyze_with_gemini(title, content):
    # Gemini에게 판별 기준을 더 명확히 전달
    prompt = f"""
    당신은 의료기기 입찰 전문 분석가입니다.
    다음 공고가 '수술용 모바일 C-ARM (Surgical Mobile C-ARM)' 장비 구매 관련 건인지 판별하세요.
    - 로봇 팔, 산업용 장비, 단순 부품 교체는 NO입니다.
    - 병원 입찰, Fluoroscopy 시스템, 모바일 X-ray 영상 장비는 YES일 확률이 높습니다.
    답변은 오직 'YES' 또는 'NO'로만 하세요.

    제목: {title}
    내용 요약: {content[:700]}
    """
    try:
        response = model.generate_content(prompt)
        return "YES" in response.text.upper()
    except:
        return False

def generate_html(tenders):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cards_html = ""
    valid_count = 0
    
    for t in tenders:
        title = t.get('title', ['No Title'])[0]
        deadline = t.get('dt-deadline', 'N/A')
        link = t.get('oj-url', '#')
        content_list = t.get('content-list', [])
        content = content_list[0].get('content', '') if content_list else ""

        # Gemini가 C-ARM 건만 필터링
        if analyze_with_gemini(title, content):
            valid_count += 1
            # 마감기한 포맷팅 (YYYYMMDD -> YYYY-MM-DD)
            formatted_deadline = deadline if len(deadline) < 8 else f"{deadline[:4]}-{deadline[4:6]}-{deadline[6:8]}"
            
            cards_html += f"""
            <div class="toss-card p-6 border border-gray-100 mb-4 bg-white rounded-3xl shadow-sm">
                <div class="flex justify-between items-start mb-3">
                    <span class="text-[11px] font-bold bg-blue-50 text-blue-600 px-2 py-1 rounded-md">C-ARM TENDER</span>
                    <span class="text-xs text-red-400 font-medium">마감: {formatted_deadline}</span>
                </div>
                <h2 class="text-lg font-bold text-gray-800 mb-2 leading-tight">{title}</h2>
                <div class="text-sm text-gray-500 line-clamp-2 mb-4">{content[:150]}...</div>
                <a href="{link}" target="_blank" class="inline-block text-sm font-semibold text-[#3182F7]">공고 상세보기 →</a>
            </div>
            """

    empty_state_html = ""
    if valid_count == 0:
        empty_state_html = f"""
        <div class='text-center py-20'>
            <div class='text-4xl mb-4'>🔍</div>
            <div class='text-gray-400'>2024년 이후 검색 결과 중<br>Gemini가 분류한 C-ARM 공고가 없습니다.</div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>C-ARM Global Tender Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background-color: #F2F4F6; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; letter-spacing: -0.02em; }}
            .toss-card {{ transition: all 0.2s ease-in-out; }}
            .toss-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.04); }}
        </style>
    </head>
    <body class="p-4 md:p-8 text-gray-900">
        <div class="max-w-2xl mx-auto">
            <header class="mb-8 px-2 flex justify-between items-end">
                <div>
                    <h1 class="text-2xl font-bold tracking-tight">C-ARM 입찰 현황</h1>
                    <p class="text-sm text-gray-500 mt-1">최근 업데이트: {now}</p>
                </div>
                <div class="text-right">
                    <span class="text-xs font-bold text-blue-600 bg-blue-50 px-3 py-1 rounded-full">실시간 분석 중</span>
                </div>
            </header>
            <div id="container">
                {cards_html}
                {empty_state_html}
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    data = fetch_ted_tenders()
    generate_html(data)
