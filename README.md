# Telegram Ghost Detector

Telegram bot using **Telethon** to detect and remove ghost (deleted) accounts from groups.  

---

## ⚙️ Setup
1. Clone repo & install deps:
   ```bash
   git clone https://github.com/mencretsu/tg-ghost-detector
   cd tg-ghost-detector
   pip install -r requirements.txt
2. Create ```.env```
3. Run: ```python detector.py```

## 📖 Commands
```/start``` → Show bot info (private only).

```/scanmembers``` → Scan group for ghost accounts.

Button → Remove ghost accounts.

## ⚠️ Notes
Bot must be admin with Ban Members permission.

Only group admins can run ```/scanmembers```
