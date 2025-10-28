# Quick Start Guide - YouTube Monitoring

## ✅ Setup Complete!

Your bot now monitors [@yirmibirbitcoin](https://www.youtube.com/@yirmibirbitcoin) for new videos.

## Start the Bot

```bash
cd /home/kasita/Documents/yirmibirbitcoinbot
python bot.py
```

## What to Expect

After starting, you'll see in the logs:
```
✅ Initialized YouTube monitor with existing video
✅ YouTube monitoring started
```

## When a New Video is Published

**Within 30 minutes**, the bot will automatically post to the Telegram group:

```
🎬 *Yeni Video:* [Video Title]

[Video Link]
```

## Test Current Setup

```bash
# Check channel ID detection
python3 -c "from utils.youtube_monitor import get_channel_id_from_handle; print(get_channel_id_from_handle())"

# Expected output: UCugsZu41X5nxL_6XJxT5vlg
```

## Current Settings

- **Check Every**: 30 minutes
- **Channel**: @yirmibirbitcoin
- **Latest Video** (pre-loaded): https://youtu.be/eNw-xsqOlfE
- **Target**: YirmibirBitcoin Telegram group

## Customization

### Change Check Frequency

Edit `.env`:
```bash
YOUTUBE_CHECK_INTERVAL=1800  # 30 minutes (default)
YOUTUBE_CHECK_INTERVAL=900   # 15 minutes (faster)
YOUTUBE_CHECK_INTERVAL=3600  # 1 hour (slower)
```

### View Logs

```bash
# Watch in real-time
tail -f bot.log | grep -i youtube

# Check recent YouTube activity
grep -i youtube bot.log | tail -20
```

## Automated Content Schedule

| Content | Frequency | Next Check |
|---------|-----------|------------|
| 🎬 YouTube Videos | 30 min | After bot starts |
| 🎙️ Podcast Episodes | 1 hour | After bot starts |
| 💭 Satoshi Quotes | 24 hours | After bot starts |

## All Set! 🎉

Your bot is ready to monitor YouTube and post new videos automatically.

---

**Need Help?**
- Full docs: [YOUTUBE_MONITORING.md](YOUTUBE_MONITORING.md)
- Implementation: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- Main README: [README.md](README.md)

