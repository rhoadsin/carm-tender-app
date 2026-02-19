import os
import google.generativeai as genai
import requests
import xml.etree.ElementTree as ET

# 1. 환경 설정
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. TED 데이터 가져오기 (검색 범위를 대폭 넓힌 주소입니다)
# 33111400 코드를 가진 모든 최신 공고를 가져옵니다.
ted_url = "https://ted.europa.eu/en/rss-feed?searchScope=ACTIVE&mainCpv=33111400"
response = requests.get(ted_url)
root = ET.fromstring(response.content)

results_html = ""
found_count = 0

# 3. AI 분석 (더 유연하게 판별하도록 프롬프트 수정)
for item in root.findall('.//item'): 
    title = item.find('title').text
    description = item.find('description').text
    link = item.find('link').text
    
    # AI에게 'arm'이라는 단어가 직접 없더라도 정황상 C-ARM이면 찾아내라고 지시
    prompt = f"""
    당신은 의료기기 글로벌 영업팀장입니다. 
    다음 공고가 '수술용 C-arm'이나 '이동형 투시 엑스레이' 입찰인지 분석하세요.
    단어 'arm'이 없더라도 내용이 C-arm 장비에 해당하면 'YES'라고 하세요.
    제목: {title}
    내용: {description}
    답변은 'YES' 또는 'NO'로 시작하고 이유를 짧게 적으세요.
    """
    ai_response = model.generate_content(prompt)
    
    if "YES" in ai_response.text.upper():
        found_count += 1
        results_html += f"""
        <div style='margin-bottom: 20px; padding: 20px; border-radius: 10px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 6px solid #0052cc;'>
            <h3 style='color: #0052cc; margin-top: 0;'>[포착] {title}</h3>
            <p style='color: #444; font-size: 0.95em;'>{description[:400]}</p>
            <p style='font-size: 0.85em; color: #666;'><b>AI 분석 결과:</b> {ai_response.text}</p>
            <a href='{link}' target='_blank' style='display: inline-block; margin-top: 10px; color: white; background: #0052cc; padding: 8px 16px; text-decoration: none; border-radius: 5px;'>상세 공고문 보기</a>
        </div>
        """

# 4. 최종 결과 생성
if found_count == 0:
    results_html = "<div style='text-align:center; padding: 50px;'>신규 공고가 없습니다. 검색 조건을 더 넓게 모니터링 중입니다.</div>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(f"""
    <html>
    <head><meta charset='utf-8'><title>Genoray C-ARM Tracker</title></head>
    <body style='font-family: sans-serif; background: #f0f2f5; padding: 20px;'>
        <div style='max-width: 800px; margin: 0 auto;'>
            <h1 style='color: #1c1e21;'>📡 제노레이 텐더 감지기</h1>
            <p>현재 모니터링 중인 기기: <b>C-ARM / Fluoroscopy</b></p>
            <hr style='border: 0; border-top: 1px solid #ddd; margin: 20px 0;'>
            {results_html}
        </div>
    </body>
    </html>
    """)
