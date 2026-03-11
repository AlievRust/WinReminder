# Project: Reminder Application

## Purpose
A mini Reminder application for Windows 10/11 to demonstrate spec-driven development with AI.

## MVP
Create, view, and manage reminders with automatic notifications and recurring support.

## Tech
Python + Tkinter + plyer + APScheduler + SQLite3.

## Features
- Add/delete reminders with title, description, date/time
- Status management: Pending, Done, Overdue, Cancelled
- Recurring reminders: hour, day, week, month
- Quick time shortcuts: +1 min, +15 min, +30 min, +1 hour
- System notifications (work when app is minimized)
- Filter reminders by status

## Repo map
- src/reminder/ — main package
- openspec/changes/change-001/ — active change
- tests/ — pytest
- data/ — SQLite database