# IELTS 7.5+ 雅思全科實戰 · 美劇高頻詞庫 · 動態刷題系統

## 部署與自動更新步驟
1. 將本專案檔案上傳至 GitHub Repository，並先在本地執行一次 `python update_english_db.py` 產生初始 `vocab.json` 與 `ielts_bank.json`。
2. 前往 GitHub Repo 的 **Settings → Pages**，將 Source 設為 `Deploy from a branch` (`main` / `/root`) 即可取得免費網址。
3. 前往 **Settings → Actions → General**，確認 Workflow permissions 已勾選 `Read and write permissions`，系統即會每日自動擴充單字與刷新題庫。
