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
    {"id": "core_15", "word": "behind closed doors", "ipa": "/bɪˈhaɪnd kloʊzd dɔːrz/", "pos": "idiom", "zh": "私下地、秘密地（不公開）", "collocations": "negotiate behind closed doors", "example": "In Washington politics, crucial compromises are frequently brokered behind closed doors.", "source": "TV: 同路人 (Fellow Travelers)", "part": "Reading", "freq": True},
    {"id": "core_16", "word": "off the record", "ipa": "/ɔːf ðə ˈrek.ɚd/", "pos": "idiom", "zh": "非公開地、不可引述地", "collocations": "speak strictly off the record", "example": "The senior official agreed to brief journalists strictly off the record.", "source": "TV: 同路人 (Fellow Travelers)", "part": "Listening", "freq": True},
    {"id": "core_17", "word": "bide your time", "ipa": "/baɪd jʊr taɪm/", "pos": "idiom", "zh": "耐心等待時機、韜光養晦", "collocations": "bide one's time until", "example": "When the political climate turns hostile, you have to bide your time and pick your battles.", "source": "TV: 同路人 (Fellow Travelers)", "part": "Speaking", "freq": True},
    {"id": "core_18", "word": "think on your feet", "ipa": "/θɪŋk ɑːn jʊr fiːt/", "pos": "idiom", "zh": "臨機應變、反應敏捷", "collocations": "ability to think on your feet", "example": "If you want to survive the night shift at the diner, you have to think on your feet.", "source": "TV: 破產姊妹 (2 Broke Girls)", "part": "Speaking", "freq": True},
    {"id": "core_19", "word": "out of the question", "ipa": "/aʊt əv ðə ˈkwes.tʃən/", "pos": "idiom", "zh": "絕不可能、想都別想", "collocations": "completely out of the question", "example": "Everyone knows Joey does not share food, so touching his fries is out of the question.", "source": "TV: 六人行 (Friends)", "part": "Speaking", "freq": True},
    {"id": "core_20", "word": "make ends meet", "ipa": "/meɪk endz miːt/", "pos": "idiom", "zh": "維持生計、收支平衡", "collocations": "struggle to make ends meet", "example": "Rising inflation makes it increasingly difficult for low-income families to make ends meet.", "source": "Song: Ariana Grande", "part": "Speaking", "freq": True}
]

EXTRA_POP_IELTS_ITEMS = [
    {
        "id": "ft_2",
        "work": "同路人",
        "workEn": "Fellow Travelers · State Department Secrecy",
        "category": "drama",
        "ytId": "",
        "startSec": 0,
        "endSec": 7,
        "fullSentence": "Never put anything in writing; in this town, every sensitive conversation happens behind closed doors and strictly off the record.",
        "clozedTemplate": "Never put anything in writing; in this town, every sensitive conversation happens [1] and strictly [2].",
        "blanks": ["behind closed doors", "off the record"],
        "listeningTip": "注意 put anything 連讀成 /pʊ-ˈtɛn.i.θɪŋ/；off the record 中 off 與 the 連讀順暢。",
        "sentenceZh": "千萬別留下任何白紙黑字的紀錄；在這座政治城市裡，每場敏感對話都在私下閉門進行，且嚴格不公開紀錄。",
        "casualPhrase": "behind closed doors / off the record",
        "casualExplain": "私下閉門進行 / 非公開、不可引述",
        "registerQuestion": "《同路人》中 Hawkins 告誡年輕幕僚重要協商都在 \"behind closed doors and off the record\"。若要在【雅思寫作 Task 2】論述「外交談判有時需要高度保密，以避免過早受到輿論干擾」，哪個學術替換最精準？",
        "registerOptions": [
            "conduct confidential deliberations without premature public disclosure",
            "lock all wooden office doors and turn off tape recorders",
            "write secret letters inside quiet Washington apartments",
            "avoid speaking to any newspaper reporters permanently"
        ],
        "academicAnswer": "conduct confidential deliberations without premature public disclosure",
        "academicSentence": "Complex international peace negotiations often require diplomats to conduct confidential deliberations without premature public disclosure.",
        "stressGuide": "NEVer PUT ANything in WRITing; EVery SENsitive converSAtion HAPpens beHIND CLOSED DOORS and STRICTly OFF the RECord.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Government Transparency & Privacy",
        "ieltsSpeakingQ": "Should governments make all political discussions public, or are private negotiations sometimes necessary?",
        "ieltsSpeakingModel": "While democratic accountability is vital, I believe sensitive diplomatic talks often need to happen behind closed doors initially, as confidential deliberations allow leaders to compromise without political posturing."
    },
    {
        "id": "ft_3",
        "work": "同路人",
        "workEn": "Fellow Travelers · Walking a Tightrope",
        "category": "drama",
        "ytId": "",
        "startSec": 0,
        "endSec": 7,
        "fullSentence": "You spend every day walking a tightrope between your conscience and your ambition, terrified of making one false move.",
        "clozedTemplate": "You spend every day [1] between your conscience and your ambition, terrified of making one [2].",
        "blanks": ["walking a tightrope", "false move"],
        "listeningTip": "注意 walking a tightrope 連讀成 /ˈwɔː.kɪ.ŋə-ˈtaɪt.roʊp/；conscience 發音為 /ˈkɑːn.ʃəns/。",
        "sentenceZh": "你每天都在良知與政治野心之間走鋼索，戰戰兢兢深怕走錯任何一步。",
        "casualPhrase": "walking a tightrope / false move",
        "casualExplain": "如履薄冰走鋼索（在兩難間維持微妙平衡）/ 走錯一步",
        "registerQuestion": "《同路人》Tim 對 Hawkins 說他每天都在 \"walking a tightrope between conscience and ambition\"。若要在【雅思寫作 Task 2】描述「政府在刺激經濟成長與實施嚴格環保法規之間必須維持微妙平衡」，哪個學術替換最精準？",
        "registerOptions": [
            "navigate a precarious equilibrium between competing policy imperatives",
            "walk carefully across a circus rope high above the ground",
            "choose personal career ambition over environmental science",
            "avoid making sudden physical movements in the office"
        ],
        "academicAnswer": "navigate a precarious equilibrium between competing policy imperatives",
        "academicSentence": "Policymakers in developing economies must navigate a precarious equilibrium between competing policy imperatives of rapid industrialization and carbon reduction.",
        "stressGuide": "You SPEND EVery DAY WALKing‿a TIGHTrope beTWEEN your CONscience and your amBItion, TERrified of MAK-ing ONE FALSE MOVE.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Ethics & Career Ambition",
        "ieltsSpeakingQ": "Do you think it is possible to achieve high career success without compromising personal values?",
        "ieltsSpeakingModel": "It can certainly feel like walking a tightrope in highly competitive industries, yet I believe long-term credibility depends on maintaining that precarious equilibrium without sacrificing core ethical principles."
    },
    {
        "id": "ft_4",
        "work": "同路人",
        "workEn": "Fellow Travelers · Strategic Patience",
        "category": "drama",
        "ytId": "",
        "startSec": 0,
        "endSec": 7,
        "fullSentence": "When the political climate turns hostile, you cannot fight head-on; you have to bide your time and pick your battles.",
        "clozedTemplate": "When the political climate turns hostile, you cannot fight head-on; you have to [1] and [2].",
        "blanks": ["bide your time", "pick your battles"],
        "listeningTip": "注意 fight head-on 連讀成 /faɪt-he-dɑːn/；bide your time 意為「韜光養晦、耐心等待最佳時機」。",
        "sentenceZh": "當政治氣候變得充滿敵意時，你不能硬碰硬；你必須學會韜光養晦等待時機，並慎選戰場。",
        "casualPhrase": "bide your time / pick your battles",
        "casualExplain": "耐心等待時機 / 慎選戰場（集中精力在關鍵爭端）",
        "registerQuestion": "《同路人》中 Marcus 提醒在逆境中要 \"bide your time and pick your battles\"。若要在【雅思寫作 Task 2】表達「面對有限的公共財政預算，政府必須審慎排定優先順序並等待適當時機推動改革」，哪個學術替換最貼切？",
        "registerOptions": [
            "exercise strategic restraint and prioritize high-impact interventions",
            "wait patiently beside a clock until the battle ends",
            "fight every minor argument in the parliament building",
            "postpone all public healthcare funding indefinitely"
        ],
        "academicAnswer": "exercise strategic restraint and prioritize high-impact interventions",
        "academicSentence": "Constrained by fiscal deficits, municipal authorities must exercise strategic restraint and prioritize high-impact interventions.",
        "stressGuide": "When the poLITical CLIimate TURNS HOStile, you CANnot FIGHT HEAD-ON; you HAVE to BIDE your TIME and PICK your BATtles.",
        "ieltsSpeakingPart": "IELTS Speaking Part 2 · Patience & Strategic Decision-Making",
        "ieltsSpeakingQ": "Describe a time when waiting patiently for the right moment helped you solve a problem.",
        "ieltsSpeakingModel": "During a major network migration with conflicting stakeholder demands, I learned to pick my battles and bide my time until we had empirical performance data, which made consensus effortless."
    },
    {
        "id": "ft_5",
        "work": "同路人",
        "workEn": "Fellow Travelers · Senate Investigation",
        "category": "drama",
        "ytId": "",
        "startSec": 0,
        "endSec": 7,
        "fullSentence": "When investigators start digging into your past, you have to cover your tracks and protect the people you love at all costs.",
        "clozedTemplate": "When investigators start digging into your past, you have to [1] and protect the people you love [2].",
        "blanks": ["cover your tracks", "at all costs"],
        "listeningTip": "注意 digging into 連讀成 /ˈdɪɡ.ɪ.ŋɪn.tuː/；at all costs 中 t 與 all 連讀成 /æ-ɾɔːl-kɑːsts/。",
        "sentenceZh": "當調查人員開始深挖你的過去時，你必須掩蓋行蹤並竭盡全力、不惜一切代價保護你所愛的人。",
        "casualPhrase": "cover your tracks / at all costs",
        "casualExplain": "掩蓋行蹤不留痕跡 / 不惜一切代價",
        "registerQuestion": "《同路人》面對參議院調查時強調必須保護重要之人 \"at all costs\"。若要在【雅思寫作 Task 2】論述「在數位監控日益普及的時代，民主社會必須全力捍衛公民的基本隱私權」，哪個學術表達最有力？",
        "registerOptions": [
            "safeguard fundamental civil liberties as an inviolable priority",
            "erase footprints in the snow behind government buildings",
            "pay expensive legal fees at every court hearing",
            "hide personal documents under the floorboards"
        ],
        "academicAnswer": "safeguard fundamental civil liberties as an inviolable priority",
        "academicSentence": "Even amidst heightened national security concerns, democratic institutions must safeguard fundamental civil liberties as an inviolable priority.",
        "stressGuide": "When inVESTigators START DIGging‿into your PAST, you HAVE to COV-er your TRACKS and proTECT the PEOple you LOVE at ALL COSTS.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Digital Privacy & Surveillance",
        "ieltsSpeakingQ": "How important is it for individuals to protect their personal privacy online nowadays?",
        "ieltsSpeakingModel": "It is paramount. With algorithms constantly digging into users' browsing histories, individuals must take proactive steps to cover their digital tracks and safeguard their personal privacy."
    },
    {
        "id": "ft_6",
        "work": "同路人",
        "workEn": "Fellow Travelers · Moral Courage",
        "category": "drama",
        "ytId": "",
        "startSec": 0,
        "endSec": 7,
        "fullSentence": "Silence only emboldens bullies; sooner or later, you have to stand your ground and speak truth to power.",
        "clozedTemplate": "Silence only emboldens bullies; sooner or later, you have to [1] and [2].",
        "blanks": ["stand your ground", "speak truth to power"],
        "listeningTip": "注意 emboldens 意為「使大膽、助長」；speak truth to power 為政治與社會學經典片語，意為「向當權者直言進諫」。",
        "sentenceZh": "沉默只會助長欺凌者的氣焰；遲早有一天，你必須堅守立場，勇敢向當權者說出真相。",
        "casualPhrase": "stand your ground / speak truth to power",
        "casualExplain": "堅守立場不退讓 / 向當權者直言真理",
        "registerQuestion": "《同路人》Tim 決定不再妥協，要 \"stand your ground and speak truth to power\"。若要在【雅思寫作 Task 2】論述「獨立新聞媒體與吹哨者在揭露制度性腐敗與維護社會正義中扮演不可或缺的角色」，哪個表達最學術？",
        "registerOptions": [
            "hold entrenched institutions accountable through courageous public scrutiny",
            "stand firmly on the floor during loud arguments",
            "shout loudly inside a government power plant",
            "refuse to listen to any historical speeches"
        ],
        "academicAnswer": "hold entrenched institutions accountable through courageous public scrutiny",
        "academicSentence": "Investigative journalism plays an indispensable role in enabling citizens to hold entrenched institutions accountable through courageous public scrutiny.",
        "stressGuide": "SIlence ONly emBOLDens BULlies; SOONer or LATer, you HAVE to STAND your GROUND and SPEAK TRUTH to POWer.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Courage, Justice & Social Change",
        "ieltsSpeakingQ": "What qualities do you think are most important for people who want to bring positive change to society?",
        "ieltsSpeakingModel": "Above all, moral courage and resilience—history shows that meaningful reform only happens when principled individuals stand their ground and speak truth to power despite institutional resistance."
    },
    {
        "id": "2bg_2",
        "work": "破產姊妹",
        "workEn": "2 Broke Girls · Diner Shift",
        "category": "drama",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "If you want to survive the night shift at the diner, you have to think on your feet and keep your cool.",
        "clozedTemplate": "If you want to survive the night shift at the diner, you have to [1] and [2].",
        "blanks": ["think on your feet", "keep your cool"],
        "listeningTip": "注意 think on your 中 think 與 on 連讀成 /θɪŋ-kɑːn/；keep your 連讀成 /kiː-pjɚ/。",
        "sentenceZh": "如果你想在餐館大夜班生存下來，你必須學會臨機應變並保持冷靜。",
        "casualPhrase": "think on your feet / keep your cool",
        "casualExplain": "臨機應變、在壓力下保持冷靜",
        "registerQuestion": "《破產姊妹》強調服務業必須 \"think on your feet and keep your cool\"。若要在【雅思寫作 Task 2】論述「現代醫療與緊急應變人員須具備高壓下的快速應變能力」，哪個學術替換最精準？",
        "registerOptions": [
            "demonstrate cognitive agility and composure under acute pressure",
            "stand on both shoes while thinking about cold weather",
            "walk quickly around the restaurant kitchen at night",
            "keep ice cubes inside the diner freezer"
        ],
        "academicAnswer": "demonstrate cognitive agility and composure under acute pressure",
        "academicSentence": "Frontline emergency personnel must demonstrate cognitive agility and composure under acute pressure during public health crises.",
        "stressGuide": "If you WANT to surVIVE the NIGHT SHIFT, you HAVE to THINK‿on your FEET and KEEP your COOL.",
        "ieltsSpeakingPart": "IELTS Speaking Part 2 / Part 3 · Handling Unexpected Situations",
        "ieltsSpeakingQ": "Describe a job or situation where someone needs to make quick decisions under pressure.",
        "ieltsSpeakingModel": "Working in network operations during an outage requires you to think on your feet and keep your cool, because demonstrating cognitive agility under acute pressure prevents minor glitches from escalating."
    },
    {
        "id": "fr_2",
        "work": "六人行",
        "workEn": "Friends · Joey Doesn't Share Food",
        "category": "drama",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Everyone knows Joey does not share food, so touching his fries is completely out of the question.",
        "clozedTemplate": "Everyone knows Joey does not [1], so touching his fries is completely [2].",
        "blanks": ["share food", "out of the question"],
        "listeningTip": "注意 out of the 在美式快速口語中常連讀弱化為 /aʊ-ɾə-ðə/。",
        "sentenceZh": "大家都知道 Joey 絕不跟別人分食，所以想碰他的薯條是門都沒有、絕不可能的事。",
        "casualPhrase": "out of the question",
        "casualExplain": "絕不可能、不在考慮範圍內",
        "registerQuestion": "《六人行》經典名言衍生情境中提到某事 \"out of the question\"。若要在【雅思寫作 Task 2】表達「在缺乏國際監管的情況下，全面解除人工智慧限制是絕對不可行的」，哪個替換最正式？",
        "registerOptions": [
            "categorically unfeasible without robust regulatory oversight",
            "completely outside the exam question paper",
            "impossible because nobody wants to share lunch",
            "removed from the classroom quiz list"
        ],
        "academicAnswer": "categorically unfeasible without robust regulatory oversight",
        "academicSentence": "Unrestricted deployment of autonomous weapon systems remains categorically unfeasible without robust regulatory oversight.",
        "stressGuide": "EVeryone KNOWS JOey does NOT SHARE FOOD, so TOUCHing his FRIES is comPLETEly OUT‿of the QUEStion.",
        "ieltsSpeakingPart": "IELTS Speaking Part 1 · Food & Dining Habits",
        "ieltsSpeakingQ": "Do you prefer sharing dishes family-style or ordering your own individual meal?",
        "ieltsSpeakingModel": "Normally I enjoy sharing dishes, though when I am starving after a long shift, giving away my favorite dish is pretty much out of the question!"
    },
    {
        "id": "ts_2",
        "work": "Taylor Swift",
        "workEn": "Blank Space",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Got a long list of ex-lovers, they will tell you I am insane, because reputation precedes me.",
        "clozedTemplate": "Got a long list of [1], they will tell you I am insane, because [2] precedes me.",
        "blanks": ["ex-lovers", "reputation"],
        "listeningTip": "注意 list of 連音成 /lɪs-təv/；reputation 重音在第三音節 /ˌrep.jəˈteɪ.ʃən/。",
        "sentenceZh": "有一長串前任名單，他們會告訴你我瘋了，因為我的名聲早已不脛而走。",
        "casualPhrase": "reputation precedes me",
        "casualExplain": "名聲在外、未見其人先聞其名",
        "registerQuestion": "《Blank Space》語境中提到「名聲在外」。若要在【雅思寫作 Task 2】表達「企業或機構的公眾聲譽對長期信任至關重要」，哪個學術句型最精準？",
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
            for rank, line in enumerate(r.text.splitlines()[:30000], start=1):
                parts = line.strip().split()
                if parts and parts[0].isalpha() and len(parts[0]) >= 6:
                    tv_words[parts[0].lower()] = rank
    except Exception as e:
        print("美劇詞頻下載略過:", e)
    return tv_words


def fetch_real_dictionary_example(word: str):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{requests.utils.quote(word)}"
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code != 200:
            return None
        data = r.json()[0]
        for m in data.get("meanings", []):
            for d in m.get("definitions", []):
                ex = (d.get("example") or "").strip()
                if ex and 35 <= len(ex) <= 220 and word.lower() in ex.lower():
                    return {"example": ex, "definition": d.get("definition", "")}
    except Exception:
        pass
    return None


def build_clean_10k_vocab():
    """排除前 4,500 個基礎生活單字，篩選真正 IELTS Band 7.5+ 與美劇高階詞彙至 10,000 單"""
    vocab_map = {item["word"].lower(): item for item in CORE_SEED_VOCAB}
    tv_freq_map = fetch_tv_subtitle_frequency()

    ecdict_url = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv"
    try:
        with requests.get(ecdict_url, headers=HEADERS, stream=True, timeout=35) as resp:
            resp.raise_for_status()
            lines = (line.decode("utf-8", errors="ignore") for line in resp.iter_lines())
            reader = csv.DictReader(lines)

            ielts_adv = []
            tv_adv = []

            for row in reader:
                word = (row.get("word") or "").strip()
                if not word or not word.isalpha() or len(word) < 6 or not word.islower():
                    continue
                if word in vocab_map:
                    continue

                zh_raw = (row.get("translation") or "").strip().replace("\\n", "；")
                if not zh_raw:
                    continue

                bnc = int(row.get("bnc") or 99999)
                frq = int(row.get("frq") or 99999)
                # 排除前 4,500 個基礎單字 (如 stomach, salad, clock, jeans)
                if (0 < frq <= 4500) or (0 < bnc <= 4500):
                    continue

                phonetic = (row.get("phonetic") or "").strip()
                ipa = f"/{phonetic}/" if phonetic else ""
                pos = (row.get("pos") or "vocab").split(":")[0]
                tag = (row.get("tag") or "").lower()
                tv_rank = tv_freq_map.get(word, 99999)

                is_ielts_or_gre = any(t in tag for t in ["ielts", "toefl", "gre"])
                is_tv_mid_high = 4500 < tv_rank <= 22000

                if is_ielts_or_gre:
                    is_high_freq = ("ielts" in tag) and (4500 < frq <= 12000)
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
                        "freq": tv_rank <= 9000,
                        "_rank": tv_rank
                    })

            ielts_adv.sort(key=lambda x: x["_rank"])
            tv_adv.sort(key=lambda x: x["_rank"])

            for item in ielts_adv[:7500]:
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
    """從 5 大國際新聞/科普 RSS 與線上字典自動抓取真實語境考題（擴充至 300 題）"""
    bank = load_json(BANK_FILE, {"listening": [], "reading": [], "writing": [], "speaking": [], "quizPool": []})
    clean_pool = [
        q for q in bank.get("quizPool", [])
        if not q.get("id", "").startswith("web_ielts_")
        and "elevates your IELTS Band score" not in q.get("question", "")
    ]
    existing_ids = {q["id"] for q in clean_pool}

    for v in CORE_SEED_VOCAB:
        qid = f"core_q_{v['word'].replace(' ', '_')}"
        if qid not in existing_ids and v["word"].lower() in v["example"].lower():
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
            existing_ids.add(qid)

    high_freq_candidates = [v for v in vocab_list if v.get("freq") and v["word"].isalpha() and len(v["word"]) >= 7]
    random.shuffle(high_freq_candidates)
    adv_word_names = [v["word"] for v in high_freq_candidates[:300]]

    dict_added = 0
    for v in high_freq_candidates[:25]:
        if dict_added >= 15:
            break
        qid = f"dict_q_{v['word'].lower()}"
        if qid in existing_ids:
            continue
        info = fetch_real_dictionary_example(v["word"])
        if info and len(adv_word_names) >= 10:
            masked = re.sub(rf"\b{re.escape(v['word'])}\b", "________", info["example"], count=1, flags=re.IGNORECASE)
            distractors = random.sample([w for w in adv_word_names if w.lower() != v["word"].lower()], 3)
            opts = distractors + [v["word"]]
            random.shuffle(opts)
            clean_pool.append({
                "id": qid,
                "tag": f"字典真實例句自動出題 · {v['source']}",
                "question": f"請根據語境選出最適合填入空格的 Band 7.5+ 詞彙：\n\"{masked}\"",
                "options": opts,
                "answer": v["word"],
                "explanation": f"正確答案為「{v['word']}」({v['zh']})。\n英英釋義：{info['definition']}"
            })
            existing_ids.add(qid)
            dict_added += 1

    rss_urls = [
        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://feeds.npr.org/1001/rss.xml",
        "https://www.theguardian.com/science/rss",
        "https://www.sciencedaily.com/rss/top/science.xml"
    ]
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    for rss in rss_urls:
        try:
            r = requests.get(rss, headers=HEADERS, timeout=10)
            root = ET.fromstring(r.text)
            for item in root.findall(".//item")[:10]:
                desc = re.sub(r"<[^>]+>", "", item.findtext("description") or "").strip()
                desc = re.sub(r"\s+", " ", desc)
                tokens = re.findall(r"\b[a-z]{8,14}\b", desc)
                if tokens and 65 <= len(desc) <= 280 and len(adv_word_names) >= 10:
                    target_w = tokens[0]
                    qid = f"news_q_{target_w.lower()}_{today_str}"
                    if qid not in existing_ids:
                        masked = re.sub(rf"\b{re.escape(target_w)}\b", "________", desc, count=1)
                        distractors = random.sample([w for w in adv_word_names if w.lower() != target_w.lower()], 3)
                        opts = distractors + [target_w]
                        random.shuffle(opts)
                        clean_pool.append({
                            "id": qid,
                            "tag": f"每日國際新聞/科普語境 ({today_str})",
                            "question": f"請選出最適合填入國際報導語境空格的高階單字：\n\"{masked}\"",
                            "options": opts,
                            "answer": target_w,
                            "explanation": f"原句出自國際新聞/科普報導，正確單字為「{target_w}」。"
                        })
                        existing_ids.add(qid)
        except Exception:
            continue

    bank["quizPool"] = clean_pool[-300:]
    with open(BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)


def update_pop_ielts_bank():
    existing = load_json(POP_BANK_FILE, [])
    merged = {item["id"]: item for item in existing if item.get("clozedTemplate")}
    for item in EXTRA_POP_IELTS_ITEMS:
        merged[item["id"]] = item
    with open(POP_BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(list(merged.values()), f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    vocab_data = build_clean_10k_vocab()
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(vocab_data, f, ensure_ascii=False, indent=2)

    update_ielts_quiz_bank(vocab_data)
    update_pop_ielts_bank()
