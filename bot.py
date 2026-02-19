import os
import json
import requests
import google.generativeai as genai
from datetime import datetime

# 1. 환경 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def fetch_ted_tenders():
    print("Fetching data from TED API...")
    url = "https://ted.europa.eu/api/v3/notices/search"
    # CPV 33111400 (Fluoroscopy) 및 키워드 arm 검색
    query = "CPV_CODE IN (33111400) AND CONTENT ~ 'arm'"
    payload = {
        "query": query,
        "limit": 20,
        "fields": ["publication-number", "content-list", "title", "dt-deadline", "oj-url"]
    }
    try:
        response = requests.post(url, json=payload)
        return response.json().get('notices', [])
    except Exception as e:
        print(f"Error fetching TED data: {e}")
        return []

def analyze_with_gemini(title, content):
    prompt = f"""
    Analyze the following medical device tender information.
    Is this tender specifically for a "Surgical Mobile C-ARM" (imaging equipment)?
    Answer ONLY 'YES' or 'NO'. 
    If it's about robotic arms, industrial arms, or general parts not related to C-ARM imaging, answer 'NO'.

    Title: {title}
    Description: {content[:500]}
    """
    try:
        response = model.generate_content(prompt)
        result = response.text.strip().upper()
        return "YES" in result
    except:
        return False

def generate_html(tenders):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Toss Style UI Template
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>C-ARM Global Tender</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #F2F4F6; }}
            .toss-card {{ background: white; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); transition: transform 0.2s; }}
            .toss-card:active {{ transform: scale(0.98); }}
            .toss-blue {{ color: #3182F7; }}
            .bg-toss-blue {{ background-color: #3182F7; }}
        </style>
    </head>
    <body class="p-4 md:p-8">
        <div class="max-w-2xl mx-auto">
            <header class="mb-8">
                <h1 class="text-2xl font-bold text-gray-900">C-ARM 입찰 모니터링</h1>
                <p class="text-sm text-gray-500 mt-2">최근 업데이트: {now}</p>
            </header>

            <div class="space-y-4">
                {{cards}}
            </div>
            
            {{empty_state}}
        </div>
    </body>
    </html>
    """
    
    cards = ""
    valid_count = 0
    
    for t in tenders:
        title = t.get('title', ['No Title'])[0]
        deadline = t.get('dt-deadline', 'N/A')
        link = t.get('oj-url', '#')
        content = t.get('content-list', [{}])[0].get('content', '')

        if analyze_with_gemini(title, content):
            valid_count += 1
            cards += f"""
            <div class="toss-card p-6 border border-gray-100">
                <div class="flex justify-between items-start mb-3">
                    <span class="text-xs font-semibold bg-blue-50 text-blue-600 px-2 py-1 rounded">C-ARM 검출</span>
                    <span class="text-xs text-gray-400">마감: {deadline}</span>
                </div>
                <h2 class="text-lg font-bold text-gray-800 mb-2 leading-tight">{title}</h2>
                <a href="{link}" target="_blank" class="inline-block mt-4 text-sm font-semibold toss-blue">공고 상세보기 →</a>
            </div>
            """

    empty_state = "" if valid_count > 0 else "<div class='text-center py-20 text-gray-400'>새로운 관련 공고가 없습니다.</div>"
    
    final_html = html_template.replace("{{cards}}", cards).replace("{{empty_state}}", empty_state)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print(f"Update Complete: {valid_count} tenders found.")

if __name__ == "__main__":
    raw_data = fetch_ted_tenders()
    generate_html(raw_data)
