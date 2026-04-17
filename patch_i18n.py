import json

def update_locale(filepath, data):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = json.load(f)
    
    if "dashboard" not in content:
        content["dashboard"] = {}
        
    for k, v in data.items():
        content["dashboard"][k] = v
        
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

update_locale("frontend/messages/en.json", {
    "roi": "AI ROI (30d)",
    "period_7d": "7 days",
    "period_30d": "30 days",
    "period_90d": "90 days"
})

update_locale("frontend/messages/ar.json", {
    "roi": "عائد الاستثمار (AI)",
    "period_7d": "7 أيام",
    "period_30d": "30 يومًا",
    "period_90d": "90 يومًا"
})

update_locale("frontend/messages/tr.json", {
    "roi": "AI Yatırım Getirisi",
    "period_7d": "7 gün",
    "period_30d": "30 gün",
    "period_90d": "90 gün"
})
