import json
import re
import random
from datetime import datetime
import requests
import xml.etree.ElementTree as ET

VOCAB_FILE = "vocab.json"
BANK_FILE = "ielts_bank.json"

# 預設高頻學術與美劇種子池（每次執行會自動挑選尚未收錄的新詞並串接線上字典補全音標與真實例句）
CANDIDATE_POOL = [
    {"word": "ubiquitous", "zh": "無所不在的、十分普遍的", "source": "IELTS Academic", "part": "Reading", "freq": True},
    {"word": "mitigate", "zh": "減輕、緩和（風險或負面影響）", "source": "IELTS Academic", "part": "Writing", "freq": True},
    {"word": "exacerbate", "zh": "使惡化、加劇", "source": "IELTS Academic", "part": "Writing", "freq": True},
    {"word": "detrimental", "zh": "有害的、不利的", "source": "IELTS Academic", "part": "Writing", "freq": True},
    {"word": "proliferate", "zh": "激增、迅速擴散", "source": "IELTS Academic", "part": "Listening", "freq": True},
    {"word": "unprecedented", "zh": "史無前例的、空前的", "source": "IELTS Academic", "part": "Writing", "freq": True},
    {"word": "scrutinize", "zh": "仔細審查、嚴格檢視", "source": "IELTS Academic", "part": "Reading", "freq": True},
    {"word": "alleviate", "zh": "緩解、減輕（痛苦或擁塞）", "source": "IELTS Academic", "part": "Writing", "freq": True},
    {"word": "substantiate", "zh": "證實、提供證據支持", "source": "IELTS Academic", "part": "Reading", "freq": True},
    {"word": "dichotomy", "zh": "二分法、截然對立", "source": "IELTS Academic", "part": "Reading", "freq": False},
    {"word": "pragmatic", "zh": "務實的、講求實效的", "source": "IELTS Academic", "part": "Speaking", "freq": True},
    {"word": "conducive", "zh": "有助於...的、有益的", "source": "IELTS Academic", "part": "Writing", "freq": True},
    {"word": "repercussion", "zh": "深遠影響、惡果", "source": "IELTS Academic", "part": "Writing", "freq": True},
    {"word": "ambiguous", "zh": "模稜兩可的、含糊不清的", "source": "IELTS Academic", "part": "Reading", "freq": True},
    {"word": "cut corners", "zh": "偷工減料、圖省事走捷徑", "source": "TV: Suits (無照律師)", "part": "Speaking", "freq": True},
    {"word": "off the top of my head", "zh": "憑直覺/不假思索地說", "source": "TV: Friends (六人行)", "part": "Speaking", "freq": True},
    {"word": "on the same page", "zh": "達成共識、想法一致", "source": "TV: The Office (辦公室瘋雲)", "part": "Listening", "freq": True},
    {"word": "double-edged sword", "zh": "雙面刃（有利亦有弊）", "source": "TV: Silicon Valley (矽谷群瞎傳)", "part": "Speaking", "freq": True},
    {"word": "a blessing in disguise", "zh": "塞翁失馬、因禍得福", "source": "TV: Modern Family (摩登家庭)", "part": "Speaking", "freq": True},
    {"word": "elephant in the room", "zh": "顯而易見卻人人避談的棘手問題", "source": "TV: House of Cards (紙牌屋)", "part": "Speaking", "freq": True}
]


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def fetch_dictionary_enrichment(word: str):
    """串接免費 Free Dictionary API 抓取 IPA 音標、詞性與真實例句"""
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{requests.utils.quote(word)}"
        res = requests.get(url, timeout=6)
        if res.status_code != 200:
            return None
        data = res.json()[0]
        ipa = data.get("phonetic") or ""
        if not ipa:
            for p in data.get("phonetics", []):
                if p.get("text"):
                    ipa = p["text"]
                    break
        meaning = data.get("meanings", [{}])[0]
        pos = meaning.get("partOfSpeech", "vocab")
        defs = meaning.get("definitions", [{}])
        en_def = defs[0].get("definition", "")
        example = ""
        for d in defs:
            if d.get("example"):
                example = d["example"]
                break
        return {"ipa": ipa, "pos": pos, "enDef": en_def, "example": example}
    except Exception:
        return None


def fetch_daily_news_vocab():
    """從 BBC / NPR 公開 RSS 擷取每日高頻學術單字並補全字典釋義"""
    rss_urls = [
        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://feeds.npr.org/1001/rss.xml"
    ]
    harvested = []
    for url in rss_urls:
        try:
            r = requests.get(url, timeout=8)
            root = ET.fromstring(r.text)
            for item in root.findall(".//item")[:5]:
                desc = item.findtext("description") or ""
                # 挑選 9~13 字母的進階英文單字作為每日擴充候選
                tokens = re.findall(r"\b[a-z]{9,13}\b", desc.lower())
                for tok in tokens[:2]:
                    info = fetch_dictionary_enrichment(tok)
                    if info and info["enDef"]:
                        harvested.append({
                            "id": f"daily_{tok}_{datetime.utcnow().strftime('%Y%m%d')}",
                            "word": tok,
                            "ipa": info["ipa"],
                            "pos": info["pos"],
                            "zh": f"[每日新聞精選] {info['enDef']}",
                            "enDef": info["enDef"],
                            "collocations": f"{tok} (Daily News Context)",
                            "example": info["example"] or desc.strip(),
                            "source": f"Daily Auto-Sync ({datetime.utcnow().strftime('%Y-%m-%d')})",
                            "part": "Reading",
                            "freq": True
                        })
        except Exception:
            continue
    return harvested


def update_databases():
    existing_vocab = load_json(VOCAB_FILE, [])
    existing_words = {v["word"].lower() for v in existing_vocab}

    # 1. 補齊核心 IELTS 7.5+ 與美劇高頻詞庫
    for idx, item in enumerate(CANDIDATE_POOL):
        if item["word"].lower() not in existing_words:
            enriched = fetch_dictionary_enrichment(item["word"]) or {}
            existing_vocab.append({
                "id": f"core_{idx+1}",
                "word": item["word"],
                "ipa": enriched.get("ipa", ""),
                "pos": enriched.get("pos", "vocab"),
                "zh": item["zh"],
                "enDef": enriched.get("enDef", ""),
                "collocations": f"{item['word']} in IELTS context",
                "example": enriched.get("example") or f"Using '{item['word']}' appropriately elevates your IELTS Band score.",
                "source": item["source"],
                "part": item["part"],
                "freq": item["freq"]
            })
            existing_words.add(item["word"].lower())

    # 2. 每日自動從國際新聞語料擴充新詞（每次最多新增 3 筆保持高品質）
    daily_new = fetch_daily_news_vocab()
    added_today = 0
    for d_item in daily_new:
        if d_item["word"].lower() not in existing_words and added_today < 3:
            existing_vocab.append(d_item)
            existing_words.add(d_item["word"].lower())
            added_today += 1

    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_vocab, f, ensure_ascii=False, indent=2)

    # 3. 同步更新 ielts_bank.json 內的動態選擇題池
    bank = load_json(BANK_FILE, {"listening": [], "reading": [], "writing": [], "speaking": [], "quizPool": []})
    quiz_pool = bank.get("quizPool", [])
    existing_q_ids = {q["id"] for q in quiz_pool}

    valid_for_quiz = [v for v in existing_vocab if v.get("example") and v["word"].lower() in v["example"].lower()]
    random.shuffle(valid_for_quiz)

    for v in valid_for_quiz[:15]:
        qid = f"auto_q_{v['word'].lower().replace(' ', '_')}"
        if qid in existing_q_ids:
            continue
        pattern = re.compile(re.escape(v["word"]), re.IGNORECASE)
        masked = pattern.sub("________", v["example"], count=1)
        distractors = [x["word"] for x in existing_vocab if x["word"].lower() != v["word"].lower()]
        if len(distractors) >= 3:
            opts = random.sample(distractors, 3) + [v["word"]]
            random.shuffle(opts)
            quiz_pool.append({
                "id": qid,
                "tag": f"每日自動出題 · {v['source']}",
                "question": f"請選出最適合填入句中空格的單字或片語：\n\"{masked}\"",
                "options": opts,
                "answer": v["word"],
                "explanation": f"正確答案為「{v['word']}」：{v['zh']}"
            })

    bank["quizPool"] = quiz_pool[-60:]  # 保留最新 60 題真題與動態題
    with open(BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)

    print(f"更新完成！目前總詞庫：{len(existing_vocab)} 筆，題庫：{len(bank['quizPool'])} 題。")


if __name__ == "__main__":
    update_databases()
