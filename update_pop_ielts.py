import json

BANK_FILE = "pop_ielts_bank.json"

# 可持續在此新增更多美劇台詞與歌手金曲的 YouTube 秒數區間與雅思學術替換對照
EXTRA_POP_ITEMS = [
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


def main():
    try:
        with open(BANK_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception:
        existing = []

    merged = {item["id"]: item for item in existing}
    for item in EXTRA_POP_ITEMS:
        merged[item["id"]] = item

    with open(BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(list(merged.values()), f, ensure_ascii=False, indent=2)

    print(f"✅ 已更新 {BANK_FILE}，目前自訂擴充題庫共 {len(merged)} 題。")


if __name__ == "__main__":
    main()
