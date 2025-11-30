# Quick Deploy to Hugging Face Spaces

## TL;DR - 5 Minute Deployment

### 1. Create Space (2 minutes)
Go to: https://huggingface.co/new-space

- **Name**: `scientific-content-agent`
- **SDK**: Gradio
- **Hardware**: CPU basic (free)
- Click "Create Space"

### 2. Clone and Copy Files (1 minute)
```bash
# Clone your new Space
git clone https://huggingface.co/spaces/YOUR_USERNAME/scientific-content-agent
cd scientific-content-agent

# Copy files from your project
cp ../agentic-content-generation/src . -r
cp ../agentic-content-generation/main.py .
cp ../agentic-content-generation/app.py .
cp ../agentic-content-generation/ui_app.py .
cp ../agentic-content-generation/requirements.txt .
cp ../agentic-content-generation/docs/README_HF_SPACES.md ./README.md
cp ../agentic-content-generation/.env.example .
```

Or use this one-liner:
```bash
cd scientific-content-agent && \
cp -r ../agentic-content-generation/{src,main.py,app.py,ui_app.py,requirements.txt,.env.example} . && \
cp ../agentic-content-generation/docs/README_HF_SPACES.md README.md
```

### 3. Push to HF (1 minute)
```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

### 4. Add API Key Secret (1 minute)
1. Go to: `https://huggingface.co/spaces/YOUR_USERNAME/scientific-content-agent/settings`
2. Click "Variables and secrets" → "New secret"
3. Name: `GOOGLE_API_KEY`
4. Value: Your API key from https://aistudio.google.com/app/api_keys
5. Click "Save"

### 5. Done! ✅
Your Space will build automatically (2-5 minutes)

Access it at: `https://huggingface.co/spaces/YOUR_USERNAME/scientific-content-agent`

---

## What You Get

✅ Free public URL for your portfolio
✅ No server maintenance
✅ Auto-updates when you push changes
✅ Ready for Kaggle submission (+5 bonus points!)

## Files You Need

```
scientific-content-agent/          (HF Space repo)
├── src/                           ← Copy from your project
│   ├── agents.py
│   ├── config.py
│   ├── tools.py
│   ├── profile.py
│   ├── session_manager.py
│   └── ...
├── main.py                        ← Copy from your project
├── app.py                         ← Copy from your project
├── ui_app.py                      ← Copy from your project
├── requirements.txt               ← Copy from your project
├── README.md                      ← Copy docs/README_HF_SPACES.md as README.md
└── .env.example                   ← Optional, for documentation
```

## Troubleshooting

**Build fails?**
- Check `requirements.txt` is present
- Verify `app.py` exists and imports correctly

**App runs but no generation?**
- Add `GOOGLE_API_KEY` secret in Space settings
- Or configure it in the Settings tab

**Need more help?**
See [HUGGINGFACE_DEPLOYMENT.md](./HUGGINGFACE_DEPLOYMENT.md) for detailed guide

## Update Your Space

```bash
cd scientific-content-agent
# Make changes...
git add .
git commit -m "Update: your changes"
git push origin main
```

Space rebuilds automatically!

---

**Pro Tip**: Add this badge to your GitHub README:

```markdown
[![Hugging Face Space](https://img.shields.io/badge/🤗-Hugging%20Face-yellow)](https://huggingface.co/spaces/YOUR_USERNAME/scientific-content-agent)
```
