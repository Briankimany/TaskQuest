
## Disclaimer

This system was developed as a personal project and for individual use. It is best suited for those who appreciate gaming mechanics and reward-based systems. While it can be a powerful tool for motivation and productivity, its effectiveness may vary depending on personal preferences and work styles. 

- [API-DOCS](https://cynic1.pythonanywhere.com/docs)

## Introduction

The TaskQuest System is a web application that Transforms your daily schedule into a game-like interface. It allows users to:

- Create and manage activities and sub-activities
- Schedule tasks on a daily basis
- Complete tasks to gain experience points (EXP) and level up
- Track progress with a character sheet-style dashboard
- Visualize daily discipline and productivity

## Features

- User authentication and profile management
- Activity and sub-activity creation and management
- Daily task scheduling and timetable view
- Task completion with EXP rewards
- Character leveling system with attributes (INT, STA, FCS, CHA, DSC)
- Dashboard for quick overview of progress and scheduled tasks
- API endpoints for data retrieval and task management



## 🚀 How to Use

### 1. 🔗 Hosted Version
You can try it live at: [https://cynic1.pythonanywhere.com](https://cynic1.pythonanywhere.com)

---

### 2. 🛠️ Local Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Briankimany/TaskQuest.git 
   cd TaskQuest
   ```
2. **Install Requirements**

   ```bash
   cd app
   pip install -r requirements.txt
   ```

3. **Run the Application**

   ```bash
   python3 run.py
   ```

4. **Access the App**
   Open your browser and go to:
   [http://localhost:5000](http://localhost:5000)


## 🤖 LLM Judge / OmniRoute

The System Judge and late/skip-penalty evaluation run through [OmniRoute](https://omniroute.local) combos rather than a direct model API key. Key points:

- **Combos carry their own auth.** A combo like `taskquest-judge-google` resolves to a provider (*e.g.* Google Gemini) whose connection is authenticated server-side inside OmniRoute. TaskQuest sends **no** per-request session id (`x-opencode-session`) and only an optional `OMNIROUTE_API_KEY` Bearer token.
- **Config**: `OMNIROUTE_URL` (proxy base URL) and `OMNIROUTE_MODEL` (combo id) as environment variables; defaults live in `app/seed/data/assistant/provider_config.yaml`.
- **Graceful fallback**: if the proxy is unreachable the app never hangs — evaluation falls back instantly to deterministic multipliers and marks reviews `PROVISIONAL`, with a LIVE / PROVISIONAL / OFF status pill on the dashboard and judge log.


## Coming Soon: Portable Version 🚀

- I'm tinkering with a MicroPython-powered server version for Windows! The goal is to make setup super simple - just double-click a .bat file and you're ready to play with the system.

This side project is all about:
- Making it easier to try out
- Learning more about portable Python implementations
