import csv
import io
import json
import random
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

VOCAB_FILE = "vocab.json"
BANK_FILE = "ielts_bank.json"
TARGET_VOCAB_COUNT = 10000

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

# 經典美劇母語者高頻片語庫
TV_DRAMA_IDIOMS = [
    {"word": "cut corners", "ipa": "/kʌt ˈkɔːr.nərz/", "pos": "idiom", "zh": "偷工減料、圖省事走捷徑", "example": "When building mission-critical infrastructure, engineers can never afford to cut corners.", "source": "TV: Suits (無照律師)", "part": "Speaking", "freq": True},
    {"word": "off the top of my head", "ipa": "/ɔːf ðə tɑːp əv maɪ hed/", "pos": "idiom", "zh": "憑直覺、不假思索地說", "example": "Off the top of my head, I would say public transport subsidies are the most effective measure.", "source": "TV: Friends (六人行)", "part": "Speaking", "freq": True},
    {"word": "on the same page", "ipa": "/ɑːn ðə seɪm peɪdʒ/", "pos": "idiom", "zh": "達成共識、想法一致", "example": "Before launching the rollout, let us make sure all stakeholders are on the same page.", "source": "TV: The Office (辦公室瘋雲)", "part": "Listening", "freq": True},
    {"word": "a blessing in disguise", "ipa": "/ə ˈbles.ɪŋ ɪn dɪsˈɡaɪz/", "pos": "idiom", "zh": "塞翁失馬、因禍得福", "example": "Missing that flight turned out to be a blessing in disguise because I met my future partner.", "source": "TV: Modern Family (摩登家庭)", "part": "Speaking", "freq": True},
    {"word": "double-edged sword", "ipa": "/ˌdʌb.əl ˈedʒd sɔːrd/", "pos": "idiom", "zh": "雙面刃（有利亦有弊）", "example": "Artificial intelligence is a double-edged sword that boosts productivity while displacing routine jobs.", "source": "TV: Silicon Valley (矽谷群瞎傳)", "part": "Speaking", "freq": True},
    {"word": "call it a day", "ipa": "/kɔːl ɪt ə deɪ/", "pos": "idiom", "zh": "今天就到此為止、收工", "example": "We have been troubleshooting this routing table for six hours; let us call it a day.", "source": "TV: Brooklyn Nine-Nine", "part": "Listening", "freq": True},
    {"word": "tread on thin ice", "ipa": "/tred ɑːn θɪn aɪs/", "pos": "idiom", "zh": "如履薄冰、冒極大風險", "example": "By withholding crucial audit disclosures, the executives were treading on thin ice.", "source": "TV: Breaking Bad (絕命毒師)", "part": "Speaking", "freq": True},
    {"word": "elephant in the room", "ipa": "/ˈel.ɪ.fənt ɪn ðə ruːm/", "pos": "idiom", "zh": "顯而易見卻人人避談的棘手問題", "example": "Rising housing unaffordability is the elephant in the room during every municipal debate.", "source": "TV: House of Cards (紙牌屋)", "part": "Speaking", "freq": True},
    {"word": "bite the bullet", "ipa": "/baɪt ðə ˈbʊl.ɪt/", "pos": "idiom", "zh": "咬緊牙關硬著頭皮做", "example": "We had to bite the bullet and overhaul the entire legacy database over the weekend.", "source": "TV: Suits (無照律師)", "part": "Speaking", "freq": True},
    {"word": "burn the midnight oil", "ipa": "/bɜːrn ðə ˈmɪd.naɪt ɔɪl/", "pos": "idiom", "zh": "熬夜加班或讀書", "example": "Many candidates burn the midnight oil preparing for the IELTS Academic module.", "source": "TV: The Big Bang Theory", "part": "Speaking", "freq": True},
    {"word": "hit the nail on the head", "ipa": "/hɪt ðə neɪl ɑːn ðə hed/", "pos": "idiom", "zh": "一針見血、說到點子上", "example": "Your analysis of urban sprawl hit the nail on the head.", "source": "TV: Friends (六人行)", "part": "Speaking", "freq": True},
    {"word": "back to square one", "ipa": "/bæk tə skwer wʌn/", "pos": "idiom", "zh": "回到原點、重新開始", "example": "When the prototype failed stress testing, the engineering team was back to square one.", "source": "TV: Silicon Valley (矽谷群瞎傳)", "part": "Listening", "freq": True}
]


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def fetch_tv_subtitle_frequency_words():
    """抓取美劇/電影 OpenSubtitles 高頻口語單字清單"""
    url = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_50k.txt"
    tv_words = {}
    try:
        print("正在下載美劇/影視字幕高頻詞表 (OpenSubtitles)...")
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            for rank, line in enumerate(r.text.splitlines()[:18000], start=1):
                parts = line.strip().split()
                if len(parts) >= 1 and parts[0].isalpha() and len(parts[0]) >= 4:
                    tv_words[parts[0].lower()] = rank
        print(f"成功取得 {len(tv_words)} 個美劇高頻詞頻排名。")
    except Exception as e:
        print("美劇詞頻表下載略過:", e)
    return tv_words


def build_10k_vocab_database(existing_vocab):
    """結合 IELTS 學術標籤詞庫與美劇高頻詞表，建構 10,000 單字量雙語資料庫"""
    vocab_map = {v["word"].lower(): v for v in existing_vocab}

    # 1. 先放入美劇經典片語
    for idx, item in enumerate(TV_DRAMA_IDIOMS):
        w_key = item["word"].lower()
        if w_key not in vocab_map:
            vocab_map[w_key] = {
                "id": f"tv_idiom_{idx+1}",
                "word": item["word"],
                "ipa": item["ipa"],
                "pos": item["pos"],
                "zh": item["zh"],
                "collocations": f"{item['word']} (Native Drama Expression)",
                "example": item["example"],
                "source": item["source"],
                "part": item["part"],
                "freq": True
            }

    if len(vocab_map) >= TARGET_VOCAB_COUNT:
        return list(vocab_map.values())

    # 2. 取得美劇高頻詞排名
    tv_freq_map = fetch_tv_subtitle_frequency_words()

    # 3. 串流下載開源 ECDICT 雙語字典並篩選 IELTS 7.5+ 與美劇高頻單字至 10,000 筆
    ecdict_url = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv"
    print("正在從開源雙語語料庫篩選 IELTS 7.5+ 與美劇高頻詞彙 (目標 10,000 單)...")
    try:
        with requests.get(ecdict_url, headers=HEADERS, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            lines = (line.decode("utf-8", errors="ignore") for line in resp.iter_lines())
            reader = csv.DictReader(lines)

            ielts_candidates = []
            tv_candidates = []

            for row in reader:
                word = (row.get("word") or "").strip()
                if not word or not word.isalpha() or len(word) < 4 or not word.islower():
                    continue
                if word in vocab_map:
                    continue

                zh_raw = (row.get("translation") or "").strip().replace("\\n", "；")
                if not zh_raw:
                    continue

                phonetic = (row.get("phonetic") or "").strip()
                ipa = f"/{phonetic}/" if phonetic else ""
                pos = (row.get("pos") or "vocab").split(":")[0]
                tag = (row.get("tag") or "").lower()
                bnc = int(row.get("bnc") or 99999)
                frq = int(row.get("frq") or 99999)
                tv_rank = tv_freq_map.get(word, 99999)

                is_ielts_or_adv = any(t in tag for t in ["ielts", "toefl", "gre", "cet6"])
                is_tv_common = tv_rank <= 12000

                if is_ielts_or_adv:
                    is_high_freq = ("ielts" in tag) or (0 < frq <= 6500) or (0 < bnc <= 6500)
                    part_guess = "Writing" if word.endswith(("ate", "ize", "ify", "tion", "ment")) else ("Reading" if len(word) >= 8 else "Speaking")
                    ielts_candidates.append({
                        "id": f"ielts_{word}",
                        "word": word,
                        "ipa": ipa,
                        "pos": pos,
                        "zh": zh_raw[:90],
                        "collocations": f"{word} (IELTS Band 7.5+)",
                        "example": f"In academic discourse, '{word}' is frequently used to articulate precise arguments.",
                        "source": "IELTS 7.5+ Academic",
                        "part": part_guess,
                        "freq": is_high_freq,
                        "_rank": frq if frq > 0 else 50000
                    })
                elif is_tv_common:
                    tv_candidates.append({
                        "id": f"tv_{word}",
                        "word": word,
                        "ipa": ipa,
                        "pos": pos,
                        "zh": zh_raw[:90],
                        "collocations": f"{word} (US TV Subtitle Top {tv_rank})",
                        "example": f"Native speakers in American TV dramas often use '{word}' in everyday dialogue.",
                        "source": "TV Drama High-Freq (美劇高頻)",
                        "part": "Listening" if tv_rank <= 5000 else "Speaking",
                        "freq": tv_rank <= 4500,
                        "_rank": tv_rank
                    })

            # 依詞頻排序並合併至 10,000 單
            ielts_candidates.sort(key=lambda x: x["_rank"])
            tv_candidates.sort(key=lambda x: x["_rank"])

            for item in ielts_candidates[:6500]:
                item.pop("_rank", None)
                vocab_map[item["word"]] = item
                if len(vocab_map) >= TARGET_VOCAB_COUNT:
                    break

            for item in tv_candidates:
                if len(vocab_map) >= TARGET_VOCAB_COUNT:
                    break
                if item["word"] not in vocab_map:
                    item.pop("_rank", None)
                    vocab_map[item["word"]] = item

    except Exception as e:
        print(f"抓取 ECDICT 過程發生錯誤: {e}")

    print(f"詞庫建構完成，目前總單字量：{len(vocab_map)} 單。")
    return list(vocab_map.values())


def scrape_web_ielts_resources(bank):
    """爬取公開雅思官方與備考網站範例題目，持續擴充閱讀/聽力/寫作/口說題庫"""
    print("正在從網路雅思備考資源爬取最新閱讀與考題語料...")
    target_urls = [
        "https://ielts.org/take-a-test/preparation-resources/sample-test-questions/academic-test",
        "https://ieltsidpindia.com/prepare/ielts-exam-sample-papers"
    ]
    scraped_snippets = []
    for url in target_urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=12)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                for p in soup.find_all(["p", "li"]):
                    txt = re.sub(r"\s+", " ", p.get_text()).strip()
                    if 80 <= len(txt) <= 320 and ("IELTS" in txt or "Academic" in txt or "Listening" in txt):
                        scraped_snippets.append(txt)
        except Exception:
            continue

    # 將爬取到的最新題型說明轉化為閱讀與模擬考題補充包
    if scraped_snippets:
        unique_snips = list(dict.fromkeys(scraped_snippets))[:6]
        bank.setdefault("quizPool", [])
        existing_ids = {q["id"] for q in bank["quizPool"]}
        for i, snip in enumerate(unique_snips):
            qid = f"web_ielts_{datetime.utcnow().strftime('%Y%m')}_{i+1}"
            if qid not in existing_ids:
                bank["quizPool"].append({
                    "id": qid,
                    "tag": "網路雅思官方題型精選",
                    "question": f"Based on official IELTS exam guidelines:\n\"{snip}\"\nWhich skill area does this format requirement belong to?",
                    "options": [
                        "IELTS Academic & General Module Format",
                        "Casual Slang Translation Only",
                        "Handwriting Calligraphy Assessment",
                        "Programming Syntax Evaluation"
                    ],
                    "answer": "IELTS Academic & General Module Format",
                    "explanation": f"摘自公開雅思官方備考指南：{snip}"
                })

    # 從 BBC / NPR 每日抓取高階學術句子加入動態填空題池
    rss_urls = [
        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://feeds.npr.org/1001/rss.xml"
    ]
    for rss in rss_urls:
        try:
            r = requests.get(rss, headers=HEADERS, timeout=10)
            root = ET.fromstring(r.text)
            for item in root.findall(".//item")[:5]:
                desc = re.sub(r"<[^>]+>", "", item.findtext("description") or "").strip()
                tokens = re.findall(r"\b[a-z]{9,13}\b", desc)
                if tokens and len(desc) > 50:
                    target_w = tokens[0]
                    masked = re.sub(rf"\b{re.escape(target_w)}\b", "________", desc, count=1)
                    qid = f"news_q_{target_w.lower()}"
                    if not any(q["id"] == qid for q in bank["quizPool"]):
                        distractors = random.sample(
                            ["unprecedented", "ubiquitous", "mitigate", "exacerbate", "detrimental", "feasible", "scrutinize", "proliferate"],
                            3
                        )
                        if target_w.lower() not in [d.lower() for d in distractors]:
                            opts = distractors + [target_w]
                            random.shuffle(opts)
                            bank["quizPool"].append({
                                "id": qid,
                                "tag": f"每日國際新聞真題語境 ({datetime.utcnow().strftime('%Y-%m-%d')})",
                                "question": f"請選出最適合填入新聞語境空格的高階單字：\n\"{masked}\"",
                                "options": opts,
                                "answer": target_w,
                                "explanation": f"原句出自國際新聞語料，正確單字為「{target_w}」。"
                            })
        except Exception:
            continue

    bank["quizPool"] = bank.get("quizPool", [])[-80:]
    return bank


def main():
    existing_vocab = load_json(VOCAB_FILE, [])
    full_vocab = build_10k_vocab_database(existing_vocab)
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(full_vocab, f, ensure_ascii=False, indent=2)

    # 注意：僅更新 quizPool，保留並擴充 listening / reading / writing / speaking 陣列
    bank = load_json(BANK_FILE, {})
    bank = scrape_web_ielts_resources(bank)
    with open(BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)

    print(f"✅ 全部完成！vocab.json 共 {len(full_vocab)} 筆單字，ielts_bank.json 題庫共 {len(bank.get('quizPool', []))} 題。")


if __name__ == "__main__":
    main()
