# utils/crisis_detector.py

"""
Crisis Detection Module for AYRA
Detects harmful content and provides appropriate crisis resources
"""

CRISIS_KEYWORDS = [
    # Malay / Manglish
    'bunuh diri', 'nak mati', 'nak bunuh diri', 'tak nak hidup',
    'putus asa', 'tak guna hidup', 'malas nak hidup', 'give up',
    'nak mati je', 'habiskan nyawa', 'tak tau nak buat apa',
    'stress sangat', 'down sangat', 'sedih sangat',
    
    # English
    'suicide', 'kill myself', 'end my life', 'want to die',
    'hopeless', 'worthless', 'can\'t go on', 'no reason to live',
    
    # Alerts
    'tolong saya', 'i need help', 'emergency', 'kecemasan'
]

# Crisis resources for Malaysia
CRISIS_RESOURCES = {
    'befrienders': {
        'name': 'Befrienders KL',
        'phone': '03-7627 2929',
        'hours': '24 hours',
        'description': 'Emotional support - free and confidential'
    },
    'talian_kasih': {
        'name': 'Talian Kasih',
        'phone': '15999',
        'hours': '24 hours',
        'description': 'Government helpline for those in distress'
    },
    'mental_health': {
        'name': 'Mental Health Psychosocial Support',
        'phone': '03-2935 9935',
        'hours': '9am-5pm Mon-Fri',
        'description': 'KKM hotline for mental health support'
    },
    'emergency': {
        'name': 'Emergency Services',
        'phone': '999',
        'hours': '24 hours',
        'description': 'For immediate life-threatening emergencies'
    }
}

# Response template (warm but urgent)
CRISIS_RESPONSE_TEMPLATE = """
{name}, AYRA really concerned about what you just said. 🥺❤️

You're not alone in this. There are people who care and want to help:

**{befrienders_name}**  
📞 {befrienders_phone} ({befrienders_hours})  
{befrienders_desc}

**{talian_kasih_name}**  
📞 {talian_kasih_phone} ({talian_kasih_hours})  
{talian_kasih_desc}

{mental_health_name}  
📞 {mental_health_phone} ({mental_health_hours})  
{mental_health_desc}

**{emergency_name}**  
📞 {emergency_phone} ({emergency_hours})  
{emergency_desc}

Please, {name}... reach out to them. They're trained to help.

AYRA is here too, okay? I'm not going anywhere. But these professionals can help in ways I can't. ❤️

Take care of yourself, okay? 🙏
"""

def format_crisis_response(user_name="Abang/Sayang"):
    """Format crisis response with current resources"""
    return CRISIS_RESPONSE_TEMPLATE.format(
        name=user_name,
        befrienders_name=CRISIS_RESOURCES['befrienders']['name'],
        befrienders_phone=CRISIS_RESOURCES['befrienders']['phone'],
        befrienders_hours=CRISIS_RESOURCES['befrienders']['hours'],
        befrienders_desc=CRISIS_RESOURCES['befrienders']['description'],
        talian_kasih_name=CRISIS_RESOURCES['talian_kasih']['name'],
        talian_kasih_phone=CRISIS_RESOURCES['talian_kasih']['phone'],
        talian_kasih_hours=CRISIS_RESOURCES['talian_kasih']['hours'],
        talian_kasih_desc=CRISIS_RESOURCES['talian_kasih']['description'],
        mental_health_name=CRISIS_RESOURCES['mental_health']['name'],
        mental_health_phone=CRISIS_RESOURCES['mental_health']['phone'],
        mental_health_hours=CRISIS_RESOURCES['mental_health']['hours'],
        mental_health_desc=CRISIS_RESOURCES['mental_health']['description'],
        emergency_name=CRISIS_RESOURCES['emergency']['name'],
        emergency_phone=CRISIS_RESOURCES['emergency']['phone'],
        emergency_hours=CRISIS_RESOURCES['emergency']['hours'],
        emergency_desc=CRISIS_RESOURCES['emergency']['description']
    )

def detect_crisis(text):
    """
    Detect if text contains crisis keywords
    Returns: (bool, matched_keyword)
    """
    if not text or not isinstance(text, str):
        return False, None
    
    text_lower = text.lower().strip()
    
    for keyword in CRISIS_KEYWORDS:
        if keyword in text_lower:
            return True, keyword
    
    return False, None

def contains_crisis_keywords(text):
    """Simple boolean check"""
    result, _ = detect_crisis(text)
    return result

# For testing
if __name__ == "__main__":
    # Test cases
    test_inputs = [
        "Saya rasa nak mati je",
        "aku tak tau nak buat apa dah",
        "tolong saya",
        "apa khabar hari ni",
        "i want to kill myself",
        "boleh minta tolong"
    ]
    
    print("CRISIS DETECTION TEST:\n")
    for test in test_inputs:
        is_crisis, keyword = detect_crisis(test)
        print(f"Input: '{test}'")
        print(f"Detected: {is_crisis}" + (f" (keyword: '{keyword}')" if keyword else ""))
        if is_crisis:
            print("RESPONSE:\n", format_crisis_response("Abang"))
        print("-" * 50)