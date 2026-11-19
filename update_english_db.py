import json
import requests

BANK_FILE = "pop_culture_bank.json"

POP_SEED_BANK = [
    # 破產姊妹 (2 Broke Girls)
    {"id": "d_2bg_1", "category": "drama", "work": "破產姊妹", "workEn": "2 Broke Girls", "subTitle": "Max & Caroline 創業日常", "target": "flat broke", "zh": "身無分文、徹底破產", "quote": "We are not just broke, we are flat broke with zero backup plan.", "nuance": "flat 在口語中表「徹底地」，flat broke 比單講 broke 更有戲劇張力。", "freq": True},
    {"id": "d_2bg_2", "category": "drama", "work": "破產姊妹", "workEn": "2 Broke Girls", "subTitle": "美式直率吐槽", "target": "sugarcoat", "zh": "美化、粉飾太平（講好聽話）", "quote": "Do not sugarcoat it—tell me straight if the cupcake batch tastes awful.", "nuance": "字面是「裹糖衣」，Max 常說 I don't sugarcoat things，意為有話直說。", "freq": True},
    {"id": "d_2bg_3", "category": "drama", "work": "破產姊妹", "workEn": "2 Broke Girls", "subTitle": "紐約打拚精神", "target": "hustle", "zh": "拚命打拚、積極找門路賺錢", "quote": "In New York, if you do not hustle every single day, you get left behind.", "nuance": "side hustle 即為「副業」，hustle 兼具忙得不可開交與努力賺錢之意。", "freq": True},
    {"id": "d_2bg_4", "category": "drama", "work": "破產姊妹", "workEn": "2 Broke Girls", "subTitle": "精打細算對話", "target": "pinch pennies", "zh": "精打細算、省吃儉用", "quote": "When you are saving up for a storefront, you have to pinch pennies on everything.", "nuance": "字面是「捏緊每一分錢」，形容預算極度吃緊時精打細算過日子。", "freq": True},

    # 同路人 (Fellow Travelers)
    {"id": "d_ft_1", "category": "drama", "work": "同路人", "workEn": "Fellow Travelers", "subTitle": "1950s 華府政壇暗湧", "target": "keep a low profile", "zh": "保持低調、避免引人注目", "quote": "With the Senate committee investigating everyone, you need to keep a low profile.", "nuance": "高壓政治與職場環境下最實用的生存表達。", "freq": True},
    {"id": "d_ft_2", "category": "drama", "work": "同路人", "workEn": "Fellow Travelers", "subTitle": "外交官與國會幕僚對話", "target": "read between the lines", "zh": "體會言外之意、聽出弦外之音", "quote": "In Washington, survival depends on your ability to read between the lines.", "nuance": "指從字裡行間讀懂對方未明說的真正意圖。", "freq": True},
    {"id": "d_ft_3", "category": "drama", "work": "同路人", "workEn": "Fellow Travelers", "subTitle": "跨越數十年的承諾", "target": "weather the storm", "zh": "渡過難關、安然度過風暴", "quote": "No matter how fierce the political backlash gets, we will weather the storm together.", "nuance": "weather 作動詞時意為「經受住、安全熬過危機」。", "freq": True},

    # 六人行 (Friends)
    {"id": "d_fr_1", "category": "drama", "work": "六人行", "workEn": "Friends", "subTitle": "Central Perk 經典感情梗", "target": "on a break", "zh": "暫時分開冷靜一下（感情暫停期）", "quote": "Ross insisted for ten seasons that they were on a break!", "nuance": "感情關係中的暫時冷靜期，不同於正式分手 break up。", "freq": True},
    {"id": "d_fr_2", "category": "drama", "work": "六人行", "workEn": "Friends", "subTitle": "Chandler 招牌反問句", "target": "could it be any more", "zh": "難道還能更……嗎？（反諷強調語氣）", "quote": "Could that outfit be any more obvious when you are trying to impress her?", "nuance": "Chandler Bing 最具代表性的重讀反問句型。", "freq": True},
    {"id": "d_fr_3", "category": "drama", "work": "六人行", "workEn": "Friends", "subTitle": "Joey 經典諧音梗", "target": "moo point", "zh": "毫無意義的觀點（源自 moot point）", "quote": "It is like a cow’s opinion—it just does not matter, it is a moo point.", "nuance": "正確單字為 moot point（無實際意義的爭論點），Joey 誤聽為牛叫聲 moo。", "freq": True},

    # 摩登家庭 (Modern Family)
    {"id": "d_mf_1", "category": "drama", "work": "摩登家庭", "workEn": "Modern Family", "subTitle": "Phil Dunphy 酷爸哲學", "target": "peer pressure", "zh": "同儕壓力", "quote": "I am not just a dad; I am a cool dad who understands peer pressure.", "nuance": "討論青少年社交與教育議題的高頻詞彙。", "freq": True},
    {"id": "d_mf_2", "category": "drama", "work": "摩登家庭", "workEn": "Modern Family", "subTitle": "Gloria 聽力誤會金句", "target": "dog-eat-dog world", "zh": "弱肉強食、競爭極度殘酷的世界", "quote": "Gloria misheard it as a doggy-dog world instead of a dog-eat-dog world.", "nuance": "形容競爭殘酷的商業與現實社會。", "freq": True},
    {"id": "d_mf_3", "category": "drama", "work": "摩登家庭", "workEn": "Modern Family", "subTitle": "Claire 完美主義日常", "target": "control freak", "zh": "控制狂（事事都要掌控的人）", "quote": "Everyone calls me a control freak, yet nothing gets done unless I plan it.", "nuance": "freak 接在名詞後表示對某事極度執著的人。", "freq": True},

    # 9 大西洋歌手
    {"id": "s_ts_1", "category": "singer", "work": "Taylor Swift", "workEn": "Bad Blood / Shake It Off", "subTitle": "代表作高頻口語", "target": "bad blood", "zh": "積怨、深仇大恨、不和", "quote": "After that public fallout, there was clearly bad blood between the two former allies.", "nuance": "形容兩人之間長期的敵意與心結。", "freq": True},
    {"id": "s_ts_2", "category": "singer", "work": "Taylor Swift", "workEn": "Shake It Off", "subTitle": "豁達面對批評", "target": "shake it off", "zh": "擺脫負面情緒、不把批評放在心上", "quote": "Whenever critics question your ambition, the best response is to just shake it off.", "nuance": "迅速走出低潮、不被流言影響。", "freq": True},
    {"id": "s_ag_1", "category": "singer", "work": "Ariana Grande", "workEn": "thank u, next", "subTitle": "逆境轉機隱喻", "target": "silver lining", "zh": "黑暗中的一線希望、因禍得福的正面收穫", "quote": "Even a painful breakup carries a silver lining when it teaches you self-reliance.", "nuance": "源自諺語 Every cloud has a silver lining。", "freq": True},
    {"id": "s_ss_1", "category": "singer", "work": "Sam Smith", "workEn": "Stay With Me", "subTitle": "內心掙扎表達", "target": "second-guess", "zh": "事後懷疑、猶豫不決、自我懷疑", "quote": "Stop second-guessing every decision you make once you have already committed to it.", "nuance": "做出決定後不斷回頭懷疑自己。", "freq": True},
    {"id": "s_cp_1", "category": "singer", "work": "Charlie Puth", "workEn": "Attention", "subTitle": "感情心理學片語", "target": "string someone along", "zh": "吊著某人胃口、給人虛假希望", "quote": "She was never genuinely interested; she was just stringing him along for attention.", "nuance": "故意讓對方抱有期待卻不給承諾。", "freq": True},
    {"id": "s_sm_1", "category": "singer", "work": "Shawn Mendes", "workEn": "There’s Nothing Holdin’ Me Back", "subTitle": "突破自我限制", "target": "hold someone back", "zh": "阻礙某人前進、使有所顧忌", "quote": "Fear of failure is the only thing holding you back from pursuing your dream.", "nuance": "常用於鼓勵或討論心理障礙。", "freq": True},
    {"id": "s_lv_1", "category": "singer", "work": "Lauv", "workEn": "I Like Me Better", "subTitle": "都會情感內心獨白", "target": "overthink", "zh": "過度胡思亂想、鑽牛角尖", "quote": "Late at night, it is all too easy to overthink every small conversation from the day.", "nuance": "現代年輕世代最高頻心理動詞。", "freq": True},
    {"id": "s_ch_1", "category": "singer", "work": "Christopher", "workEn": "Bad", "subTitle": "流行舞曲社交金句", "target": "play hard to get", "zh": "欲擒故縱、故意裝作冷淡難追", "quote": "At first I thought she was playing hard to get, until I realized she meant every word.", "nuance": "故意表現難以親近以吸引對方注意。", "freq": True},
    {"id": "s_lg_1", "category": "singer", "work": "Lady Gaga", "workEn": "Shallow", "subTitle": "奧斯卡金曲隱喻", "target": "off the deep end", "zh": "情緒失控、陷入狂熱或徹底豁出去", "quote": "Together they dove off the deep end, leaving their old comfort zones far behind.", "nuance": "象徵無所畏懼地躍入未知領域。", "freq": True},
    {"id": "s_be_1", "category": "singer", "work": "Billie Eilish", "workEn": "Birds of a Feather", "subTitle": "經典英語諺語", "target": "birds of a feather", "zh": "物以類聚、志趣相投的人", "quote": "As the old saying goes, birds of a feather flock together through thick and thin.", "nuance": "形容性格或品味相同的人自然會聚在一起。", "freq": True}
]


def main():
    try:
        with open(BANK_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception:
        existing = []

    merged = {item["id"]: item for item in existing}
    for seed in POP_SEED_BANK:
        merged[seed["id"]] = seed

    result = list(merged.values())
    with open(BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ 已更新 {BANK_FILE}，共收錄 {len(result)} 則美劇與西洋金曲精選題庫！")


if __name__ == "__main__":
    main()
