"""
CampusPulse AI Training & Evaluation Dataset - Multilingual Edition
Focused on 3 core campus languages:
1. English (Standard English + Indian-English idioms)
2. Hindi (Devanagari script + Romanized Hinglish)
3. Bengali (Bengali script + Romanized Benglish)

Covers all 7 campus operational categories and cross-lingual semantic duplicate pairs.
"""

from typing import List, Dict, Tuple

CAMPUS_TRAINING_DATA: List[Dict[str, str]] = [
    # =========================================================================
    # 1. Hostel / Water
    # =========================================================================
    # English
    {"text": "No water in Block C since morning, taps are completely dry", "category": "Hostel / Water"},
    {"text": "Water stopped in Hostel C 2nd floor washrooms", "category": "Hostel / Water"},
    {"text": "Severe water crisis in Block C, cannot even brush teeth or take bath", "category": "Hostel / Water"},
    {"text": "Taps are bone dry in Block C wing 2, booster pump is off", "category": "Hostel / Water"},
    {"text": "Hostel C bathroom taps running with zero hydrostatic pressure", "category": "Hostel / Water"},
    {"text": "Geyser in 3rd floor hostel bathroom is not heating water at all, getting freezing cold water", "category": "Hostel / Water"},
    {"text": "Continuous pipe leakage in Block A toilet, water is accumulating on tiles", "category": "Hostel / Water"},
    {"text": "Flush tank valve broken in room 214 washroom, water overflowing non-stop", "category": "Hostel / Water"},
    {"text": "Drinking water cooler on 1st floor hostel has dirty yellowish water coming out", "category": "Hostel / Water"},
    {"text": "Shower head broken and spraying water all over the hostel corridor ceiling", "category": "Hostel / Water"},
    {"text": "Drainage clogged in hostel washroom, dirty soapy water backing up", "category": "Hostel / Water"},
    # Hindi (Devanagari)
    {"text": "हॉस्टल सी में सुबह से बिल्कुल पानी नहीं आ रहा है, नल सूखे पड़े हैं", "category": "Hostel / Water"},
    {"text": "ब्लॉक सी की दूसरी मंजिल के बाथरूम में पानी बंद है", "category": "Hostel / Water"},
    {"text": "बाथरूम का गीजर पानी गर्म नहीं कर रहा, कड़ाके की ठंड में बर्फ जैसा पानी आ रहा है", "category": "Hostel / Water"},
    {"text": "हॉस्टल वॉशरूम का फ्लश टूट गया है और पानी लगातार बह रहा है", "category": "Hostel / Water"},
    {"text": "पीने के पानी के वाटर कूलर से गंदा पीला पानी निकल रहा है", "category": "Hostel / Water"},
    # Hinglish (Romanized Hindi)
    {"text": "Block C me paani bilkul band hai subah se, taps dry hai", "category": "Hostel / Water"},
    {"text": "Hostel C 2nd floor bathroom me paani nahi aa raha hai", "category": "Hostel / Water"},
    {"text": "Geyser kharab ho gaya hai 3rd floor bathroom me, ekdam chilled paani aa raha hai", "category": "Hostel / Water"},
    {"text": "Flush tank toot gaya hai room 214 washroom me, continuously overflow kar raha hai", "category": "Hostel / Water"},
    {"text": "Paani ki bohot dikkat hai hostel me, motor chalu karwao please", "category": "Hostel / Water"},
    # Bengali (Bengali Script)
    {"text": "হোস্টেল সি-তে সকাল থেকে কোনো জল নেই, বাথরুমের কল একদম শুকনো", "category": "Hostel / Water"},
    {"text": "ব্লক সি এর দোতলার বাথরুমে জল আসছে না, মোটর বন্ধ আছে", "category": "Hostel / Water"},
    {"text": "৩য় তলার বাথরুমে গিজার কাজ করছে না, প্রচণ্ড ঠান্ডা জল আসছে স্নান করা যাচ্ছে না", "category": "Hostel / Water"},
    {"text": "হোস্টেল বাথরুমের পাইপ লিক করছে, পুরো মেঝেতে নোংরা জল জমে গেছে", "category": "Hostel / Water"},
    {"text": "খাবার জলের কুলার থেকে নোংরা ঘোলাটে জল বের হচ্ছে হোস্টেলে", "category": "Hostel / Water"},
    # Benglish (Romanized Bengali)
    {"text": "Hostel C-te shokal theke jol nei, baathroomer tap puro shukno", "category": "Hostel / Water"},
    {"text": "Block C 2nd floor e jol asche na, motor bondho ache mone hoy", "category": "Hostel / Water"},
    {"text": "Geesar kaaj korche na 3rd floor e, eto thandaye borof jol asche", "category": "Hostel / Water"},
    {"text": "Bathroom er pipe leak kore shob jol jome geche hostel floor e", "category": "Hostel / Water"},
    {"text": "Jol er line bondho hoye ache hostel C te, bath kora jache na", "category": "Hostel / Water"},

    # =========================================================================
    # 2. IT / Network
    # =========================================================================
    # English
    {"text": "WiFi isn't working in Lab 3, terminals cannot connect to internet", "category": "IT / Network"},
    {"text": "High packet loss and ping spikes on campus eduroam in CS Turing block", "category": "IT / Network"},
    {"text": "Subnet gateway unreachable from workstations in Turing Computer Lab 3", "category": "IT / Network"},
    {"text": "Campus portal login gateway timing out during course registration", "category": "IT / Network"},
    {"text": "Internet access point dropped out in 2nd floor library east wing", "category": "IT / Network"},
    {"text": "LAN port on desk 14 in computer centre is dead, no ethernet link light", "category": "IT / Network"},
    {"text": "Student portal ERP throwing 502 bad gateway error when trying to view hall ticket", "category": "IT / Network"},
    {"text": "DNS server failing to resolve internal university github server", "category": "IT / Network"},
    # Hindi (Devanagari)
    {"text": "कंप्यूटर लैब 3 में वाई-फाई बिल्कुल नहीं चल रहा है, इंटरनेट बंद है", "category": "IT / Network"},
    {"text": "कॉलेज का स्टूडेंट पोर्टल लॉगिन नहीं हो रहा, 502 गेटवे टाइम आउट आ रहा है", "category": "IT / Network"},
    {"text": "कैंपस इंटरनेट बहुत धीमा है, प्रैक्टिकल एग्जाम के लिए कोडिंग साइट्स नहीं खुल रही हैं", "category": "IT / Network"},
    {"text": "ट्यूरिंग लैब के कंप्यूटर नेटवर्क से कनेक्ट नहीं हो पा रहे हैं", "category": "IT / Network"},
    # Hinglish
    {"text": "Lab 3 ka wifi connection bar bar disconnect ho raha hai", "category": "IT / Network"},
    {"text": "Portal pe hall ticket download nahi ho raha gateway time out aa raha hai", "category": "IT / Network"},
    {"text": "Hostel room me wifi signal bohot weak hai, speed 0 hai bilkul", "category": "IT / Network"},
    {"text": "Turing lab me internet band hai, practical submission nahi ho pa raha", "category": "IT / Network"},
    {"text": "Campus-net wifi password accept nahi kar raha bar bar error de raha hai", "category": "IT / Network"},
    # Bengali (Bengali Script)
    {"text": "কম্পিউটার ল্যাব ৩-এ ওয়াইফাই কাজ করছে না, কোনো ইন্টারনেট কানেকশন নেই", "category": "IT / Network"},
    {"text": "স্টুডেন্ট পোর্টালে লগইন হচ্ছে না, সার্ভার ডাউন এবং টাইম আউট দেখাচ্ছে", "category": "IT / Network"},
    {"text": "ক্যাম্পাস ওয়াইফাই খুব স্লো, প্র্যাকটিক্যাল কোডিং অ্যাসাইনমেন্ট সাবমিট করা যাচ্ছে না", "category": "IT / Network"},
    {"text": "লাইব্রেরির রিডিং রুমে ওয়াইফাই রাউটার অফ হয়ে আছে", "category": "IT / Network"},
    # Benglish
    {"text": "Lab 3 er wifi puro down, internet e connect kora jacche na", "category": "IT / Network"},
    {"text": "Student portale marks dekhte gelei 502 gateway time out hocche", "category": "IT / Network"},
    {"text": "Eduroam wifi e bar bar disconnected hoye jacche Turing block e", "category": "IT / Network"},
    {"text": "Hostel e wifi signal paoa jacche na, net ekdom slow", "category": "IT / Network"},

    # =========================================================================
    # 3. Electrical
    # =========================================================================
    # English
    {"text": "Electricity keeps tripping off in Block B corridor", "category": "Electrical"},
    {"text": "Sparking observed from main distribution switchboard in Science block staircase", "category": "Electrical"},
    {"text": "Emergency lighting and corridor tube lights pitch dark in science quad stairwell", "category": "Electrical"},
    {"text": "Ceiling fan making loud grinding noise and vibrating dangerously in room 302", "category": "Electrical"},
    {"text": "Power socket in reading room giving mild electric shock when plugging laptop charger", "category": "Electrical"},
    {"text": "Classroom 401 has no power, main MCB tripped after spark near AC unit", "category": "Electrical"},
    {"text": "Streetlights between library and hostel 4 are completely dark, pitch black at night", "category": "Electrical"},
    {"text": "Switchboard melted and burning smell coming from 2nd floor switch box", "category": "Electrical"},
    # Hindi (Devanagari)
    {"text": "साइंस ब्लॉक की सीढ़ियों के स्विचबोर्ड से चिंगारी निकल रही है, बहुत बड़ा खतरा है", "category": "Electrical"},
    {"text": "हॉस्टल ब्लॉक बी में बार-बार बिजली ट्रिप हो रही है, लाइट चली जाती है", "category": "Electrical"},
    {"text": "कमरे का पंखा बहुत तेज आवाज कर रहा है और हिल रहा है, कभी भी गिर सकता है", "category": "Electrical"},
    {"text": "स्विच बोर्ड से जलने की बदबू आ रही है और प्लग काला पड़ गया है", "category": "Electrical"},
    # Hinglish
    {"text": "Science quad me switchboard se spark nikal raha hai short circuit ho sakta hai", "category": "Electrical"},
    {"text": "Block B corridor me bar bar light jaa rahi hai mcb trip ho raha hai", "category": "Electrical"},
    {"text": "Room 302 me ceiling fan bohot awaaz kar raha hai dangerous lag raha hai", "category": "Electrical"},
    {"text": "Laptop charger lagane par socket me se current lag raha hai reading room me", "category": "Electrical"},
    {"text": "Library ke raste me streetlights band hai, raat ko andhera rehta hai", "category": "Electrical"},
    # Bengali (Bengali Script)
    {"text": "সায়েন্স ব্লকের সিঁড়ির মেইন সুইচবোর্ড থেকে স্পার্ক বের হচ্ছে, শর্ট সার্কিট হতে পারে", "category": "Electrical"},
    {"text": "হোস্টেল ব্লক বি-তে বারবার বিদ্যুৎ চলে যাচ্ছে এবং লাইট ট্রিপ করছে", "category": "Electrical"},
    {"text": "হোস্টেলের ঘরের ফ্যান ভীষণ আওয়াজ করছে এবং কাঁপছে, ভেঙে পড়ার ভয় আছে", "category": "Electrical"},
    {"text": "সুইচবোর্ড পুড়ে গন্ধ বের হচ্ছে এবং প্লাগ গলে গেছে", "category": "Electrical"},
    # Benglish
    {"text": "Science block er switchboard theke sparking hocche, dangerous obostha", "category": "Electrical"},
    {"text": "Block B corridor e baar baar power cut hocche, MCB trip korche", "category": "Electrical"},
    {"text": "Ghorer ceiling fan ta prochondo aowaj korche, off kore rekhechi", "category": "Electrical"},
    {"text": "Socket e plug lagale mild electric shock lagche library table e", "category": "Electrical"},

    # =========================================================================
    # 4. Food / Mess
    # =========================================================================
    # English
    {"text": "Food quality in mess is terrible, dal is completely watery and tasteless", "category": "Food / Mess"},
    {"text": "Dining hall food served cold, steam warmers in mess 1 are not switched on", "category": "Food / Mess"},
    {"text": "Found insect and dirt in rice served at central dining mess today lunch", "category": "Food / Mess"},
    {"text": "Undercooked rotis and raw vegetable curry served to students in hostel mess", "category": "Food / Mess"},
    {"text": "Mess staff not wearing hairnets or gloves while serving meals", "category": "Food / Mess"},
    {"text": "Stale breakfast bread served, multiple students complaining of stomach ache", "category": "Food / Mess"},
    {"text": "Plates and spoons in dining hall have greasy residue, not washed with warm water", "category": "Food / Mess"},
    # Hindi (Devanagari)
    {"text": "मेस का खाना बहुत ही खराब है, दाल में सिर्फ पानी है और रोटियां कच्ची हैं", "category": "Food / Mess"},
    {"text": "डाइनिंग हॉल में खाना बिल्कुल ठंडा परोसा जा रहा है, हीटर बंद है", "category": "Food / Mess"},
    {"text": "आज दोपहर मेस के चावल में कीड़ा निकला है, बहुत ही अस्वच्छ खाना है", "category": "Food / Mess"},
    {"text": "मेस में बासी खाना देने से कई छात्रों की तबीयत खराब हो गई है", "category": "Food / Mess"},
    # Hinglish
    {"text": "Mess ka khana bilkul bekar hai, dal paani jaisi hai aur sabzi kacchi hai", "category": "Food / Mess"},
    {"text": "Dining hall me khana bilkul cold serve kar rahe hai, heater on nahi hai", "category": "Food / Mess"},
    {"text": "Rice me insect mila hai mess 1 me aaj lunch time par, inspection karo", "category": "Food / Mess"},
    {"text": "Mess ke bartan saaf nahi dhoye jate, oily smell aati hai thali se", "category": "Food / Mess"},
    # Bengali (Bengali Script)
    {"text": "মেসের খাবারের মান খুব খারাপ, ডালে শুধু জল আর কোনো স্বাদ নেই", "category": "Food / Mess"},
    {"text": "ডাইনিং হলে একদম ঠান্ডা খাবার দেওয়া হচ্ছে, হিটার চলছে না মেসে", "category": "Food / Mess"},
    {"text": "আজকের মেসে ভাতের মধ্যে পোকা পাওয়া গেছে, চরম অস্বাস্থ্যকর অবস্থা", "category": "Food / Mess"},
    {"text": "রুটিগুলো কাঁচা এবং তরকারি বাসি দেওয়া হচ্ছে ডাইনিং হলে", "category": "Food / Mess"},
    # Benglish
    {"text": "Messer khabar ekdom baje, daal ta puro joler moto aar roti gulo kacha", "category": "Food / Mess"},
    {"text": "Dining hall e shob khabar thanda, khete para jacche na mess 1 e", "category": "Food / Mess"},
    {"text": "Bhaater moddhe poka paoa geche mess e, warden k complaint kora dorkar", "category": "Food / Mess"},
    {"text": "Mess er thala bati bhalo kore dhoa hoy na, tel tel gondho", "category": "Food / Mess"},

    # =========================================================================
    # 5. Sanitation
    # =========================================================================
    # English
    {"text": "Garbage cans overflowing near library entrance, foul smell everywhere", "category": "Sanitation"},
    {"text": "Hostel corridor dustbins haven't been emptied for 4 days, pests roaming", "category": "Sanitation"},
    {"text": "Severe foul odor and sewage smell coming from ground floor washroom vents", "category": "Sanitation"},
    {"text": "Cockroach and termite infestation spotted in hostel reading room carpet", "category": "Sanitation"},
    {"text": "Sanitary pad incinerator machine in ladies hostel washroom is jammed and broken", "category": "Sanitation"},
    {"text": "Washroom mirrors, sinks and commodes are unhygienic and covered in grime", "category": "Sanitation"},
    # Hindi (Devanagari)
    {"text": "लाइब्रेरी के पास कूड़ेदान भर कर बाहर गिर रहा है, बहुत बदबू आ रही है", "category": "Sanitation"},
    {"text": "हॉस्टल के वॉशरूम में सीवेज की दुर्गंध आ रही है, चार दिन से सफाई नहीं हुई", "category": "Sanitation"},
    {"text": "हॉस्टल के कमरों में कॉकरोच और कीड़े घूम रहे हैं, पेस्ट कंट्रोल की जरूरत है", "category": "Sanitation"},
    # Hinglish
    {"text": "Library ke samne dustbin overflow ho raha hai, smell unbearable hai", "category": "Sanitation"},
    {"text": "Hostel bathroom me cockroach ghoom rahe hai, cleaning bilkul nahi hoti", "category": "Sanitation"},
    {"text": "Washroom se sewer ki bhashan smell aa rahi hai ground floor par", "category": "Sanitation"},
    # Bengali (Bengali Script)
    {"text": "লাইব্রেরির সামনে ডাস্টবিন উপচে আবর্জনা পড়ছে, চারিদিকে তীব্র দুর্গন্ধ", "category": "Sanitation"},
    {"text": "হোস্টেল বাথরুম থেকে নর্দমার গন্ধ আসছে, অনেকদিন পরিষ্কার করা হয়নি", "category": "Sanitation"},
    {"text": "রিডিং রুমে আরশোলা এবং পোকার উপদ্রব হয়েছে, পেস্ট কন্ট্রোল দরকার", "category": "Sanitation"},
    # Benglish
    {"text": "Library r kache dustbin overflow korche, baje gondho charidike", "category": "Sanitation"},
    {"text": "Bathroom e cockroach ar poka ghurchhe, kono safai hocche na hostel e", "category": "Sanitation"},
    {"text": "Washroom theke sewer er gondho ber hocche ground floor e", "category": "Sanitation"},

    # =========================================================================
    # 6. Security
    # =========================================================================
    # English
    {"text": "Someone damaged and kicked down the hostel back exit door", "category": "Security"},
    {"text": "Bicycle stolen from bicycle stand outside mechanical department", "category": "Security"},
    {"text": "Unidentified strangers roaming near girls hostel gate without visitor passes", "category": "Security"},
    {"text": "CCTV camera at main gate is angled down and not functioning", "category": "Security"},
    {"text": "Room lock broken and belongings rummaged while student was in class", "category": "Security"},
    # Hindi (Devanagari)
    {"text": "हॉस्टल का पिछला दरवाजा किसी ने तोड़ दिया है, सुरक्षा का भारी खतरा है", "category": "Security"},
    {"text": "मैकेनिकल डिपार्टमेंट के बाहर स्टैंड से साइकिल चोरी हो गई है", "category": "Security"},
    {"text": "गर्ल्स हॉस्टल के पास अनजान लोग घूम रहे हैं बिना किसी पास के", "category": "Security"},
    # Hinglish
    {"text": "Hostel ka back gate kisi ne tod diya hai, security ka risk hai", "category": "Security"},
    {"text": "Cycle stand se cycle chori ho gayi mechanical block ke bahar", "category": "Security"},
    {"text": "Main gate ka CCTV camera band pada hai kaam nahi kar raha", "category": "Security"},
    # Bengali (Bengali Script)
    {"text": "হোস্টেলের পেছনের গেট কেউ ভেঙে ফেলেছে, রাতে সিকিউরিটির সমস্যা হচ্ছে", "category": "Security"},
    {"text": "মেকানিক্যাল ডিপার্টমেন্টের সাইকেল স্ট্যান্ড থেকে সাইকেল চুরি হয়ে গেছে", "category": "Security"},
    {"text": "মেইন গেটের সিসিটিভি ক্যামেরা কাজ করছে না, নষ্ট হয়ে আছে", "category": "Security"},
    # Benglish
    {"text": "Hostel er pichoner dorja keu bhenge feleche, safe mone hocche na", "category": "Security"},
    {"text": "Cycle stand theke cycle churi hoye geche, guard o chilo na", "category": "Security"},
    {"text": "Main gate er CCTV camera bondho hoye ache, check kora jacche na", "category": "Security"},

    # =========================================================================
    # 7. Academics / Facilities
    # =========================================================================
    # English
    {"text": "Professor hasn't uploaded midterm marks on the ERP portal", "category": "Academics / Facilities"},
    {"text": "Classroom 204 chairs and benches are broken, not enough seating for students", "category": "Academics / Facilities"},
    {"text": "Projector display in lecture hall 3 has purple hue and bulb is flickering constantly", "category": "Academics / Facilities"},
    {"text": "Whiteboard markers completely dried out in academic block wing C", "category": "Academics / Facilities"},
    {"text": "Library book return kiosk machine rejecting barcode scans", "category": "Academics / Facilities"},
    # Hindi (Devanagari)
    {"text": "पोर्टल पर मिडटर्म परीक्षा के नंबर अभी तक अपलोड नहीं किए गए हैं", "category": "Academics / Facilities"},
    {"text": "कमरा 204 में डेस्क और कुर्सियां टूटी हुई हैं, बैठने की जगह नहीं है", "category": "Academics / Facilities"},
    {"text": "लेक्चर हॉल 3 का प्रोजेक्टर खराब है और स्क्रीन बार बार झिलमिला रही है", "category": "Academics / Facilities"},
    # Hinglish
    {"text": "Prof ne midterm marks abhi tak portal pe upload nahi kiye", "category": "Academics / Facilities"},
    {"text": "Classroom 204 me bench tooti hui hai, baithne ki jagah nahi hai", "category": "Academics / Facilities"},
    {"text": "Lecture hall ka projector display flicker kar raha hai padhai me dikkat ho rahi hai", "category": "Academics / Facilities"},
    # Bengali (Bengali Script)
    {"text": "প্রফেসর এখনও পোর্টাল-এ মিডটার্ম পরীক্ষার নম্বর আপলোড করেননি", "category": "Academics / Facilities"},
    {"text": "ক্লাসরুম ২০৪-এর বেঞ্চ আর চেয়ারগুলো ভাঙা, বসার জায়গা নেই", "category": "Academics / Facilities"},
    {"text": "লেকচার হলের প্রজেক্টরের ডিসপ্লে কাঁপছে, বোর্ডে কিছু দেখা যাচ্ছে না", "category": "Academics / Facilities"},
    # Benglish
    {"text": "Midterm er marks ekhono ERP portale upload hoyni prof er theke", "category": "Academics / Facilities"},
    {"text": "Classroom e bench gulo bhenge geche, bosa jacche na 204 e", "category": "Academics / Facilities"},
    {"text": "Lecture hall 3 er projector ta noshto, screen flicker korche", "category": "Academics / Facilities"}
]


# -----------------------------------------------------------------------------
# 2. Paired Dataset for Duplicate Threshold Calibration (Cross-Lingual)
# -----------------------------------------------------------------------------
PAIRED_EVALUATION_DATA: List[Tuple[str, str, int]] = [
    # 1 = SAME (Duplicate Issue Cluster), 0 = DIFFERENT (Separate Incident)
    
    # --- POSITIVE PAIRS: English to English Paraphrase ---
    ("No water in Block C", "Water stopped in Hostel C 2nd floor", 1),
    ("Block C taps are bone dry", "Hostel C bathroom zero water pressure", 1),
    ("WiFi isn't working in Lab 3", "Internet in CS Turing lab 3 is completely down", 1),
    ("High ping and packet drops on campus wifi in Lab 3", "WiFi gateway unreachable in Turing Computer Lab 3", 1),
    ("Food quality in mess is terrible and cold", "Mess dal is watery and steam warmer is off", 1),
    ("Dining hall food served cold today", "Lunch was freezing cold in central dining mess 1", 1),
    ("Electricity keeps tripping in Block B", "Corridor lights blackout in Block B hostel", 1),
    ("Sparking from switchboard in science block staircase", "Main electrical distribution box sparking in Science quad", 1),
    ("Staircase lights pitch dark in science block", "Emergency lighting out on science quad stairwell", 1),
    ("Garbage cans overflowing near library gate", "Trash bin not emptied for days outside central library", 1),
    ("Bicycle stolen from mechanical department stand", "Cycle theft reported outside mechanical block", 1),

    # --- POSITIVE PAIRS: Cross-Lingual (English <-> Hindi <-> Bengali) ---
    ("No water in Block C since morning", "हॉस्टल सी में सुबह से बिल्कुल पानी नहीं आ रहा है", 1),
    ("Block C me paani bilkul band hai subah se", "হোস্টেল সি-তে সকাল থেকে কোনো জল নেই", 1),
    ("Hostel C-te shokal theke jol nei baathroom e", "हॉस्टल सी में पानी नहीं आ रहा है", 1),
    ("Taps are bone dry in Block C", "Block C me paani bilkul nahi aa raha", 1),
    ("WiFi isn't working in Lab 3", "कंप्यूटर लैब 3 में वाई-फाई बिल्कुल नहीं चल रहा है", 1),
    ("Lab 3 ka wifi connection bar bar disconnect ho raha hai", "কম্পিউটার ল্যাব ৩-এ ওয়াইফাই কাজ করছে না", 1),
    ("Lab 3 er wifi puro down internet connection nei", "Turing Computer Lab 3 internet completely down", 1),
    ("Food quality in mess is terrible", "मेस का खाना बहुत ही खराब है, दाल में सिर्फ पानी है", 1),
    ("Mess ka khana bilkul bekar hai dal paani jaisi hai", "মেসের খাবারের মান খুব খারাপ ডালে শুধু জল", 1),
    ("Messer khabar ekdom baje daal joler moto", "Mess dal is watery and tasteless", 1),
    ("Electricity keeps tripping off in Block B corridor", "हॉस्टल ब्लॉक बी में बार-बार बिजली ट्रिप हो रही है", 1),
    ("Block B corridor me bar bar light jaa rahi hai", "হোস্টেল ব্লক বি-তে বারবার বিদ্যুৎ চলে যাচ্ছে", 1),
    ("Someone damaged the hostel back exit door", "हॉस्टल का पिछला दरवाजा किसी ने तोड़ दिया है", 1),
    ("Hostel er pichoner dorja keu bhenge feleche", "Someone kicked down the hostel back door", 1),
    ("Professor hasn't uploaded midterm marks", "पोर्टल पर मिडटर्म परीक्षा के नंबर अभी तक अपलोड नहीं किए गए हैं", 1),
    ("Prof ne midterm marks abhi tak portal pe upload nahi kiye", "প্রফেসর এখনও পোর্টাল-এ নম্বর আপলোড করেননি", 1),

    # --- NEGATIVE PAIRS: Cross-domain or Cross-topic (DIFFERENT = 0) ---
    ("No water in Block C", "WiFi isn't working in Lab 3", 0),
    ("हॉस्टल सी में पानी नहीं आ रहा है", "কম্পিউটার ল্যাব ৩-এ ওয়াইফাই কাজ করছে না", 0),
    ("No water in Block C", "Electricity keeps tripping in Block B", 0),
    ("Block C me paani nahi aa raha", "Block B me light chali gayi", 0),
    ("WiFi isn't working in Lab 3", "Projector display in lecture hall 3 broken", 0),
    ("Food quality in mess is terrible", "Drinking water cooler in hostel 1 has yellowish water", 0),
    ("মেসের খাবারের মান খুব খারাপ", "হোস্টেলের পেছনের গেট কেউ ভেঙে ফেলেছে", 0),
    ("Electricity keeps tripping in Block B", "Hostel door lock damaged in Block B", 0),
    ("Garbage cans overflowing near library", "Library book return kiosk machine broken", 0),
    ("Sparking from switchboard in science block", "No water in science block washroom", 0),
    ("Bicycle stolen from mechanical department", "WiFi down in mechanical cad cam lab", 0),
    ("Cycle theft outside mechanical block", "Cycle puncture shop closed in campus", 0),
    ("Geyser in 3rd floor bathroom not heating", "Shower head broken in 1st floor bathroom", 0),
    ("Professor hasn't uploaded midterm marks", "Classroom 204 chairs and benches are broken", 0),
    ("Food is cold in mess", "WiFi is down in hostel", 0),
    ("Someone damaged hostel door", "WiFi password expired on campus-net", 0)
]
