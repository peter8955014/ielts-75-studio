ielts-75-studio/
├── index.html                          # 主網站（Notion 深淺色風格、4大Part模擬、雙語速聽力、動態刷題、自訂單字本）
├── vocab.json                          # 動態單字與美劇片語資料庫（由 Python 每日自動擴充）
├── ielts_bank.json                     # 歷屆雅思考題庫（Listening / Reading / Writing / Speaking 真題）
├── update_english_db.py                # Python 自動更新腳本（抓取最新學術新聞語料與字典音標，擴充 JSON）
├── requirements.txt                    # Python 套件清單
├── README.md                           # GitHub 部署與自動更新說明
└── .github/workflows/daily_update.yml  # GitHub Actions 每日自動執行 Python 更新並 Commit
