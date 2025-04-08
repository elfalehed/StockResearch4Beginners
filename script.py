# 🛠️ SETUP
!pip install yfinance openai beautifulsoup4 pandas --quiet

import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd
import openai
import datetime

# 🔑 SET YOUR OPENAI API KEY
openai.api_key = "sk-..."  # Replace with your own OpenAI API key

# 📈 STEP 1: Fetch Stock Info
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    current_price = stock.history(period="1d")["Close"].iloc[-1]
    five_year_data = stock.history(period="5y")
    return current_price, five_year_data

def summarize_performance(five_year_data):
    start_price = five_year_data["Close"].iloc[0]
    end_price = five_year_data["Close"].iloc[-1]
    return {
        "Start Price": round(start_price, 2),
        "End Price": round(end_price, 2),
        "Return (%)": round(((end_price - start_price) / start_price) * 100, 2)
    }

# 🔍 STEP 2: Get 10-K Filing from SEC
def get_cik(ticker):
    url = "https://www.sec.gov/files/company_tickers_exchange.json"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    data = r.json()
    for company in data.values():
        if company["ticker"].upper() == ticker.upper():
            return str(company["cik_str"]).zfill(10)
    return None

def get_latest_10k_url(cik):
    headers = {"User-Agent": "Mozilla/5.0"}
    base_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    r = requests.get(base_url, headers=headers)
    data = r.json()
    for i, form_type in enumerate(data["filings"]["recent"]["form"]):
        if form_type == "10-K":
            accession = data["filings"]["recent"]["accessionNumber"][i].replace("-", "")
            return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/10-K.txt"
    return None

def get_10k_text(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    return soup.get_text()[:15000]  # Get first 15,000 chars

# 🧠 STEP 3: Summarize with LLM
def summarize_with_gpt(text):
    prompt = f"""
You are a financial analyst. Please summarize the following 10-K filing, covering:

1. Business Overview
2. Key Financial Metrics
3. Risk Factors
4. Opportunities and Growth Areas
5. Anything notable or unusual

TEXT:
{text}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response["choices"][0]["message"]["content"]

# 📊 STEP 4: Generate Final Report
def generate_report(ticker):
    print(f"🔎 Researching {ticker}...\n")
    current_price, data = get_stock_data(ticker)
    perf = summarize_performance(data)

    cik = get_cik(ticker)
    tenk_url = get_latest_10k_url(cik)
    tenk_text = get_10k_text(tenk_url) if tenk_url else "10-K not found."

    summary = summarize_with_gpt(tenk_text) if tenk_url else "Summary not available."

    print("=== 📘 STOCK PERFORMANCE ===")
    print(f"Current Price: ${current_price:.2f}")
    print(perf)

    print("\n=== 📄 10-K SUMMARY ===")
    print(summary)

# ▶️ Run it
generate_report("AAPL")  # Replace with your target stock ticker
