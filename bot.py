import os
import requests
import google.generativeai as genai
from datetime import datetime

# 1. 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def fetch_ted_tenders():
    print("Fetching data from TED API...")
    url = "https://ted.europa.eu/api/v3/notices/search"
    
    # 검색 조건 완화: 'C-ARM' 키워드가 포함된 모든 의료기기 공고 검색
    query = "CONTENT ~ 'C-ARM' OR (CPV_CODE IN (33111400, 33110000) AND CONTENT ~ 'arm')"
    
    payload = {
        "query": query,
        "limit": 30,
        "fields": ["publication-number", "content-list", "title", "dt-deadline", "oj-url"]
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get('notices', [])
    except Exception as e:
        print(f"Error fetching TED data: {e}")
        return []

def analyze_with_gemini(title, content):
    prompt = f"""
    Analyze this medical tender. Is it for a "Surgical Mobile C-ARM"? 
    Answer ONLY 'YES' or 'NO'. 
    Title: {title}
    Description: {content[:500]}
    """
    try:
        response = model.generate_content(prompt)
        return "YES" in response.text.upper()
    except:
        return False

def generate_html(tenders):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 카드 레이아웃 생성
    cards_html = ""
    valid_count = 0
    
    for t in tenders:
        title = t.get('title', ['No Title'])[0]
        deadline = t.get('dt-deadline', 'N/A')
        link = t.get('oj-url', '#')
        content_list = t.get('content-list', [])
        content = content_list[0].get('content', '') if content_list else ""

        if analyze_with_gemini(title, content):
            valid_count += 1
            cards_html += f"""
            <div class="toss-card p-6 border border-gray-100 mb-4 bg-white rounded-3xl shadow-sm">
                <div class="flex justify-between items-start mb-3">
                    <span class="text-[11px] font-bold bg-blue-50 text-blue-600 px-2 py-1 rounded-md">C-ARM TENDER</span>
                    <span class="text-xs text-gray-400">마감: {deadline}</span>
                </div>
                <h2 class="text-lg font-bold text-gray-800 mb-2 leading-tight">{title}</h2>
                <a href="{link}" target="_blank" class="inline-block mt-2 text-sm font-semibold text-[#3182F7]">공고 상세보기 →</a>
            </div>
            """

    empty_state_html = ""
    if valid_count == 0:
        empty_state_html = "<div class='text-center py-20 text-gray-400'>현재 실시간 C-ARM 입찰 건이 없습니다.</div>"

    # 전체 HTML 템플릿 (중괄호 충돌 방지를 위해 % 방식 또는 단순 결합 사용)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>C-ARM Global Tender</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background-color: #F2F4F6; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            .toss-card {{ transition: transform 0.2s ease-in-out; }}
            .toss-card:active {{ transform: scale(0.98); }}
        </style>
    </head>
    <body class="p-4 md:p-8">
        <div class="max-w-2xl mx-auto">
            <header class="mb-8 px-2">
                <h1 class="text-2xl font-bold text-gray-900">C-ARM 입찰 모니터링</h1>
                <p class="text-sm text-gray-500 mt-1">최근 업데이트: {now}</p>
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
    print(f"Update Complete: {valid_count} items found.")

if __name__ == "__main__":
    data = fetch_ted_tenders()
    generate_html(data)
