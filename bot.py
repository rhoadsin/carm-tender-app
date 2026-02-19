import os
import google.generativeai as genai
import requests
import json

# 1. 환경 설정
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. TED 검색 API 호출 (사용자님의 검색 조건 반영)
# 검색어 'arm'과 CPV '33111400' 조건을 API 형태로 전달합니다.
search_url = "https://ted.europa.eu/api/v3/notices/search"
query = {
    "q": "33111400 AND arm",
    "scope": "ACTIVE",
    "limit": 20
}
headers = {'Content-Type': 'application/json'}

results_html = ""
found_count = 0

try:
    response = requests.post(search_url, json=query, headers=headers)
    data = response.json()
    notices = data.get('notices', [])

    # 3. AI 분석 및 데이터 추출
    for notice in notices:
        title = notice.get('title', {}).get('en', 'No Title')
        summary = notice.get('summary', {}).get('en', 'No Summary available')
        notice_id = notice.get('noticeId')
        link = f"https://ted.europa.eu/en/notice/-/detail/{notice_id}"
        
        # AI 판별 로직
        prompt = f"Analyze if this is a 'Surgical Mobile C-arm' tender. Answer 'YES' or 'NO': Title: {title}, Content: {summary}"
        ai_response = model.generate_content(prompt)
        
        if "YES" in ai_response.text.upper():
            found_count += 1
            results_html += f"""
            <div style='margin-bottom: 20px; padding: 20px; border-radius: 12px; background: white; border-left: 8px solid #0052cc; box-shadow: 0 4px 12px rgba(0,0,0,0.08);'>
                <h3 style='color: #0052cc; margin-top: 0;'>[포착] {title}</h3>
                <p style='color: #333; font-size: 0.95rem;'>{summary[:500]}...</p>
                <div style='margin-top: 15px;'>
                    <a href='{link}' target='_blank' style='background: #0052cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 600;'>공고 상세페이지 보기</a>
                </div>
            </div>
            """
except Exception as e:
    results_html = f"<p>데이터를 가져오는 중 오류가 발생했습니다: {str(e)}</p>"

# 4. 결과가 없을 경우 대비
if found_count == 0 and not results_html:
    results_html = "<div style='text-align:center; padding: 60px; color: #666;'>현재 TED 웹사이트의 실시간 결과와 AI 판별 조건이 일치하는 C-ARM 공고가 없습니다.</div>"

# 5. index.html 저장
with open("index.html", "w", encoding="utf-8") as f:
    f.write(f"""
    <html>
    <head><meta charset='utf-8'><title>Genoray Dashboard</title></head>
    <body style='font-family: -apple-system, sans-serif; background: #f4f7f9; padding: 40px;'>
        <div style='max-width: 900px; margin: 0 auto;'>
            <h1 style='color: #1a1a1a; font-size: 2.5rem; margin-bottom: 10px;'>📡 Genoray Intelligence</h1>
            <p style='color: #666; font-size: 1.1rem;'>TED EU 실시간 모니터링: <b>CPV 33111400 / arm</b></p>
            <hr style='border: 0; border-top: 2px solid #eee; margin: 30px 0;'>
            {results_html}
        </div>
    </body>
    </html>
    """)
