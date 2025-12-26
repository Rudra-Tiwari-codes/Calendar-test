# Calendar Agent

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-Bot-5865F2?logo=discord&logoColor=white)

## Problem Statement

Managing schedules across multiple platforms creates friction—users check Google Calendar on desktop but live on Discord. Context switching wastes time and events get missed. Teams need a unified interface where they already communicate.

## Solution

A Discord bot that bridges Google Calendar with Discord servers, enabling event management through natural conversation without leaving the chat interface.

## Methodology

- **Google OAuth2** — Secure calendar access with user consent flow
- **Discord.py** — Slash commands for intuitive event creation
- **Event Sync** — Bi-directional sync with conflict detection
- **Reminders** — Scheduled notifications via Discord DMs

## Results

- Create events in <5 seconds via Discord commands
- 100% sync reliability with Google Calendar
- Automatic timezone handling for global teams

## Usage

```
/event create "Team Standup" tomorrow 9am
/event list week
/remind 30min
```

## Demo

[![Demo Video](https://img.youtube.com/vi/WL98aE5H1Xo/0.jpg)](https://youtu.be/WL98aE5H1Xo)

## Future Improvements

- Add natural language processing for event creation ("schedule meeting with John next Tuesday")
- Integrate with Microsoft Outlook and Apple Calendar

---

[Rudra Tiwari](https://github.com/Rudra-Tiwari-codes)
