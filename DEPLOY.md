# Deploying to Streamlit Cloud

## Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Sports Injury Risk Pipeline"
   git remote add origin https://github.com/YOUR_USERNAME/sports-injury-pipeline.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your repository
   - Main file path: `app.py`
   - Click "Deploy"

3. **No secrets needed** — the app uses the bundled seed dataset by default.
   The live scraper (`data/build_dataset.py --scrape`) runs locally only.

## GitHub repo structure expected by Streamlit Cloud

```
/
├── app.py               ← entry point
├── requirements.txt     ← dependencies
├── .streamlit/
│   └── config.toml      ← dark theme config
├── data/
│   ├── __init__.py
│   ├── seed_data.py
│   └── build_dataset.py
└── pages/
    ├── __init__.py
    ├── p00_overview.py
    └── ... (all pages)
```

## Troubleshooting imports on Streamlit Cloud

If you see `ModuleNotFoundError: No module named 'data'`, ensure:
- `data/__init__.py` exists (it does in this project)
- `app.py` is at the repo root (not inside a subdirectory)
- The path fix in `p10_dashboard.py` is present:
  ```python
  ROOT = Path(__file__).resolve().parent.parent
  if str(ROOT) not in sys.path:
      sys.path.insert(0, str(ROOT))
  ```
