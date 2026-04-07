# iDealz Marketing Analytics

End-to-end marketing analytics web app for LK_DigiBrush_iDealz.
Analyzes Meta Ads, TikTok Ads, and Google Analytics (GA4) data.

## Features

- Upload Meta CSV, TikTok XLSX, GA4 CSV exports
- Automated analysis: CPM, CPC, CTR, frequency, fatigue alerts
- TikTok video funnel: watch time, completion rate, destination CTR
- Website traffic: sessions, engagement rate, channel breakdown
- One-click PDF report generation (CEO-ready)
- One-click Excel export with all analysis tabs
- Smart alerts for critical issues

## How to run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## How to deploy on Streamlit Community Cloud (free)

1. Push this folder to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/idealz-analytics.git
git push -u origin main
```

2. Go to share.streamlit.io
3. Sign in with GitHub
4. New app → select your repo → main branch → app.py
5. Deploy → live in 2 minutes

## How to deploy on Hugging Face Spaces (free)

1. Go to huggingface.co/spaces
2. Create Space → SDK: Streamlit
3. Name: idealz-marketing-analytics
4. Push your code:
```bash
git clone https://huggingface.co/spaces/shakeebumn2001/idealz-marketing-analytics
cd idealz-marketing-analytics
cp -r /path/to/idealz_analytics/* .
git add .
git commit -m "Deploy iDealz analytics"
git push
```

## Weekly workflow

### Monday (Data Pull)
1. Export Meta CSV from Ads Manager → Ads tab → Export
2. Export TikTok XLSX from Ads Manager → Reporting → Custom Report
3. Export GA4 CSV from Analytics → Traffic Acquisition → Download

### Tuesday–Thursday (Analysis)
1. Open the web app
2. Upload all 3 files in sidebar
3. Review each tab for insights and alerts

### Friday (Report)
1. Go to Weekly Report tab
2. Add your recommendations
3. Click Download PDF → send to team lead

## File naming convention
```
meta_2026_04_06.csv
tiktok_2026_04_06.xlsx
ga4_2026_04_06.csv
```

## Project structure
```
idealz_analytics/
├── app.py                      Main Streamlit app
├── requirements.txt
├── README.md
├── analysis/
│   ├── meta_analysis.py        Meta ads analysis + charts
│   ├── tiktok_analysis.py      TikTok video metrics analysis
│   ├── website_analysis.py     GA4 website analysis
│   └── report_generator.py     PDF + Excel report generator
└── utils/
    ├── data_loader.py           File upload + data cleaning
    └── alerts.py                Smart alert system
```
