# 🧠 FlashMind Pro — Executive AI Learning Hub & Knowledge Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gemini API](https://img.shields.io/badge/Google%20Gemini-3.8--flash-orange)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**FlashMind Pro** is a modern, security-focused active recall platform powered by **Streamlit**, **Python**, and the **Google Gemini API** (`google-genai` SDK). It converts raw lecture text, technical documentation, or custom study topics into interactive flashcard decks, browser-based audio lessons, and custom-tailored study guides.

---

## 📋 Table of Contents
- [Key Features](#-key-features)
- [Architecture & Workflow](#-architecture--workflow)
- [Tech Stack](#-tech-stack)
- [Repository Structure](#-repository-structure)
- [Installation & Setup](#-installation--setup)
- [Application Workspace Overview](#-application-workspace-overview)
- [Security & Privacy Features](#-security--privacy-features)
- [Deployment Guide](#-deployment-guide)
- [Troubleshooting & Common Issues](#-troubleshooting--common-issues)
- [License & Acknowledgments](#-license--acknowledgments)

---

## ✨ Key Features

### 🎴 1. AI Active Recall Engine
- Uses `gemini-3.8-flash` paired with strict `pydantic` JSON schemas to generate educational flashcards on demand.
- Supports multi-perspective generation modes: *Executive Summary*, *Technical Deep-Dive*, *Conceptual Fundamentals*, and *Interview Preparation*.

### 📑 2. Smart Study Note Synthesizer
- Generates high-yield Markdown cheat sheets tailored to explicit learning goals (e.g., 5-minute overviews, full subject mastery guides, or high-yield interview Q&A sections).
- Exportable as standalone `.md` files for note-taking apps like Obsidian or Notion.

### 🔊 3. Native Text-to-Speech (Audio Mode)
- Integrates browser-native Web Speech API components allowing users to listen to flashcard questions and answers hands-free.

### 📊 4. Real-Time Session Analytics
- Tracks card mastery states (*Mastered*, *Needs Review*, *Pending*) and lets users tag custom difficulty levels (*Easy*, *Medium*, *Hard*).

### ✏️ 5. Card Annotations
- Dedicated per-card text area for writing personal memory hooks, supplementary formulas, or code snippets.

### 💾 6. Multi-Format Data Export
- Download active decks, user notes, and mastery progress in standard `.csv`, `.json`, or `.md` formats.

---

## 🏗️ Architecture & Workflow

```text
[ User Input / File Upload (.txt) ]
               │
               ▼
   [ Streamlit Control Panel ] ──(Input Sanitization & Length Check)
               │
               ▼
  [ Google Gemini API Engine ]
   ├── Model: gemini-3.8-flash (Fallback: gemini-3.5-flash-lite)
   └── Config: JSON Schema Enforcement via Pydantic
               │
               ▼
  [ Streamlit Session State ] ──(Maintains Active Decks, Mastery, Notes)
               │
               ├──► Tab 1: Interactive Flashcard Canvas & TTS Engine
               ├──► Tab 2: Smart Study Note Synthesizer
               ├──► Tab 3: Card Annotations & Personal Notes
               ├──► Tab 4: Mastery Metrics Dashboard
               └──► Tab 5: Multi-Format Data Exporter (.CSV / .JSON / .MD)