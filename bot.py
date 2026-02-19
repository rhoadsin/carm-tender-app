import os
import google.generativeai as genai

# 금고에서 키 가져오기
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 1. 텐더 샘플 데이터 (나중에는 실제 사이트에서 긁어오도록 바뀝니다)
sample_tenders = [
    "Poland - X-ray fluoroscopy devices - RTG ramię C - 645 731 PLN",
    "Germany - Dental X-ray unit for clinic - 50 000 EUR",
    "Romania - Sistem C-Arm pentru ortopedie - 2 bucati"
]

results_html = ""

# 2. AI에게 C-ARM인지 물어보고 HTML 한 줄씩 만들기
for tender in sample_tenders:
    prompt = f"이 공고가 수술용 C-ARM이면 'YES', 아니면 'NO'라고만 답해줘: {tender}"
    response = model.generate_content(prompt)
    
    if "YES" in response.text.upper():
        results_html += f"<li>✅ <b>C-ARM 발견:</b> {tender}</li>"

# 3. index.html 파일 생성 (결과 페이지)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(f"<html><body><h1>C-ARM 실시간 텐더 리스트</h1><ul>{results_html}</ul></body></html>")
