import os
import google.generativeai as genai
import requests
import xml.etree.ElementTree as ET

# 1. 환경 설정
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. TED 데이터 가져오기 (사용자 설정 반영: CPV 33111400 & 키워드 arm)
# 실제 TED 검색 결과에 'arm'이 포함된 공고를 가져오도록 URL을 구성합니다.
ted_url = "https://ted.europa.eu/en/rss-feed?searchScope=ACTIVE&mainCpv=33111400&freeText=arm"
response = requests.get(ted_url)
root = ET.fromstring(response.content)

results_html = ""

# 3. AI 분석 및 정밀 필터링
for item in root.findall('.//item')[:15]: # 분석 범위를 조금 더 넓혔습니다.
    title = item.find('title').text
    description = item.find('description').text
    link = item.find('link').text
    
    # AI 프롬프트 수정: 'arm'이라는 단어가 들어간 공고 중 'C-arm' 장치인지 구분
    prompt = f"""
    당신은 C-ARM 제조사 제노레이의 입찰 분석 전문가입니다. 
    아래 공고는 'arm'이라는 단어를 포함하고 있습니다. 
    이 공고가 '수술용 이동식 엑스레이 장비(Mobile C-arm)'인 경우에만 'YES'라고 답하고, 
    단순한 부품(Arm rest), 로봇 팔, 혹은 고정형 투시장치라면 'NO'라고 답하세요.
    제목: {title}
    내용: {description}
    """
    ai_response = model.generate_content(prompt)
    
    if "YES" in ai_response.text.upper():
        results_html += f"""
        <div style='margin-bottom: 25px; padding: 20px; border-left: 5px solid #3498db; background-color: white; border-radius: 4px; shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <h3 style='margin-top: 0; color: #2c3e50;'>[확인됨] {title}</h3>
            <p style='font-size: 14px; color: #34495e;'>{description[:300]}...</p>
            <a href='{link}' target='_blank' style='display: inline-block; padding: 8px 15px; background-color: #3498db; color: white; text-decoration: none; border-radius: 4px; font-size: 13px;'>공고 원문 페이지로 이동</a>
        </div>
        """

# 4. 결과 저장
if not results_html:
    results_html = "<p style='text-align: center; color: #95a5a6; padding: 40px;'>현재 조건(arm)에 부합하는 새로운 C-ARM 공고가 검색되지 않았습니다.</p>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(f"""
    <html>
    <head><meta charset='utf-8'><title>Genoray C-ARM Monitor</title></head>
    <body style='font-family: -apple-system, sans-serif; line-height: 1.6; padding: 30px; background-color: #f8f9fa;'>
        <div style='max-width: 900px; margin: 0 auto;'>
            <h1 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>📡 Genoray C-ARM 실시간 모니터링</h1>
            <p style='color: #7f8c8d;'>검색 조건: CPV 33111400 / Keyword: <b>arm</b></p>
            {results_html}
        </div>
    </body>
    </html>
    """)
