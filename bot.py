import os
import requests
import google.generativeai as genai
from datetime import datetime

# 1. API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def fetch_ted_tenders():
    print("Fetching data...")
    url = "https://ted.europa.eu/api/v3/notices/search"
    
    # 쿼리 단순화: 의료 장비(33100000) 중 arm 키워드 포함 건 전체
    # 문법을 가장 표준적인 방식으로 변경
    query = "CPV_CODE IN (33100000, 33111000, 33111400) AND CONTENT ~ 'arm'"
    
    payload = {
        "query": query,
        "limit": 50,
        "fields": ["publication-number", "title", "dt-deadline", "oj-url", "content-list"]
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.json().get('notices', [])
    except Exception as e:
        print(f"API Error: {e}")
        return []

def generate_html(tenders):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cards_html = ""
    valid_count = 0
    
    # 데이터가 있을 경우 처리
    for t in tenders:
        title = t.get('title', ['No Title'])[0]
        deadline = t.get('dt-deadline', 'N/A')
        link = t.get('oj-url', '#')
        
        # Gemini 분석 (간소화하여 속도 향상)
        prompt = f"Is this tender for a 'Surgical C-ARM'? Answer YES/NO only. Title: {title}"
        try:
            res = model.generate_content(prompt)
            if "YES" in res.text.upper():
                valid_count += 1
                cards_html += f"""
                <div class="bg-white p-6 rounded-3xl mb-4 shadow-sm border border-gray-100">
                    <div class="text-[11px] font-bold text-blue-600 mb-2">C-ARM TENDER</div>
                    <h2 class="text-lg font-bold mb-3">{title}</h2>
                    <div class="flex justify-between items-center">
                        <span class="text-xs text-gray-400">마감: {deadline}</span>
                        <a href="{link}" target="_blank" class="text-sm font-bold text-blue-500">상세보기 →</a>
                    </div>
                </div>
                """
        except:
            continue

    # 데이터가 없을 때 메시지
    if valid_count == 0:
        cards_html = "<div class='text-center py-20 text-gray-400 font-medium text-sm'>현재 조건에 맞는 C-ARM 입찰 건이 없습니다.</div>"

    # HTML 템플릿 (f-string 충돌을 피하기 위해 분리)
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>body { background-color: #F2F4F6; }</style>
    </head>
    <body class="p-6">
        <div class="max-w-xl mx-auto">
            <header class="mb-8">
                <h1 class="text-2xl font-bold">C-ARM 입찰 모니터링</h1>
                <p class="text-xs text-gray-500 mt-1">업데이트: {{TIME}}</p>
            </header>
            <div>{{CARDS}}</div>
        </div>
    </body>
    </html>
    """
    
    # 안전하게 치환
    final_html = template.replace("{{TIME}}", now).replace("{{CARDS}}", cards_html)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)

if __name__ == "__main__":
    raw_notices = fetch_ted_tenders()
    generate_html(raw_notices)
