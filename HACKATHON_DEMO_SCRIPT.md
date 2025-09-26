# 🎯 Calendar Agent Discord Bot - Hackathon Demo Script

## 🚀 **Opening Hook (30 seconds)**

*"Hey everyone! Ever struggled to manage your calendar while chatting with your team on Discord? We built something that changes everything. Meet the Calendar Agent - your AI-powered calendar assistant that lives right inside Discord."*

---

## 📋 **Demo Flow: "The Magic Moments"**

### **1. Setup & Introduction (1 minute)**

**SAY:** *"Let me show you how this works. I'm here in our Discord server, and I have our Calendar Agent bot running."*

**DO:**
```
/ping
```
**EXPECT:** `🏓 Pong! Bot is online and ready.`

**SAY:** *"First, I need to connect my Google Calendar. This is super secure - we use Supabase OAuth."*

**DO:**
```
/connect
```
**EXPECT:** Shows secure connection link

---

### **2. The Core Magic - Natural Language Parsing (2 minutes)**

**SAY:** *"Here's where it gets interesting. I can create calendar events using natural language, just like talking to a human assistant."*

#### **Demo A: Simple Event**
**DO:**
```
/addevent title:Team Standup when:tomorrow 9am
```
**SAY:** *"Look at that! It understood 'tomorrow 9am' and automatically:"*
- *"Converted it to the correct timezone (Australia/Melbourne)"*
- *"Set a 1-hour duration"*
- *"Created it in my actual Google Calendar"*

#### **Demo B: Complex Natural Language**
**DO:**
```
/addevent title:Hackathon Final Presentation when:Friday 2pm location:Tech Hub description:Demo our amazing bot!
```
**SAY:** *"It handles complex scheduling with locations, descriptions, and even figures out which Friday I mean!"*

#### **Demo C: Show the Intelligence**
**DO:**
```
/addevent title:Coffee Chat when:3pm September 26
```
**SAY:** *"Now here's the smart part - since it's already past 3pm today, it automatically schedules it for 3pm next year. No confusion!"*

---

### **3. Calendar Management Features (1.5 minutes)**

**SAY:** *"But it's not just about creating events. Let me show you the full calendar management experience."*

#### **View Your Events**
**DO:**
```
/myevents limit:3
```
**SAY:** *"I can see all my upcoming events, properly formatted in my local timezone."*

#### **Search Events**
**DO:**
```
/findevent query:hackathon
```
**SAY:** *"Need to find something specific? Intelligent search across all your events."*

#### **Event Details**
**DO:**
```
/eventdetails event_id:[copy from previous command]
```
**SAY:** *"Full event details with proper timezone display, attendees, locations - everything you need."*

#### **Modify Events**
**DO:**
```
/modifyevent event_id:[event_id] new_time:Friday 3pm new_location:Main Auditorium
```
**SAY:** *"And I can modify events on the fly - perfect for those last-minute changes."*

---

### **4. The Technical Wow Factor (1 minute)**

**SAY:** *"Now let me show you what's happening under the hood that makes this special:"*

#### **Timezone Intelligence**
**DO:** Open Google Calendar in browser
**SAY:** *"See how the event appears correctly in Google Calendar? We solved the timezone problem that plagues most calendar integrations. Events are stored in UTC but displayed in your local timezone everywhere."*

#### **Smart Parsing**
**DO:**
```
/addevent title:Quick Test when:next Monday 2-4pm
```
**SAY:** *"It understands time ranges, relative dates, and even handles past times intelligently by moving them to the next logical occurrence."*

---

### **5. The Developer Experience (1 minute)**

**SAY:** *"For the technical folks, here's what we built this with:"*

**SHOW:** Quick code glimpse or architecture diagram

**KEY POINTS:**
- *"Python + Discord.py for the bot framework"*
- *"Google Calendar API with OAuth2 via Supabase"*
- *"PostgreSQL database for user management"*
- *"Advanced date parsing with dateparser + pytz"*
- *"Production-ready with proper error handling and logging"*
- *"Deployed on Railway with auto-scaling"*

---

### **6. Real-World Impact Demo (30 seconds)**

**SAY:** *"But the real magic is in daily use. Imagine this scenario:"*

**DEMO RAPID FIRE:**
```
/addevent title:Client Call when:tomorrow 10am
/addevent title:Code Review when:Friday 1pm location:Conference Room A
/addevent title:Team Lunch when:next week Wednesday 12pm location:Downtown Cafe
```

**SAY:** *"Three events, three different time formats, all perfectly scheduled. No more switching between apps, no timezone confusion, no 'what did I mean by Friday?' - just natural conversation with your calendar."*

---

### **7. The Problem We Solved (30 seconds)**

**SAY:** *"Why does this matter? Every developer, every team lead, every project manager has this problem:"*
- *"Context switching between Discord and calendar apps"* 
- *"Timezone confusion in global teams"*
- *"Forgetting to schedule things discussed in chat"*
- *"Complex calendar UIs for simple tasks"*

**SAY:** *"We made calendar management as easy as sending a chat message."*

---

### **8. Future Vision & Closing (30 seconds)**

**SAY:** *"What's next? We're working on:"*
- *"AI-powered scheduling suggestions"*
- *"Team availability detection"*
- *"Integration with other productivity tools"*
- *"Voice command support"*

**CLOSING:** *"The Calendar Agent isn't just a bot - it's your intelligent scheduling assistant that lives where your team already collaborates. Thank you!"*

---

## 🎭 **Pro Tips for Demo Success:**

### **Before Demo:**
- [ ] Test all commands in a private channel first
- [ ] Have backup event IDs ready
- [ ] Clear your calendar view for clean screenshots
- [ ] Practice the natural flow between commands

### **During Demo:**
- [ ] Speak while typing (explain what you're doing)
- [ ] Show the Discord response AND Google Calendar
- [ ] Handle errors gracefully ("Even better, watch how it handles mistakes...")
- [ ] Keep energy high and conversational

### **Have Ready:**
- [ ] Google Calendar open in browser
- [ ] Discord server with bot permissions
- [ ] Backup demo data if live creation fails
- [ ] Architecture diagram or code snippets

### **If Something Breaks:**
- *"And this is exactly why we built comprehensive error handling!"*
- Switch to prepared screenshots/recordings
- Keep talking about the technical solution

---

## ⏱️ **Timing Breakdown (7 minutes total):**
- Opening Hook: 30s
- Natural Language Demo: 2min
- Calendar Management: 1.5min  
- Technical Deep-dive: 1min
- Real-world Impact: 30s
- Problem Statement: 30s
- Future Vision: 30s

---

## 🎯 **Key Messages to Hit:**
1. **"Natural language calendar management"**
2. **"Timezone intelligence that actually works"**  
3. **"Built for developers, by developers"**
4. **"Production-ready and scalable"**
5. **"Solves real team collaboration problems"**

Good luck with your hackathon! 🚀