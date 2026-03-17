# 🌙 Noctis

> Your private mental health notepad with a local AI companion

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

Noctis is a **100% local, privacy-first** mental health journaling application with an empathetic AI companion. Everything runs on your machine—no internet, no cloud, no data collection. Just you, your thoughts, and a supportive AI.

---

## ✨ Features

### 🔒 **Privacy First**
- **100% Local** - No internet connection required
- **Zero Data Collection** - Your notes never leave your device
- **Offline AI** - Powered by Ollama running entirely on your machine
- **Open Source** - Full transparency, audit the code yourself

### 📝 **Powerful Editor**
- **Multi-Tab Interface** - Work on multiple notes simultaneously
- **Auto-Save Tracking** - Visual indicators (●) show unsaved changes
- **Find & Replace** - Search and modify text across your notes
- **Image Support** - Paste or insert images directly (Ctrl+Shift+I)
- **Custom Fonts** - Choose your preferred monospace font and size

### 🤖 **AI Companion**
- **Empathetic Responses** - Trained for mental health support, not clinical advice
- **Smart Summarization** - Get quick insights from your notes
- **Grammar Fixing** - Improve writing while keeping your voice
- **Crisis Resources** - Built-in mental health helplines (India + Global)
- **Model: llama3.2:3b** - Fast, empathetic, runs on consumer hardware

### ⌨️ **Keyboard Shortcuts**
- `Ctrl+N` - New Tab
- `Ctrl+S` - Save
- `Ctrl+F` - Find & Replace
- `Ctrl+`` - Toggle AI Mode
- `Ctrl+Shift+I` - Insert Image
- [View all shortcuts in Help → About]

---

## 📦 Installation

### Requirements
- **Windows 10/11** (64-bit)
- **8GB+ RAM** (for AI model)
- **5GB free disk space**
- **Ollama** (AI runtime)

### Quick Start

**Option 1: Download Executable (Recommended)**

1. Download `Noctis.exe` from [Releases](https://github.com/ParthGhumatkar/noctis/releases)
2. Install Ollama from [ollama.com](https://ollama.com)
3. Start Ollama:
   ```bash
   ollama serve
   ```
4. Run `Noctis.exe`
5. **First Launch:** Setup wizard auto-downloads the AI model (2GB, ~10 minutes)
6. **Done!** Future launches are instant

**Option 2: Run from Source**

```bash
# Clone the repository
git clone https://github.com/ParthGhumatkar/noctis.git
cd noctis

# Install dependencies
pip install customtkinter requests pillow

# Install Ollama and start server
# Download from: https://ollama.com
ollama serve

# Setup AI model (first time only)
ollama pull llama3.2:3b
ollama create noctis-ai-v1 -f NoctisModel.v1

# Run Noctis
python main.py
```

---

## 🚀 Usage

### Writing Notes
1. **Create tabs** with `Ctrl+N` or the `+` button
2. **Type freely** - your notes auto-save on changes
3. **Paste images** with `Ctrl+V` or insert with `Ctrl+Shift+I`
4. **Organize** with multiple tabs for different topics

### Using the AI Companion
1. **Click the AI button** in the top-right corner
2. **Type after the `>>>`** prompt
3. **Press Enter** to send your message
4. The AI responds with empathy and support
5. **Toggle off** when you want to journal privately

### AI Features
- **Ask AI** - Start a conversation about how you're feeling
- **Summarize** - Get a gentle summary of your note
- **Fix Grammar** - Improve writing while keeping your tone

---

## 🔐 Privacy & Security

Noctis takes your privacy seriously:

- ✅ **No Internet Connection** - App works completely offline
- ✅ **No Analytics** - Zero tracking or telemetry
- ✅ **No Cloud Sync** - Notes stored locally only
- ✅ **Local AI** - Model runs on your device via Ollama
- ✅ **Open Source** - Code is auditable and transparent

**Data Storage:**
- Notes: Plain text files on your machine
- AI Model: Stored in Ollama's directory (`~/.ollama`)
- No encryption yet (planned for v2.0)

---

## 🛠️ Tech Stack

- **Language:** Python 3.13
- **GUI Framework:** CustomTkinter + Tkinter
- **AI Runtime:** Ollama
- **AI Model:** llama3.2:3b (custom fine-tuned)
- **Image Processing:** Pillow (PIL)
- **HTTP Requests:** requests library

---

## 🆘 Mental Health Resources

Noctis includes built-in crisis resources accessible via **Help → Crisis Resources**:

**India (24/7):**
- Vandrevala Foundation: +91 9999 666 555
- AASRA: +91 22 2754 6669
- National Mental Health Helpline: 1800-599-0019

**Global:**
- Befrienders Worldwide: [befrienders.org](https://befrienders.org)
- Find a Helpline: [findahelpline.com](https://findahelpline.com)

**Emergency (India):**
- Police: 100
- Ambulance: 108

---

## 🗺️ Roadmap

### v1.0 (Current)
- ✅ Multi-tab editor
- ✅ Local AI companion
- ✅ Image support
- ✅ Find & replace
- ✅ Custom fonts
- ✅ Auto-setup wizard

### v2.0 (Planned)
- 🔜 AES-256 file encryption
- 🔜 Master password protection
- 🔜 Secure file deletion
- 🔜 Export to PDF
- 🔜 Dark/Light theme toggle
- 🔜 macOS/Linux support

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report Bugs** - Open an issue with details
2. **Suggest Features** - Share your ideas
3. **Submit PRs** - Fork, improve, and submit
4. **Spread the Word** - Star ⭐ the repo if you find it helpful

### Development Setup

```bash
git clone https://github.com/ParthGhumatkar/noctis.git
cd noctis
pip install -r requirements.txt
python main.py
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

You are free to:
- ✅ Use commercially
- ✅ Modify
- ✅ Distribute
- ✅ Private use

---

## 💝 Acknowledgments

- **Ollama Team** - For making local AI accessible
- **Meta AI** - For the Llama model family
- **CustomTkinter** - For the modern UI framework
- **Mental Health Community** - For inspiring this project

---

## 👨‍💻 Author

**Parth Ghumatkar**

- GitHub: [@ParthGhumatkar](https://github.com/ParthGhumatkar)
- Project: [github.com/ParthGhumatkar/noctis](https://github.com/ParthGhumatkar/noctis)

---

## ⭐ Show Your Support

If Noctis helps you, please consider:
- ⭐ **Starring** this repository
- 🐛 **Reporting issues** you encounter
- 💡 **Suggesting features** you'd like to see
- 📢 **Sharing** with others who might benefit

---

## 📸 Screenshots



---

## ❓ FAQ

**Q: Is my data really private?**  
A: Yes! Everything runs locally. No internet connection, no cloud servers, no data collection.

**Q: Why do I need Ollama?**  
A: Ollama runs the AI model on your computer. It's like a local ChatGPT server.

**Q: Can I use this without AI?**  
A: Absolutely! The notepad works perfectly without AI. AI is optional.

**Q: Is this free?**  
A: Yes, completely free and open source under MIT license.

**Q: Does it work offline?**  
A: Yes! After initial setup, everything works offline.

**Q: Can I trust this with sensitive information?**  
A: The app itself is transparent (open source), but notes are stored as plain text files. We recommend using file encryption at the OS level for highly sensitive data. AES encryption is planned for v2.0.

---

<div align="center">

**🌙 Noctis - Your thoughts, your privacy, your safe space.**

Made with ❤️ for mental health and privacy

[Download](https://github.com/ParthGhumatkar/noctis/releases) • [Report Bug](https://github.com/ParthGhumatkar/noctis/issues) • [Request Feature](https://github.com/ParthGhumatkar/noctis/issues)

</div>
