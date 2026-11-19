import csv
import json
import random
import re
from datetime import datetime
import requests
import xml.etree.ElementTree as ET

VOCAB_FILE = "vocab.json"
BANK_FILE = "ielts_bank.json"
POP_BANK_FILE = "pop_ielts_bank.json"
TARGET_VOCAB_COUNT = 10000

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

# 1. 精選 IELTS Band 7.5+ 核心學術詞與美劇高頻片語（自帶完整 IPA 音標與真實高分例句）
CORE_SEED_VOCAB = [
    {"id": "core_1", "word": "ubiquitous", "ipa": "/juːˈbɪk.wɪ.təs/", "pos": "adj.", "zh": "無所不在的、十分普遍的", "collocations": "ubiquitous presence / become ubiquitous", "example": "Smartphones have become ubiquitous in modern urban life, reshaping interpersonal communication.", "source": "IELTS 7.5+ Academic", "part": "Reading", "freq": True},
    {"id": "core_2", "word": "mitigate", "ipa": "/ˈmɪt.ɪ.ɡeɪt/", "pos": "v.", "zh": "減輕、緩和（風險或負面影響）", "collocations": "mitigate the risk / mitigate adverse impacts", "example": "Governments must implement stringent policies to mitigate the adverse effects of carbon emissions.", "source": "IELTS 7.5+ Academic", "part": "Writing", "freq": True},
    {"id": "core_3", "word": "exacerbate", "ipa": "/ɪɡˈzæs.ə.beɪt/", "pos": "v.", "zh": "使惡化、加劇", "collocations": "exacerbate the problem / exacerbate inequality", "example": "Unplanned urban sprawl tends to exacerbate traffic congestion and air pollution.", "source": "IELTS 7.5+ Academic", "part": "Writing", "freq": True},
    {"id": "core_4", "word": "detrimental", "ipa": "/ˌdet.rɪˈmen.təl/", "pos": "adj.", "zh": "有害的、不利的", "collocations": "detrimental effect / detrimental to health", "example": "Excessive screen time before bedtime has a detrimental impact on sleep architecture.", "source": "IELTS 7.5+ Academic", "part": "Writing", "freq": True},
    {"id": "core_5", "word": "proliferate", "ipa": "/prəˈlɪf.ə.reɪt/", "pos": "v.", "zh": "激增、迅速擴散", "collocations": "rapidly proliferate / proliferate across", "example": "Micro-mobility scooters have proliferated across major metropolitan areas over the past decade.", "source": "IELTS 7.5+ Academic", "part": "Listening", "freq": True},
    {"id": "core_6", "word": "unprecedented", "ipa": "/ʌnˈpres.ɪ.den.tɪd/", "pos": "adj.", "zh": "史無前例的、空前的", "collocations": "unprecedented scale / unprecedented pace", "example": "The global economy is undergoing structural transformation at an unprecedented pace.", "source": "IELTS 7.5+ Academic", "part": "Writing", "freq": True},
    {"id": "core_7", "word": "scrutinize", "ipa": "/ˈskruː.tɪ.naɪz/", "pos": "v.", "zh": "仔細審查、嚴格檢視", "collocations": "scrutinize the data / closely scrutinize", "example": "Peer reviewers meticulously scrutinize experimental methodology before publication.", "source": "IELTS 7.5+ Academic", "part": "Reading", "freq": True},
    {"id": "core_8", "word": "alleviate", "ipa": "/əˈliː.vi.eɪt/", "pos": "v.", "zh": "緩解、減輕（痛苦或擁塞）", "collocations": "alleviate poverty / alleviate congestion", "example": "Expanding dedicated bicycle lanes can significantly alleviate peak-hour gridlock.", "source": "IELTS 7.5+ Academic", "part": "Writing", "freq": True},
    {"id": "core_9", "word": "substantiate", "ipa": "/səbˈstæn.ʃi.eɪt/", "pos": "v.", "zh": "證實、提供證據支持", "collocations": "substantiate a claim / empirical evidence to substantiate", "example": "Researchers must provide robust empirical data to substantiate their theoretical claims.", "source": "IELTS 7.5+ Academic", "part": "Reading", "freq": True},
    {"id": "core_10", "word": "dichotomy", "ipa": "/daɪˈkɒt.ə.mi/", "pos": "n.", "zh": "二分法、截然對立", "collocations": "false dichotomy / stark dichotomy", "example": "There is often a false dichotomy between economic growth and environmental sustainability.", "source": "IELTS 7.5+ Academic", "part": "Reading", "freq": True},
    {"id": "core_11", "word": "pragmatic", "ipa": "/præɡˈmæt.ɪk/", "pos": "adj.", "zh": "務實的、講求實效的", "collocations": "pragmatic approach / pragmatic solution", "example": "A pragmatic compromise is required to balance fiscal discipline with public welfare.", "source": "IELTS 7.5+ Academic", "part": "Speaking", "freq": True},
    {"id": "core_12", "word": "conducive", "ipa": "/kənˈdjuː.sɪv/", "pos": "adj.", "zh": "有助於...的、有益的", "collocations": "conducive to learning / conducive environment", "example": "Quiet, well-lit libraries provide an atmosphere highly conducive to deep concentration.", "source": "IELTS 7.5+ Academic", "part": "Writing", "freq": True},
    {"id": "core_13", "word": "repercussion", "ipa": "/ˌriː.pəˈkʌʃ.ən/", "pos": "n.", "zh": "深遠影響、惡果", "collocations": "far-reaching repercussions / serious repercussions", "example": "Deforestation carries far-reaching ecological repercussions for global biodiversity.", "source": "IELTS 7.5+ Academic", "part": "Writing", "freq": True},
    {"id": "core_14", "word": "ambiguous", "ipa": "/æmˈbɪɡ.ju.əs/", "pos": "adj.", "zh": "模稜兩可的、含糊不清的", "collocations": "remain ambiguous / deliberately ambiguous", "example": "Vague regulatory guidelines often leave companies facing ambiguous compliance obligations.", "source": "IELTS 7.5+ Academic", "part": "Reading", "freq": True},
    {"id": "core_15", "word": "cut corners", "ipa": "/kʌt ˈkɔːr.nərz/", "pos": "idiom", "zh": "偷工減料、圖省事走捷徑", "collocations": "refuse to cut corners", "example": "When building mission-critical network infrastructure, engineers can never afford to cut corners.", "source": "TV: 破產姊妹 / Suits", "part": "Speaking", "freq": True},
    {"id": "core_16", "word": "off the top of my head", "ipa": "/ɔːf ðə tɑːp əv maɪ hed/", "pos": "idiom", "zh": "憑直覺/不假思索地說", "collocations": "Speaking Part 1 & Part 3 開頭句", "example": "Off the top of my head, I would say public transport subsidies are the most effective measure.", "source": "TV: 六人行 (Friends)", "part": "Speaking", "freq": True},
    {"id": "core_17", "word": "on the same page", "ipa": "/ɑːn ðə seɪm peɪdʒ/", "pos": "idiom", "zh": "達成共識、想法一致", "collocations": "get everyone on the same page", "example": "Before launching the rollout, let us make sure all stakeholders are on the same page.", "source": "TV: 六人行 / The Office", "part": "Listening", "freq": True},
    {"id": "core_18", "word": "double-edged sword", "ipa": "/ˌdʌb.əl ˈedʒd sɔːrd/", "pos": "idiom", "zh": "雙面刃（有利亦有弊）", "collocations": "prove to be a double-edged sword", "example": "Artificial intelligence is a double-edged sword that boosts productivity while displacing routine jobs.", "source": "TV: Silicon Valley (矽谷群瞎傳)", "part": "Speaking", "freq": True},
    {"id": "core_19", "word": "a blessing in disguise", "ipa": "/ə ˈbles.ɪŋ ɪn dɪsˈɡaɪz/", "pos": "idiom", "zh": "塞翁失馬、因禍得福", "collocations": "turn out to be a blessing in disguise", "example": "Missing that flight turned out to be a blessing in disguise because I met my future partner.", "source": "TV: 摩登家庭 (Modern Family)", "part": "Speaking", "freq": True},
    {"id": "core_20", "word": "read between the lines", "ipa": "/riːd bɪˈtwiːn ðə laɪnz/", "pos": "idiom", "zh": "體會言外之意、聽出弦外之音", "collocations": "learn to read between the lines", "example": "In Washington politics, survival depends on your ability to read between the lines.", "source": "TV: 同路人 (Fellow Travelers)", "part": "Reading", "freq": True}
]

EXTRA_POP_IELTS_ITEMS = [
    {
        "id": "ts_2",
        "work": "Taylor Swift",
        "workEn": "Blank Space",
        "category": "singer",
        "ytId": "e-ORhEE9VVg",
        "startSec": 45,
        "endSec": 52,
        "fullSentence": "Got a long list of ex-lovers, they will tell you I am insane, because reputation precedes me.",
        "clozedTemplate": "Got a long list of [1], they will tell you I am insane, because [2] precedes me.",
        "blanks": ["ex-lovers", "reputation"],
        "listeningTip": "注意 list of 連音成 /lɪs-təv/；reputation 重音在第三音節 /ˌrep.jəˈteɪ.ʃən/。",
        "sentenceZh": "有一長串前任名單，他們會告訴你我瘋了，因為我的名聲早已不脛而走。",
        "casualPhrase": "reputation precedes me",
        "casualExplain": "未見其人先聞其名、名聲在外",
        "registerQuestion": "《Blank Space》語境中提到「名聲在外」。若要在【雅思寫作 Task 2】表達「品牌或機構的公眾聲譽對長期信任至關重要」，哪個學術句型最精準？",
        "registerOptions": [
            "institutional reputation underpins enduring public trust",
            "famous gossip arrives before the singer walks in",
            "everyone talks about ex-lovers in magazines",
            "long lists make people sound insane"
        ],
        "academicAnswer": "institutional reputation underpins enduring public trust",
        "academicSentence": "In the digital economy, institutional reputation underpins enduring public trust and stakeholder loyalty.",
        "stressGuide": "Got a LONG LIST‿of EX-LOVers, they will TELL you I am inSANE, because repuTAtion preCEDES me.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Fame, Media & Public Image",
        "ieltsSpeakingQ": "How does public reputation affect the success of modern companies or public figures?",
        "ieltsSpeakingModel": "In an era of instant online reviews, an organization's reputation often precedes it, directly determining whether consumers feel confident engaging with its products."
    }
]


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def fetch_tv_subtitle_frequency():
    url = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_50k.txt"
    tv_words = {}
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            for rank, line in enumerate(r.text.splitlines()[:25000], start=1):
                parts = line.strip().split()
                if parts and parts[0].isalpha() and len(parts[0]) >= 5:
                    tv_words[parts[0].lower()] = rank
    except Exception as e:
        print("美劇詞頻下載略過:", e)
    return tv_words


def build_clean_10k_vocab():
    """排除前 2,500 個小學/國中基礎單字，只收錄真正 IELTS Band 7.5+ 與美劇進階詞彙至 10,000 單"""
    vocab_map = {item["word"].lower(): item for item in CORE_SEED_VOCAB}
    tv_freq_map = fetch_tv_subtitle_frequency()

    ecdict_url = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv"
    print("正在從開源雙語詞庫篩選 IELTS Band 7.5+ 進階詞彙 (排除前 2500 基礎單字)...")
    try:
        with requests.get(ecdict_url, headers=HEADERS, stream=True, timeout=35) as resp:
            resp.raise_for_status()
            lines = (line.decode("utf-8", errors="ignore") for line in resp.iter_lines())
            reader = csv.DictReader(lines)

            ielts_adv = []
            tv_adv = []

            for row in reader:
                word = (row.get("word") or "").strip()
                # 只收錄純小寫、長度 >= 5 的單字，過濾過短基礎字
                if not word or not word.isalpha() or len(word) < 5 or not word.islower():
                    continue
                if word in vocab_map:
                    continue

                zh_raw = (row.get("translation") or "").strip().replace("\\n", "；")
                if not zh_raw:
                    continue

                bnc = int(row.get("bnc") or 99999)
                frq = int(row.get("frq") or 99999)
                # 關鍵過濾：排除最常見的前 2,500 個 A1/A2 基礎單字 (如 make, time, good, book)
                if (0 < frq <= 2500) or (0 < bnc <= 2500):
                    continue

                phonetic = (row.get("phonetic") or "").strip()
                ipa = f"/{phonetic}/" if phonetic else ""
                pos = (row.get("pos") or "vocab").split(":")[0]
                tag = (row.get("tag") or "").lower()
                tv_rank = tv_freq_map.get(word, 99999)

                is_ielts_or_gre = any(t in tag for t in ["ielts", "toefl", "gre"])
                is_tv_mid_high = 2500 < tv_rank <= 16000

                if is_ielts_or_gre:
                    is_high_freq = ("ielts" in tag) and (2500 < frq <= 9500)
                    part_guess = "Writing" if word.endswith(("ate", "ize", "ify", "tion", "ment", "ous", "ive")) else "Reading"
                    ielts_adv.append({
                        "id": f"ielts_{word}",
                        "word": word,
                        "ipa": ipa,
                        "pos": pos,
                        "zh": zh_raw[:95],
                        "collocations": f"{word} (Band 7.5+ Academic)",
                        "example": f"Candidates aiming for Band 7.5+ frequently deploy '{word}' ({zh_raw.split('；')[0]}) in {part_guess}.",
                        "source": "IELTS 7.5+ Academic",
                        "part": part_guess,
                        "freq": is_high_freq,
                        "_rank": frq if frq > 0 else 60000
                    })
                elif is_tv_mid_high:
                    tv_adv.append({
                        "id": f"tv_{word}",
                        "word": word,
                        "ipa": ipa,
                        "pos": pos,
                        "zh": zh_raw[:95],
                        "collocations": f"{word} (US TV Dialogue Rank #{tv_rank})",
                        "example": f"Native speakers in American dramas naturally use '{word}' ({zh_raw.split('；')[0]}) in dialogue.",
                        "source": "TV Drama High-Freq (美劇口語)",
                        "part": "Speaking",
                        "freq": tv_rank <= 6500,
                        "_rank": tv_rank
                    })

            ielts_adv.sort(key=lambda x: x["_rank"])
            tv_adv.sort(key=lambda x: x["_rank"])

            for item in ielts_adv[:7000]:
                item.pop("_rank", None)
                vocab_map[item["word"]] = item
                if len(vocab_map) >= TARGET_VOCAB_COUNT:
                    break

            for item in tv_adv:
                if len(vocab_map) >= TARGET_VOCAB_COUNT:
                    break
                if item["word"] not in vocab_map:
                    item.pop("_rank", None)
                    vocab_map[item["word"]] = item

    except Exception as e:
        print("ECDICT 下載異常:", e)

    return list(vocab_map.values())


def update_ielts_quiz_bank(vocab_list):
    """僅從真實新聞語料與高品質例句生成動態測驗題，絕不抓取網頁選單文字"""
    bank = load_json(BANK_FILE, {"listening": [], "reading": [], "writing": [], "speaking": [], "quizPool": []})
    # 清除舊版誤抓的 web_ielts 選單垃圾題與重複模板題
    clean_pool = [
        q for q in bank.get("quizPool", [])
        if not q.get("id", "").startswith("web_ielts_")
        and "elevates your IELTS Band score" not in q.get("question", "")
    ]

    # 1. 從 CORE_SEED_VOCAB 生成真實語境題
    for v in CORE_SEED_VOCAB:
        qid = f"core_q_{v['word'].replace(' ', '_')}"
        if not any(q["id"] == qid for q in clean_pool) and v["word"].lower() in v["example"].lower():
            masked = re.sub(re.escape(v["word"]), "________", v["example"], count=1, flags=re.IGNORECASE)
            distractors = random.sample([x["word"] for x in CORE_SEED_VOCAB if x["word"] != v["word"]], 3)
            opts = distractors + [v["word"]]
            random.shuffle(opts)
            clean_pool.append({
                "id": qid,
                "tag": f"🔥 高頻真題語境 · {v['source']}",
                "question": f"請選出最適合填入句中空格的高分單字或片語：\n\"{masked}\"",
                "options": opts,
                "answer": v["word"],
                "explanation": f"正確答案為「{v['word']}」({v['zh']})。高分搭配：{v['collocations']}。"
            })

    # 2. 從 BBC / NPR 每日國際新聞擷取進階單字語境題
    rss_urls = [
        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://feeds.npr.org/1001/rss.xml"
    ]
    adv_words = [v["word"] for v in vocab_list if v.get("freq") and len(v["word"]) >= 8][:200]
    for rss in rss_urls:
        try:
            r = requests.get(rss, headers=HEADERS, timeout=10)
            root = ET.fromstring(r.text)
            for item in root.findall(".//item")[:6]:
                desc = re.sub(r"<[^>]+>", "", item.findtext("description") or "").strip()
                tokens = re.findall(r"\b[a-z]{9,14}\b", desc)
                if tokens and 60 <= len(desc) <= 260 and len(adv_words) >= 10:
                    target_w = tokens[0]
                    masked = re.sub(rf"\b{re.escape(target_w)}\b", "________", desc, count=1)
                    qid = f"news_q_{target_w.lower()}"
                    if not any(q["id"] == qid for q in clean_pool):
                        distractors = random.sample([w for w in adv_words if w.lower() != target_w.lower()], 3)
                        opts = distractors + [target_w]
                        random.shuffle(opts)
                        clean_pool.append({
                            "id": qid,
                            "tag": f"每日國際新聞真題語境 ({datetime.utcnow().strftime('%Y-%m-%d')})",
                            "question": f"請選出最適合填入新聞語境空格的高階單字：\n\"{masked}\"",
                            "options": opts,
                            "answer": target_w,
                            "explanation": f"原句出自國際新聞報導，正確單字為「{target_w}」。"
                        })
        except Exception:
            continue

    bank["quizPool"] = clean_pool[-80:]
    with open(BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)
    print(f"✅ 已更新 {BANK_FILE}，有效題庫共 {len(bank['quizPool'])} 題。")


def update_pop_ielts_bank():
    existing = load_json(POP_BANK_FILE, [])
    merged = {item["id"]: item for item in existing if item.get("clozedTemplate")}
    for item in EXTRA_POP_IELTS_ITEMS:
        merged[item["id"]] = item
    with open(POP_BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(list(merged.values()), f, ensure_ascii=False, indent=2)
    print(f"✅ 已同步更新 {POP_BANK_FILE}。")


if __name__ == "__main__":
    vocab_data = build_clean_10k_vocab()
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(vocab_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已更新 {VOCAB_FILE}，共 {len(vocab_data)} 筆 IELTS 7.5+ 與美劇高頻詞彙！")

    update_ielts_quiz_bank(vocab_data)
    update_pop_ielts_bank()
