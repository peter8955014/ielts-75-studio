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

# 1. 核心 IELTS Band 7.5+ 學術詞與美劇/金曲高頻片語（同步匯入主站萬字詞庫與動態刷題）
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
    {"id": "core_15", "word": "think on your feet", "ipa": "/θɪŋk ɑːn jʊr fiːt/", "pos": "idiom", "zh": "臨機應變、反應敏捷", "collocations": "ability to think on your feet", "example": "If you want to survive the night shift at the diner, you have to think on your feet.", "source": "TV: 破產姊妹 (2 Broke Girls)", "part": "Speaking", "freq": True},
    {"id": "core_16", "word": "learn the ropes", "ipa": "/lɜːrn ðə roʊps/", "pos": "idiom", "zh": "摸熟門道、掌握訣竅", "collocations": "quickly learn the ropes", "example": "Caroline had to start from scratch and learn the ropes of waiting tables.", "source": "TV: 破產姊妹 (2 Broke Girls)", "part": "Speaking", "freq": True},
    {"id": "core_17", "word": "out of the question", "ipa": "/aʊt əv ðə ˈkwes.tʃən/", "pos": "idiom", "zh": "絕不可能、想都別想", "collocations": "completely out of the question", "example": "Everyone knows Joey does not share food, so touching his fries is out of the question.", "source": "TV: 六人行 (Friends)", "part": "Speaking", "freq": True},
    {"id": "core_18", "word": "out of proportion", "ipa": "/aʊt əv prəˈpɔːr.ʃən/", "pos": "idiom", "zh": "不成比例、小題大做", "collocations": "blow things out of proportion", "example": "Monica tends to blow small things out of proportion whenever guests make a mess.", "source": "TV: 六人行 (Friends)", "part": "Speaking", "freq": True},
    {"id": "core_19", "word": "make ends meet", "ipa": "/meɪk endz miːt/", "pos": "idiom", "zh": "維持生計、收支平衡", "collocations": "struggle to make ends meet", "example": "Rising inflation makes it increasingly difficult for low-income families to make ends meet.", "source": "Song: Ariana Grande", "part": "Speaking", "freq": True},
    {"id": "core_20", "word": "turn a blind eye", "ipa": "/tɜːrn ə blaɪnd aɪ/", "pos": "idiom", "zh": "視而不見、睜一隻眼閉一隻眼", "collocations": "turn a blind eye to", "example": "Authorities can no longer turn a blind eye to illegal industrial waste dumping.", "source": "Song: Sam Smith", "part": "Writing", "freq": True}
]

# 2. 擴充版：破產姊妹 (3題) + 六人行 (3題) + 九位歌手各 2 題 = 24 組三合一雅思題庫
EXTRA_POP_IELTS_ITEMS = [
    # ==================== 破產姊妹 (2 Broke Girls) ====================
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
        "registerQuestion": "《破產姊妹》強調服務業必須 "think on your feet and keep your cool"。若要在【雅思寫作 Task 2】論述「現代醫療與緊急應變人員須具備高壓下的快速應變能力」，哪個學術替換最精準？",
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
        "id": "2bg_3",
        "work": "破產姊妹",
        "workEn": "2 Broke Girls · Starting Over",
        "category": "drama",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "After losing her family fortune overnight, Caroline had to start from scratch and learn the ropes of waiting tables.",
        "clozedTemplate": "After losing her family fortune overnight, Caroline had to [1] and [2] of waiting tables.",
        "blanks": ["start from scratch", "learn the ropes"],
        "listeningTip": "注意 start from 中 t 弱化；learn the ropes 源自水手學習操作船帆繩索，意指「摸熟門道」。",
        "sentenceZh": "在一夕之間失去家產後，Caroline 不得不白手起家，從頭摸熟端盤子服務的門道。",
        "casualPhrase": "start from scratch / learn the ropes",
        "casualExplain": "從零開始、摸熟新手入門訣竅",
        "registerQuestion": "《破產姊妹》講述千金小姐 "start from scratch"。若要在【雅思寫作 Task 2】表達「許多新興經濟體正從零建構綠色能源基礎設施」，哪個學術替換最得體？",
        "registerOptions": [
          "construct sustainable infrastructure from the ground up",
          "scratch the surface of old factory walls",
          "tie ropes around new power stations",
          "lose all family savings in one night"
        ],
        "academicAnswer": "construct sustainable infrastructure from the ground up",
        "academicSentence": "Developing nations possess a unique opportunity to construct sustainable infrastructure from the ground up without legacy carbon lock-in.",
        "stressGuide": "AFter LOSing her FAMily FORtune OverNIGHT, CARoline HAD to START from SCRATCH and LEARN the ROPES.",
        "ieltsSpeakingPart": "IELTS Speaking Part 2 · Learning a New Skill",
        "ieltsSpeakingQ": "Describe a time when you had to learn something completely new from the beginning.",
        "ieltsSpeakingModel": "When I first started writing automated trading scripts, I had to start from scratch and spend weeks learning the ropes of API architecture before executing a single live order."
    },
    {
        "id": "2bg_4",
        "work": "破產姊妹",
        "workEn": "2 Broke Girls · Blunt Candor",
        "category": "drama",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Max never beats around the bush; she calls a spade a spade even when customers complain.",
        "clozedTemplate": "Max never [1]; she [2] even when customers complain.",
        "blanks": ["beats around the bush", "calls a spade a spade"],
        "listeningTip": "注意 beats around 中 s 與 around 連讀成 /biːt-sə-raʊnd/；calls a spade 連讀成 /kɔːl-zə-speɪd/。",
        "sentenceZh": "Max 說話從不拐彎抹角；就算客人抱怨，她也是有一說一、直言不諱。",
        "casualPhrase": "beats around the bush / calls a spade a spade",
        "casualExplain": "不拐彎抹角、直言不諱",
        "registerQuestion": "《破產姊妹》Max 習慣 "call a spade a spade"。若要在【雅思寫作 Task 2】論述「政策制定者應以坦率直白的態度面對財政赤字問題」，哪個學術表達最精準？",
        "registerOptions": [
          "address structural deficits with uncompromising candor",
          "dig garden soil using metal spades",
          "walk in circles around forest bushes",
          "complain loudly to restaurant customers"
        ],
        "academicAnswer": "address structural deficits with uncompromising candor",
        "academicSentence": "Elected officials must address structural deficits with uncompromising candor rather than relying on euphemistic rhetoric.",
        "stressGuide": "MAX NEVer BEATS‿aROUND the BUSH; she CALLS‿a SPADE‿a SPADE Even when CUSTomers comPLAIN.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Honesty & Communication Styles",
        "ieltsSpeakingQ": "Do you think direct communication is always better than polite indirectness?",
        "ieltsSpeakingModel": "In technical troubleshooting, I appreciate colleagues who never beat around the bush and simply call a spade a spade, though diplomatic tact is certainly vital in cross-cultural negotiations."
    },

    # ==================== 六人行 (Friends) ====================
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
        "registerQuestion": "《六人行》經典名言衍生情境中提到某事 "out of the question"。若要在【雅思寫作 Task 2】表達「在缺乏國際監管的情況下，全面解除人工智慧限制是絕對不可行的」，哪個替換最正式？",
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
        "id": "fr_3",
        "work": "六人行",
        "workEn": "Friends · Rachel's Independence",
        "category": "drama",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Cutting up her credit cards was a leap of faith that helped Rachel stand on her own two feet.",
        "clozedTemplate": "Cutting up her credit cards was a [1] that helped Rachel [2].",
        "blanks": ["leap of faith", "stand on her own two feet"],
        "listeningTip": "注意 leap of faith 連讀成 /liː-pəv-feɪθ/；stand on her 中 her 的 h 音常弱化脫落成 /stæn-dɑː-nɚ/。",
        "sentenceZh": "剪掉父親的副卡是一場破釜沉舟的冒險，卻幫助 Rachel 真正學會自立更生。",
        "casualPhrase": "leap of faith / stand on her own two feet",
        "casualExplain": "孤注一擲的嘗試 / 自立更生",
        "registerQuestion": "《六人行》Rachel 剪掉信用卡以 "stand on her own two feet"。若要在【雅思寫作 Task 2】論述「高等教育應培養年輕人實現經濟獨立與自主的能力」，哪個表達最學術？",
        "registerOptions": [
          "achieve financial autonomy and personal self-reliance",
          "stand upright on two legs without sitting down",
          "cut plastic cards with kitchen scissors",
          "jump across a wide river with closed eyes"
        ],
        "academicAnswer": "achieve financial autonomy and personal self-reliance",
        "academicSentence": "Vocational training programs empower young adults to achieve financial autonomy and personal self-reliance early in their careers.",
        "stressGuide": "CUTting UP her CREDit CARDS was a LEAP‿of FAITH that HELPED RAchel STAND‿on her OWN TWO FEET.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Youth Independence & Adulthood",
        "ieltsSpeakingQ": "At what age do you think young people should become financially independent from their parents?",
        "ieltsSpeakingModel": "Ideally right after university graduation; taking that initial leap of faith into the workforce is essential for young adults to stand on their own two feet and achieve true financial autonomy."
    },
    {
        "id": "fr_4",
        "work": "六人行",
        "workEn": "Friends · Monica's Coaster Rule",
        "category": "drama",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Monica tends to blow small things out of proportion whenever someone forgets to use a coaster.",
        "clozedTemplate": "Monica tends to [1] small things [2] whenever someone forgets to use a coaster.",
        "blanks": ["blow", "out of proportion"],
        "listeningTip": "注意 out of 在口語中連讀成 /aʊ-ɾəv/；proportion 重音在第二音節 /prəˈpɔːr.ʃən/。",
        "sentenceZh": "只要有人忘記用杯墊，Monica 就會把芝麻小事無限放大、小題大做。",
        "casualPhrase": "blow things out of proportion",
        "casualExplain": "小題大做、過度渲染或誇大其詞",
        "registerQuestion": "《六人行》中 Monica 常 "blow small things out of proportion"。若要在【雅思寫作 Task 2】批評「聳動媒體常為了點閱率而過度誇大個別社會事件」，哪個學術動詞最精準？",
        "registerOptions": [
          "sensationalize and disproportionately exaggerate isolated incidents",
          "blow air into large balloons at birthday parties",
          "measure the exact mathematical ratio of tables",
          "forget to place coasters under coffee mugs"
        ],
        "academicAnswer": "sensationalize and disproportionately exaggerate isolated incidents",
        "academicSentence": "Algorithm-driven news outlets frequently sensationalize and disproportionately exaggerate isolated incidents to maximize user engagement.",
        "stressGuide": "MONica TENDS to BLOW SMALL THINGS OUT‿of proPORtion whenEVer SOMEone forGETS to USE a COASTer.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Media & Public Perception",
        "ieltsSpeakingQ": "Do you think social media makes people worry too much about trivial problems?",
        "ieltsSpeakingModel": "Definitely. Online echo chambers tend to blow minor misunderstandings completely out of proportion, disproportionately exaggerating issues that could otherwise be resolved calmly."
    },

    # ==================== Taylor Swift (2 題) ====================
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
    },
    {
        "id": "ts_3",
        "work": "Taylor Swift",
        "workEn": "Anti-Hero",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "It is me, hi, I am the problem, it is me, staring directly at the sun instead of facing the music.",
        "clozedTemplate": "It is me, hi, I am the problem, it is me, staring [1] at the sun instead of [2].",
        "blanks": ["directly", "facing the music"],
        "listeningTip": "注意 instead of 連讀成 /ɪnˈste-dəv/；face the music 意為「勇於面對批評或承擔後果」。",
        "sentenceZh": "是我，嗨，問題就出在我身上，直視著刺眼陽光卻遲遲不敢勇於承擔後果。",
        "casualPhrase": "facing the music",
        "casualExplain": "勇於承擔後果、直面嚴厲批評",
        "registerQuestion": "《Anti-Hero》探討自我反省與「面對現實後果」(face the music)。若要在【雅思寫作 Task 2】表達「企業高層必須為環境污染負起完全的法律與道德責任」，哪個表達最學術？",
        "registerOptions": [
          "assume full accountability for adverse environmental outcomes",
          "listen to loud pop songs in front of an orchestra",
          "stare directly at the afternoon sunlight",
          "admit that singers write catchy choruses"
        ],
        "academicAnswer": "assume full accountability for adverse environmental outcomes",
        "academicSentence": "Corporate executives must assume full accountability for adverse environmental outcomes resulting from negligent supply chain practices.",
        "stressGuide": "I am the PROBlem, it is ME, STARing diRECTly at the SUN inSTEAD‿of FACing the MUsic.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Responsibility & Admitting Mistakes",
        "ieltsSpeakingQ": "Why do some people find it difficult to admit when they have made a mistake?",
        "ieltsSpeakingModel": "People often fear losing credibility, yet mature leaders recognize that facing the music early and assuming full accountability is the fastest way to rebuild trust."
    },

    # ==================== Ariana Grande (2 題) ====================
    {
        "id": "ag_2",
        "work": "Ariana Grande",
        "workEn": "7 rings",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Whoever said money cannot solve your problems must not have had enough money to make ends meet.",
        "clozedTemplate": "Whoever said money cannot [1] your problems must not have had enough money to [2].",
        "blanks": ["solve", "make ends meet"],
        "listeningTip": "注意 must not have 在美式口語中常弱讀連音為 /mʌst-nɑː-ɾəv/；make ends meet 中 ends 與 meet 連讀順暢。",
        "sentenceZh": "不管是誰說金錢解決不了問題，那個人肯定沒體會過連維持基本生計都困難的窘境。",
        "casualPhrase": "make ends meet",
        "casualExplain": "維持基本生計、使收支相抵",
        "registerQuestion": "Ariana Grande 的《7 rings》反諷金錢與生活壓力，引出 "make ends meet"。若要在【雅思寫作 Task 2】論述「生活成本飆升使低收入家庭難以維持基本經濟收支平衡」，哪個學術替換最精準？",
        "registerOptions": [
          "sustain basic household solvency amidst rising inflation",
          "tie the two ends of a shoelace together",
          "purchase seven diamond rings at a boutique",
          "count coins at the end of every week"
        ],
        "academicAnswer": "sustain basic household solvency amidst rising inflation",
        "academicSentence": "Escalating housing and energy costs make it increasingly arduous for low-income households to sustain basic household solvency amidst rising inflation.",
        "stressGuide": "WhoEVer SAID MONey CANnot SOLVE your PROBlems must NOT have HAD eNOUGH MONey to MAKE ENDS MEET.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Money, Consumerism & Living Standards",
        "ieltsSpeakingQ": "Do you think having more money automatically makes people happier?",
        "ieltsSpeakingModel": "Up to a certain threshold, yes—when people struggle just to make ends meet, financial stability drastically reduces anxiety, though beyond basic solvency, happiness depends more on relationships."
    },
    {
        "id": "ag_3",
        "work": "Ariana Grande",
        "workEn": "breathin",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "When anxiety starts clouding your judgment, you just need to keep breathing and take things in stride.",
        "clozedTemplate": "When anxiety starts clouding your [1], you just need to keep breathing and take things [2].",
        "blanks": ["judgment", "in stride"],
        "listeningTip": "注意 take things in stride 意為「大步跨過困難、泰然處之」，things in 連讀成 /θɪŋ-zɪn/。",
        "sentenceZh": "當焦慮開始蒙蔽你的判斷力時，你只需要保持深呼吸並從容不迫地應對一切。",
        "casualPhrase": "take things in stride",
        "casualExplain": "泰然處之、從容應對挫折而不慌亂",
        "registerQuestion": "Ariana Grande 的《breathin》傳達在焦慮中 "take things in stride"。若要在【雅思寫作 Task 2】描述「在快速變遷的職場中保持心理韌性與冷靜應對波動」，哪個表達最學術？",
        "registerOptions": [
          "maintain psychological equilibrium amidst occupational volatility",
          "take very long walking steps down the street",
          "breathe heavily during a marathon race",
          "ignore all medical advice about anxiety"
        ],
        "academicAnswer": "maintain psychological equilibrium amidst occupational volatility",
        "academicSentence": "Mindfulness training equips professionals to maintain psychological equilibrium amidst occupational volatility.",
        "stressGuide": "When anXIety STARTS CLOUDing your JUDGment, you JUST need to KEEP BREATHing and TAKE THINGS‿in STRIDE.",
        "ieltsSpeakingPart": "IELTS Speaking Part 1 / Part 2 · Stress Management",
        "ieltsSpeakingQ": "What do you do to relax when you feel overwhelmed by work or study?",
        "ieltsSpeakingModel": "Whenever deadlines start clouding my judgment, I step away for a brisk walk to clear my head so I can take challenges in stride and maintain psychological equilibrium."
    },

    # ==================== Sam Smith (2 題) ====================
    {
        "id": "ss_2",
        "work": "Sam Smith",
        "workEn": "Too Good at Goodbyes",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "I am never going to let you close to me, even though you mean the most to me, because I keep my guard up.",
        "clozedTemplate": "I am never going to let you close to me, [1] you mean the most to me, because I keep my [2].",
        "blanks": ["even though", "guard up"],
        "listeningTip": "注意 let you 連讀常帶有 /tʃ/ 音變成 /le-tʃuː/；keep my guard up 源自拳擊架起雙臂防禦，意為「保持戒心」。",
        "sentenceZh": "我絕不會讓你太靠近我，儘管你對我意義重大，因為我總是習慣保持防備戒心。",
        "casualPhrase": "keep my guard up",
        "casualExplain": "保持戒心、建立心理防線",
        "registerQuestion": "Sam Smith 在《Too Good at Goodbyes》唱出因害怕受傷而 "keep my guard up"。若要在【雅思寫作 Task 2】論述「數位詐騙頻傳導致網路使用者在線上互動中保持高度防禦戒心」，哪個替換最精準？",
        "registerOptions": [
          "maintain heightened defensive vigilance in digital interactions",
          "hire security guards to stand outside the house",
          "say goodbye quickly at the airport gate",
          "close all bedroom doors before sleeping"
        ],
        "academicAnswer": "maintain heightened defensive vigilance in digital interactions",
        "academicSentence": "Proliferating cyber fraud has compelled consumers to maintain heightened defensive vigilance in digital interactions.",
        "stressGuide": "I am NEVer going to LET you CLOSE to me, Even THOUGH you MEAN the MOST to me, because I KEEP my GUARD‿UP.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Trust & Social Relationships",
        "ieltsSpeakingQ": "Do you think people today are less trusting of strangers than they were in the past?",
        "ieltsSpeakingModel": "To some extent, yes. Constant news about online scams makes people keep their guard up initially, maintaining heightened vigilance until genuine credibility is established."
    },
    {
        "id": "ss_3",
        "work": "Sam Smith",
        "workEn": "I'm Not the Only One",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "For months she turned a blind eye to the rumors, even though the truth was hiding in plain sight.",
        "clozedTemplate": "For months she turned a [1] to the rumors, even though the truth was hiding in [2].",
        "blanks": ["blind eye", "plain sight"],
        "listeningTip": "注意 turned a blind eye 連讀成 /tɜːrn-də-blaɪn-daɪ/；in plain sight 意為「在眾目睽睽之下、顯而易見」。",
        "sentenceZh": "好幾個月來她對流言蜚語睜一隻眼閉一隻眼，儘管真相就擺在眼前、顯而易見。",
        "casualPhrase": "turned a blind eye / in plain sight",
        "casualExplain": "視而不見、故意忽視 / 顯而易見",
        "registerQuestion": "《I'm Not the Only One》語境中提到 "turn a blind eye"。若要在【雅思寫作 Task 2】批判「監管機構不能再對企業的環境違規行為視而不見」，哪個學術表達最有力？",
        "registerOptions": [
          "deliberately disregard glaring regulatory violations",
          "close one eye while reading a newspaper",
          "hide secret rumors inside a plain envelope",
          "visit an optometrist for vision testing"
        ],
        "academicAnswer": "deliberately disregard glaring regulatory violations",
        "academicSentence": "Environmental watchdogs can no longer afford to deliberately disregard glaring regulatory violations by major industrial polluters.",
        "stressGuide": "For MONTHS she TURNED‿a BLIND EYE to the RUmors, Even THOUGH the TRUTH was HIDing in PLAIN SIGHT.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Ethics & Accountability",
        "ieltsSpeakingQ": "What happens when organizations ignore minor problems for too long?",
        "ieltsSpeakingModel": "When management turns a blind eye to early warning signs that are hiding in plain sight, minor operational flaws inevitably snowball into systemic crises."
    },

    # ==================== Charlie Puth (2 題) ====================
    {
        "id": "cp_2",
        "work": "Charlie Puth",
        "workEn": "We Don't Talk Anymore",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "We do not talk anymore like we used to do, and drifting apart has left us with unfinished business.",
        "clozedTemplate": "We do not talk anymore like we used to do, and [1] has left us with [2].",
        "blanks": ["drifting apart", "unfinished business"],
        "listeningTip": "注意 used to 在美式口語中常讀成 /juːs-tə/；drifting apart 中 t 與 a 連讀成 /drɪf-tɪ-ŋə-pɑːrt/。",
        "sentenceZh": "我們不再像從前那樣無話不談，而彼此漸行漸遠也留下了未了的心結。",
        "casualPhrase": "drifting apart",
        "casualExplain": "（人際關係）漸行漸遠、逐漸疏遠",
        "registerQuestion": "Charlie Puth 在《We Don't Talk Anymore》唱出兩人 "drifting apart"。若要在【雅思寫作 Task 2】描述「遠距工作與數位溝通可能導致同事之間產生人際疏離感」，哪個名詞短語最學術？",
        "registerOptions": [
          "gradual interpersonal estrangement and weakened cohesion",
          "floating away on wooden boats across the ocean",
          "forgetting how to speak English anymore",
          "leaving office paperwork unfinished on Friday"
        ],
        "academicAnswer": "gradual interpersonal estrangement and weakened cohesion",
        "academicSentence": "Prolonged telecommuting without face-to-face interaction can precipitate gradual interpersonal estrangement and weakened cohesion within teams.",
        "stressGuide": "We do NOT TALK anyMORE like we USED to DO, and DRIFTing‿aPART has LEFT us with unFINished BUSiness.",
        "ieltsSpeakingPart": "IELTS Speaking Part 1 / Part 3 · Friendship & Modern Communication",
        "ieltsSpeakingQ": "Why do childhood friends sometimes lose contact as they grow older?",
        "ieltsSpeakingModel": "As people relocate for university or demanding careers, differing schedules naturally cause them to drift apart, leading to gradual interpersonal estrangement unless both sides make a conscious effort."
    },
    {
        "id": "cp_3",
        "work": "Charlie Puth",
        "workEn": "See You Again",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "It has been a long day without you my friend, and we have come a long way from where we began.",
        "clozedTemplate": "It has been a long day [1] you my friend, and we have [2] from where we began.",
        "blanks": ["without", "come a long way"],
        "listeningTip": "注意 come a long way 連讀成 /kʌ-mə-lɔːŋ-weɪ/，意為「取得長足進步、走過漫長歷程」。",
        "sentenceZh": "沒有你在身邊的這段日子漫長無比，而從我們最初的起點算起，我們已經走過了很長一段路、成長了許多。",
        "casualPhrase": "come a long way",
        "casualExplain": "取得長足進步、發展成熟許多",
        "registerQuestion": "《See You Again》經典歌詞 "we've come a long way"。若要在【雅思寫作 Task 2】表達「再生能源技術在過去二十年間已取得顯著的技術突破與發展」，哪個學術表達最精準？",
        "registerOptions": [
          "achieved substantial technological milestones over two decades",
          "walked a very long highway without stopping",
          "traveled far away from the starting line",
          "waited a long day for a friend to arrive"
        ],
        "academicAnswer": "achieved substantial technological milestones over two decades",
        "academicSentence": "Photovoltaic solar engineering has achieved substantial technological milestones over two decades, dramatically lowering per-kilowatt generation costs.",
        "stressGuide": "It has BEEN a LONG DAY withOUT you my FRIEND, and we have COME‿a LONG WAY from WHERE we beGAN.",
        "ieltsSpeakingPart": "IELTS Speaking Part 2 · Personal Achievement or Progress",
        "ieltsSpeakingQ": "Describe a skill or project in which you have made significant progress over time.",
        "ieltsSpeakingModel": "Looking back at my early Python scripts compared to my current automated workflows, I realize I have come a long way and achieved substantial technical milestones through consistent practice."
    },

    # ==================== Shawn Mendes (2 題) ====================
    {
        "id": "sm_2",
        "work": "Shawn Mendes",
        "workEn": "Stitches",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Thought that I had been hurt before, but no one has ever left me quite this sore, forcing me to pick up the pieces.",
        "clozedTemplate": "Thought that I had been [1] before, but no one has ever left me quite this sore, forcing me to [2].",
        "blanks": ["hurt before", "pick up the pieces"],
        "listeningTip": "注意 pick up the pieces 中 pick 與 up 連讀成 /pɪ-kʌp/，意為「收拾殘局、在受創後重新振作」。",
        "sentenceZh": "原以為自己以前受過傷，但從沒有人讓我如此痛徹心扉，逼得我必須重新收拾殘局、振作起來。",
        "casualPhrase": "pick up the pieces",
        "casualExplain": "收拾殘局、在重大打擊後重建生活",
        "registerQuestion": "《Stitches》描繪心碎後必須 "pick up the pieces"。若要在【雅思寫作 Task 2】論述「自然災害過後，政府應投入充足資金協助受災社區重建基礎設施與生活秩序」，哪個替換最學術？",
        "registerOptions": [
          "rehabilitate devastated communities and restore socioeconomic stability",
          "collect broken glass pieces from the living room floor",
          "stitch torn clothes together with a needle",
          "recover from minor sore muscles after exercise"
        ],
        "academicAnswer": "rehabilitate devastated communities and restore socioeconomic stability",
        "academicSentence": "Following severe climate-induced flooding, state agencies must allocate emergency funds to rehabilitate devastated communities and restore socioeconomic stability.",
        "stressGuide": "THOUGHT that I had BEEN HURT beFORE, FORCing me to PICK‿UP the PIECes.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Overcoming Adversity & Resilience",
        "ieltsSpeakingQ": "How can communities best support individuals who have experienced major setbacks?",
        "ieltsSpeakingModel": "Accessible mental health services and vocational retraining programs are crucial when people are trying to pick up the pieces and restore stability after an economic or personal crisis."
    },
    {
        "id": "sm_3",
        "work": "Shawn Mendes",
        "workEn": "In My Blood",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Sometimes I feel like giving up, but throwing in the towel is simply not in my blood.",
        "clozedTemplate": "Sometimes I feel like [1], but [2] is simply not in my blood.",
        "blanks": ["giving up", "throwing in the towel"],
        "listeningTip": "注意 throwing in the towel 源自拳擊賽教練把毛巾丟進擂台代表棄權，意為「認輸放棄」。",
        "sentenceZh": "有時候我也會覺得快撐不下去想放棄，但舉白旗認輸根本不在我的基因裡。",
        "casualPhrase": "throwing in the towel",
        "casualExplain": "認輸、舉白旗放棄",
        "registerQuestion": "Shawn Mendes 在《In My Blood》唱出拒絕 "throwing in the towel"。若要在【雅思寫作 Task 2】表達「面對氣候變遷挑戰，國際社會絕不能輕言放棄減碳目標」，哪個正式動詞最精準？",
        "registerOptions": [
          "capitulate or abandon binding decarbonization commitments",
          "throw wet bathroom towels onto the gymnasium floor",
          "stop singing high notes during a concert",
          "give up blood samples at a local clinic"
        ],
        "academicAnswer": "capitulate or abandon binding decarbonization commitments",
        "academicSentence": "Despite short-term energy supply pressures, industrialized nations must not capitulate or abandon binding decarbonization commitments.",
        "stressGuide": "SOMEtimes I FEEL like GIVing‿UP, but THROWing‿in the TOWel is SIMPly NOT in my BLOOD.",
        "ieltsSpeakingPart": "IELTS Speaking Part 2 · A Challenge You Refused to Quit",
        "ieltsSpeakingQ": "Describe a difficult task or goal that you refused to give up on.",
        "ieltsSpeakingModel": "Preparing for a Band 7.5+ target while working full-time shifts was exhausting, and there were moments I felt like giving up, yet throwing in the towel was never an option for me."
    },

    # ==================== Lauv (2 題) ====================
    {
        "id": "lv_2",
        "work": "Lauv",
        "workEn": "Paris in the Rain",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Anywhere with you feels right, even when torrential rain catches us off guard without an umbrella.",
        "clozedTemplate": "Anywhere with you feels right, even when [1] rain catches us [2] without an umbrella.",
        "blanks": ["torrential", "off guard"],
        "listeningTip": "注意 catches us off guard 連讀成 /kæ-tʃɪ-zə-sɔːf-ɡɑːrd/，意為「讓人措手不及、出其不意」。",
        "sentenceZh": "只要有你在身邊，無論在哪裡都覺得自在，就算傾盆大雨在沒帶傘時突襲讓我們措手不及也無所謂。",
        "casualPhrase": "catches us off guard",
        "casualExplain": "讓人措手不及、在毫無防備時突襲",
        "registerQuestion": "《Paris in the Rain》情境中提到突如其來的情況 "catches us off guard"。若要在【雅思寫作 Task 2】表達「缺乏預警系統使沿海城市面對極端氣候事件時措手不及」，哪個學術替換最精準？",
        "registerOptions": [
          "renders coastal municipalities unprepared for sudden extreme weather contingencies",
          "forgets to carry folding umbrellas in Paris",
          "surprises couples walking in romantic rain",
          "leaves security guards standing outside"
        ],
        "academicAnswer": "renders coastal municipalities unprepared for sudden extreme weather contingencies",
        "academicSentence": "Outdated meteorological infrastructure renders coastal municipalities unprepared for sudden extreme weather contingencies.",
        "stressGuide": "ANywhere with YOU FEELS RIGHT, Even when torRENtial RAIN CATCHes‿us OFF GUARD.",
        "ieltsSpeakingPart": "IELTS Speaking Part 1 / Part 2 · Weather & Unplanned Events",
        "ieltsSpeakingQ": "Have you ever had an outdoor plan ruined or changed by unexpected weather?",
        "ieltsSpeakingModel": "Yes, during a trip to the mountains, a sudden downpour caught us completely off guard, forcing us to improvise an indoor itinerary that actually turned out to be memorable."
    },
    {
        "id": "lv_3",
        "work": "Lauv",
        "workEn": "Modern Loneliness",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Modern loneliness means we are constantly connected online yet still feel out of touch with real people.",
        "clozedTemplate": "Modern loneliness means we are constantly [1] online yet still feel [2] with real people.",
        "blanks": ["connected", "out of touch"],
        "listeningTip": "注意 out of touch 連讀成 /aʊ-ɾəv-tʌtʃ/，兼有「失去聯繫」與「與現實脫節」雙重涵義。",
        "sentenceZh": "現代孤寂意味著我們在網路上無時無刻保持連線，卻依然感覺與真實世界的人們漸趨脫節。",
        "casualPhrase": "out of touch",
        "casualExplain": "失去聯繫、與現實脫節",
        "registerQuestion": "Lauv 的《Modern Loneliness》點出數位時代讓人感到 "out of touch"。若要在【雅思寫作 Task 2】論述「過度依賴社群媒體可能加劇年輕人的社會疏離感」，哪個學術表達最道地？",
        "registerOptions": [
          "exacerbate social alienation and weaken authentic interpersonal bonds",
          "stop touching smartphone screens with fingers",
          "disconnect home Wi-Fi routers every evening",
          "lose phone numbers of high school friends"
        ],
        "academicAnswer": "exacerbate social alienation and weaken authentic interpersonal bonds",
        "academicSentence": "Substituting face-to-face socialization with passive social media consumption can exacerbate social alienation and weaken authentic interpersonal bonds.",
        "stressGuide": "MODern LONEiness MEANS we are CONstantly conNECTed onLINE yet STILL FEEL OUT‿of TOUCH.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Technology & Social Isolation",
        "ieltsSpeakingQ": "Do you think modern communication technology brings people closer together or makes them lonelier?",
        "ieltsSpeakingModel": "It is paradoxical—while messaging apps keep us connected across continents, heavy reliance on superficial online interaction can leave individuals feeling strangely out of touch with their immediate community."
    },

    # ==================== Christopher (2 題) ====================
    {
        "id": "ch_2",
        "work": "Christopher",
        "workEn": "Heartbeat",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Every time you walk into the room, my heart skips a beat and I lose my train of thought.",
        "clozedTemplate": "Every time you walk into the room, my heart [1] and I lose my [2].",
        "blanks": ["skips a beat", "train of thought"],
        "listeningTip": "注意 skips a beat 連讀成 /skɪp-sə-biːt/；train of thought 連讀成 /treɪ-nəv-θɔːt/，意為「思緒脈絡」。",
        "sentenceZh": "每次你走進房間，我的心就會漏跳一拍，連原本的思緒都瞬間中斷。",
        "casualPhrase": "skips a beat / lose my train of thought",
        "casualExplain": "心頭一震 / 思緒中斷、忘記剛才想到哪",
        "registerQuestion": "《Heartbeat》描寫因強烈分心而 "lose my train of thought"。若要在【雅思寫作 Task 2】論述「開放式辦公室的持續噪音干擾會嚴重打斷知識工作者的深度專注力」，哪個替換最學術？",
        "registerOptions": [
          "disrupt sustained cognitive focus and analytical continuity",
          "miss a commuter train at the central railway station",
          "listen to fast pop music while counting heartbeats",
          "forget where the office meeting room is located"
        ],
        "academicAnswer": "disrupt sustained cognitive focus and analytical continuity",
        "academicSentence": "Frequent auditory interruptions in open-plan offices severely disrupt sustained cognitive focus and analytical continuity.",
        "stressGuide": "EVery TIME you WALK‿into the ROOM, my HEART SKIPS‿a BEAT and I LOSE my TRAIN‿of THOUGHT.",
        "ieltsSpeakingPart": "IELTS Speaking Part 1 · Concentration & Work Environment",
        "ieltsSpeakingQ": "What kinds of distractions make it hard for you to concentrate when studying or working?",
        "ieltsSpeakingModel": "Sudden phone notifications or loud conversations easily make me lose my train of thought, which is why I prefer a quiet environment to maintain analytical continuity."
    },
    {
        "id": "ch_3",
        "work": "Christopher",
        "workEn": "Leap of Faith",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "When you stand at a crossroads, sometimes you have to burn your bridges and take a leap of faith.",
        "clozedTemplate": "When you stand at a [1], sometimes you have to [2] and take a leap of faith.",
        "blanks": ["crossroads", "burn your bridges"],
        "listeningTip": "注意 stand at a 連讀成 /stæn-dæ-ɾə/；burn your bridges 源自軍隊過河後燒毀橋樑以示決心，意為「破釜沉舟（或斷絕退路）」。",
        "sentenceZh": "當你站在人生的十字路口時，有時候你必須破釜沉舟、不留退路地放手一搏。",
        "casualPhrase": "at a crossroads / burn your bridges",
        "casualExplain": "處於人生關鍵抉擇點 / 破釜沉舟、斷絕退路",
        "registerQuestion": "《Leap of Faith》探討在人生十字路口 "burn your bridges"（不留退路全力投入）。若要在【雅思寫作 Task 2】表達「在職業生涯轉折點做出不可逆轉的重大承諾」，哪個表達最得體？",
        "registerOptions": [
          "make an irreversible commitment at a pivotal career juncture",
          "set wooden bridges on fire across a river",
          "stand in the middle of a busy traffic intersection",
          "refuse to speak with former colleagues politely"
        ],
        "academicAnswer": "make an irreversible commitment at a pivotal career juncture",
        "academicSentence": "Relocating abroad for postgraduate research often requires scholars to make an irreversible commitment at a pivotal career juncture.",
        "stressGuide": "When you STAND‿at‿a CROSSroads, SOMEtimes you HAVE to BURN your BRIDGes and TAKE a LEAP‿of FAITH.",
        "ieltsSpeakingPart": "IELTS Speaking Part 2 · An Important Decision You Made",
        "ieltsSpeakingQ": "Describe an important decision you had to make at a turning point in your life.",
        "ieltsSpeakingModel": "Choosing to specialize in complex network engineering felt like standing at a crossroads; while I knew I should never burn my bridges professionally, taking that leap of faith opened tremendous opportunities."
    },

    # ==================== Lady Gaga (2 題) ====================
    {
        "id": "lg_2",
        "work": "Lady Gaga",
        "workEn": "Born This Way",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "Do not hide yourself in regret; embrace who you are and march to the beat of your own drum.",
        "clozedTemplate": "Do not hide yourself in [1]; embrace who you are and march to the beat of [2].",
        "blanks": ["regret", "your own drum"],
        "listeningTip": "注意 beat of your 連讀成 /biː-ɾəv-jʊr/；march to the beat of your own drum 意為「按照自己的節奏前進、不盲從」。",
        "sentenceZh": "不要把自己躲藏在悔恨之中；擁抱真實的自我，按照自己的鼓點與節奏勇敢前行。",
        "casualPhrase": "march to the beat of your own drum",
        "casualExplain": "特立獨行、走自己的路而不盲從大眾",
        "registerQuestion": "Lady Gaga《Born This Way》鼓勵人們 "march to the beat of your own drum"。若要在【雅思寫作 Task 2】論述「教育體系應鼓勵獨立思考與個人自主性，而非盲目從眾」，哪個學術替換最精準？",
        "registerOptions": [
          "foster intellectual autonomy rather than uncritical conformity",
          "play loud percussion instruments during school assemblies",
          "walk in a military parade every morning",
          "ignore all established traffic regulations"
        ],
        "academicAnswer": "foster intellectual autonomy rather than uncritical conformity",
        "academicSentence": "Progressive educational curricula should foster intellectual autonomy rather than uncritical conformity among students.",
        "stressGuide": "Do NOT HIDE yourSELF in reGRET; emBRACE who you ARE and MARCH to the BEAT‿of your OWN DRUM.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Individuality vs. Conformity",
        "ieltsSpeakingQ": "Do you think society today encourages people to be unique or to follow trends?",
        "ieltsSpeakingModel": "Social media algorithms often pressure people to follow fleeting trends, so it takes genuine confidence to march to the beat of your own drum and maintain intellectual autonomy."
    },
    {
        "id": "lg_3",
        "work": "Lady Gaga",
        "workEn": "Million Reasons",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "You are giving me a million reasons to walk away, yet I only need one good reason to stick it out.",
        "clozedTemplate": "You are giving me a million reasons to [1], yet I only need one good reason to [2].",
        "blanks": ["walk away", "stick it out"],
        "listeningTip": "注意 walk away 連讀成 /wɔː-kə-weɪ/；stick it out 連讀成 /stɪ-kɪ-taʊt/，意為「咬牙堅持到底」。",
        "sentenceZh": "你給了我一百萬個轉身離開的理由，但我只需要一個好理由就能咬牙堅持下去。",
        "casualPhrase": "stick it out",
        "casualExplain": "堅持到底、在艱難處境中撐下去",
        "registerQuestion": "《Million Reasons》對比放棄與堅持（"stick it out"）。若要在【雅思寫作 Task 2】論述「長期科學研究需要研究人員在面對初期失敗時展現堅韌不拔的毅力」，哪個學術動詞最貼切？",
        "registerOptions": [
          "persevere despite protracted experimental setbacks",
          "glue wooden sticks outside the laboratory",
          "walk away from difficult university exams",
          "count a million reasons on a spreadsheet"
        ],
        "academicAnswer": "persevere despite protracted experimental setbacks",
        "academicSentence": "Breakthrough medical discoveries require scientists to persevere despite protracted experimental setbacks and funding uncertainties.",
        "stressGuide": "You are GIVing me a MILlion REAsons to WALK‿aWAY, yet I ONly NEED ONE GOOD REAson to STICK‿it‿OUT.",
        "ieltsSpeakingPart": "IELTS Speaking Part 2 · Perseverance & Long-Term Goals",
        "ieltsSpeakingQ": "Why do some people succeed in achieving long-term goals while others give up?",
        "ieltsSpeakingModel": "Success usually comes down to intrinsic motivation—when you have a clear underlying purpose, you are willing to stick it out and persevere through inevitable plateaus."
    },

    # ==================== Billie Eilish (2 題) ====================
    {
        "id": "be_2",
        "work": "Billie Eilish",
        "workEn": "bad guy",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "So you are a tough guy who likes it really rough, always pushing boundaries just to get under my skin.",
        "clozedTemplate": "So you are a tough guy who likes it really rough, always pushing [1] just to get [2].",
        "blanks": ["boundaries", "under my skin"],
        "listeningTip": "注意 get under my skin 在美式口語中 get 的 t 常變成閃音 /ɡe-ɾʌn-dɚ/，意為「激怒某人、讓人心煩」。",
        "sentenceZh": "原來你是個喜歡硬碰硬的狠角色，總愛不斷試探底線，就為了故意惹我心煩。",
        "casualPhrase": "pushing boundaries / get under my skin",
        "casualExplain": "試探底線、突破界限 / 激怒某人、讓人心煩意亂",
        "registerQuestion": "Billie Eilish《bad guy》提到故意挑釁讓人 "get under my skin"。若要在【雅思寫作 Task 2】論述「網路酸民的惡意挑釁行為會對青少年造成嚴重的心理困擾」，哪個表達最學術？",
        "registerOptions": [
          "inflict acute psychological distress on vulnerable adolescents",
          "crawl underneath someone's epidermis layer",
          "push physical fences around a school playground",
          "act like a tough movie villain on television"
        ],
        "academicAnswer": "inflict acute psychological distress on vulnerable adolescents",
        "academicSentence": "Unmoderated cyberbullying can inflict acute psychological distress on vulnerable adolescents and erode self-esteem.",
        "stressGuide": "ALways PUSHing BOUNDaries JUST to GET‿UNder my SKIN.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Online Behaviour & Cyberbullying",
        "ieltsSpeakingQ": "Why do some people behave more aggressively online than they do in face-to-face conversations?",
        "ieltsSpeakingModel": "Anonymity lowers social accountability, emboldening trolls to push boundaries and intentionally get under people's skin in ways they would never dare in person."
    },
    {
        "id": "be_3",
        "work": "Billie Eilish",
        "workEn": "everything i wanted",
        "category": "singer",
        "ytId": "",
        "startSec": 0,
        "endSec": 6,
        "fullSentence": "I had a dream I got everything I wanted, only to realize that fame can be a double-edged sword.",
        "clozedTemplate": "I had a dream I got everything I [1], only to realize that fame can be a [2].",
        "blanks": ["wanted", "double-edged sword"],
        "listeningTip": "注意 everything I wanted 連讀成 /ˈev.ri.θɪŋ-aɪ-ˈwɑːn.tɪd/；double-edged sword 意為「雙面刃」。",
        "sentenceZh": "我曾夢見自己得到了夢寐以求的一切，卻隨即體認到成名其實是一把雙面刃。",
        "casualPhrase": "double-edged sword",
        "casualExplain": "雙面刃（同時帶來巨大利益與沉重代價）",
        "registerQuestion": "《everything i wanted》反思成名猶如 "double-edged sword"。若要在【雅思寫作 Task 2】開頭段精準表達「全球化或成名是一個兼具顯著優勢與潛在弊端的雙面現象」，哪個學術句型最加分？",
        "registerOptions": [
          "a paradoxical phenomenon yielding both substantial benefits and inherent drawbacks",
          "a medieval metal weapon sharpened on both sides",
          "a pleasant dream about winning a music award",
          "getting every single item on a shopping list"
        ],
        "academicAnswer": "a paradoxical phenomenon yielding both substantial benefits and inherent drawbacks",
        "academicSentence": "Rapid algorithmic automation represents a paradoxical phenomenon yielding both substantial benefits and inherent drawbacks for the labor market.",
        "stressGuide": "I HAD a DREAM I GOT EVerything I WANTed, ONly to REalize that FAME can be a DOUble-EDGED SWORD.",
        "ieltsSpeakingPart": "IELTS Speaking Part 3 · Fame, Privacy & Success",
        "ieltsSpeakingQ": "What are the disadvantages of becoming famous at a young age?",
        "ieltsSpeakingModel": "As Billie Eilish poignantly illustrates, early fame is truly a double-edged sword—it brings financial freedom, yet the relentless public scrutiny and loss of privacy can take a heavy toll on mental health."
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
    """排除前 2,500 個基礎單字，只收錄真正 IELTS Band 7.5+ 與美劇進階詞彙至 10,000 單"""
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
                if not word or not word.isalpha() or len(word) < 5 or not word.islower():
                    continue
                if word in vocab_map:
                    continue

                zh_raw = (row.get("translation") or "").strip().replace("\\n", "；")
                if not zh_raw:
                    continue

                bnc = int(row.get("bnc") or 99999)
                frq = int(row.get("frq") or 99999)
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
    """同步將新增的美劇/金曲語境與每日國際新聞寫入 ielts_bank.json 動態題庫"""
    bank = load_json(BANK_FILE, {"listening": [], "reading": [], "writing": [], "speaking": [], "quizPool": []})
    clean_pool = [
        q for q in bank.get("quizPool", [])
        if not q.get("id", "").startswith("web_ielts_")
        and "elevates your IELTS Band score" not in q.get("question", "")
    ]

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

    bank["quizPool"] = clean_pool[-100:]
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
    print(f"✅ 已同步更新 {POP_BANK_FILE}，新增擴充題庫共 {len(merged)} 組！")


if __name__ == "__main__":
    vocab_data = build_clean_10k_vocab()
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(vocab_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已更新 {VOCAB_FILE}，共 {len(vocab_data)} 筆 IELTS 7.5+ 與美劇高頻詞彙！")

    update_ielts_quiz_bank(vocab_data)
    update_pop_ielts_bank()
