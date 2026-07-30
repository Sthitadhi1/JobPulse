# UI_UX_PART2.md

# Part 2 — User Screens & Detailed Page Specifications

Project: JobPulse

Version: 1.0

---

# 31. Landing Page

## Purpose

Introduce JobPulse and convert visitors into registered users.

---

## Navigation Bar

Logo

Features

Supported Sources

Documentation

GitHub

Login

Register

Dark Mode Toggle

---

## Hero Section

Headline

"Never Miss Another Job Opportunity"

Subheading

Monitor thousands of public job sources in real time and receive instant notifications when new jobs matching your interests are published.

Primary CTA

Get Started

Secondary CTA

View GitHub Repository

---

## Features Section

Cards

* Real-time Monitoring
* Telegram Notifications
* Open Source
* Saved Searches
* Company Tracking
* Smart Filters

---

## Supported Sources

Display supported connector categories:

* ATS Platforms
* Company Career Pages
* Startup Boards
* Remote Job Boards

Show counts (e.g., "100+ Companies", "10+ ATS Platforms") rather than hardcoding logos.

---

## Footer

Documentation

Privacy Policy

Terms

Contributing

GitHub

License

---

# 32. Registration Page

Fields

* Name
* Email
* Password
* Confirm Password

Validation

* Required fields
* Email format
* Password strength
* Password confirmation

Actions

* Register
* Sign in
* Continue as Guest (optional)

---

# 33. Login Page

Fields

Email

Password

Remember Me

Actions

Login

Forgot Password

Register

Future

Google Login

GitHub Login

---

# 34. Dashboard

Purpose

Provide an overview of everything important.

---

Top Statistics

* New Jobs Today
* Saved Searches
* Notifications Sent
* Companies Tracked
* Bookmarked Jobs
* Applications Tracked

---

Recent Activity

Recently discovered jobs

Recent notifications

Recently bookmarked jobs

Recent searches

---

Quick Actions

Create Search

Browse Jobs

Connect Telegram

Import Preferences (future)

---

# 35. Search Page

Top Search Bar

Supports

* Keywords
* Boolean operators
* Exact phrases

---

Advanced Filters

Location

Experience

Employment Type

Remote

Salary

Company Include

Company Exclude

Source

Posted Within

Sort

---

Buttons

Search

Save Search

Reset

---

Results

Infinite scrolling

Grid/List toggle

Result count

Search execution time

---

# 36. Job Results

Each card displays:

Company Logo

Company Name

Job Title

Location

Remote Status

Experience

Employment Type

Posting Time

Source

Apply Button

Bookmark Button

Share Button

Hide Company

Ignore Job

---

Quick Preview

Hover or tap reveals:

Short description

Required skills

Salary (if available)

---

# 37. Job Details Page

Header

Company

Role

Apply Button

Bookmark

Share

---

Sections

Overview

Responsibilities

Qualifications

Preferred Skills

Benefits (if available)

Location

Employment Type

Experience

Posting Date

Source

Apply URL

---

Sidebar

Related Jobs

Other Jobs from Company

Recently Viewed

---

# 38. Saved Searches

Table Columns

Search Name

Keywords

Locations

Status

Last Match

Notification Enabled

Created Date

Actions

Edit

Run

Disable

Delete

Duplicate

---

# 39. Bookmarks

Folders

Interested

Applied

Interview

Offer

Rejected

Archive

---

Actions

Move

Delete

Notes

Export (future)

---

# 40. Notifications

Sections

Unread

Read

Archived

---

Notification Card

Company

Job

Time

Open Job

Mark Read

Delete

---

Bulk Actions

Mark All Read

Delete Selected

Filter by Channel

---

# 41. Companies

Searchable list of companies.

Each company page shows:

Logo

Website

Industry

Company Type

Current Openings

Recent Hiring Activity

Supported Connector

Hiring Trend (future)

---

# 42. Analytics Dashboard

Cards

Jobs Today

Jobs This Week

Most Active Companies

Most Active Locations

Top Job Titles

Most Popular Searches

---

Charts (future)

Hiring trend

Location distribution

Company distribution

Source distribution

---

# 43. Profile Page

Information

Name

Email

Avatar

Role

Joined Date

Telegram Status

Statistics

Saved Searches

Bookmarks

Applications

Notifications

---

Actions

Edit Profile

Change Password

Delete Account

---

# 44. Settings

General

Theme

Language

Timezone

---

Notifications

Telegram

Email

Browser Push (future)

Discord (future)

Slack (future)

---

Privacy

Export Data

Delete Account

Session Management

---

# 45. Telegram Integration

Status Card

Connected

Not Connected

---

Actions

Connect

Reconnect

Disconnect

Send Test Message

---

Connection Flow

Generate secure link

↓

User opens Telegram

↓

Confirms

↓

Bot verifies

↓

Dashboard updates

---

# 46. Application Tracker

Purpose

Track application progress manually.

Columns

Company

Role

Applied Date

Current Status

Notes

Next Action

Statuses

Interested

Applied

Online Assessment

Interview

Offer

Rejected

Accepted

---

# 47. Recent Jobs Feed

Dedicated page showing:

Newest jobs first

Filter by

Time

Source

Location

Role

Infinite scrolling

Auto-refresh indicator

---

# 48. Search History

Displays

Recent searches

Filters used

Timestamp

Result count

Actions

Run Again

Save Search

Delete

---

# 49. Help & Documentation

Searchable knowledge base

Sections

Getting Started

Telegram Setup

Saved Searches

Supported Sources

Troubleshooting

Contributing

---

# 50. Global UX Requirements

Every page should support:

* Responsive layouts
* Keyboard navigation
* Loading skeletons
* Empty states
* Error handling
* Optimistic UI where appropriate
* Accessible labels
* Consistent spacing
* Persistent navigation
* Fast transitions

Users should be able to move between the most common workflows—searching jobs, saving searches, bookmarking, and managing notifications—with no more than three clicks from the dashboard.

The interface should always prioritize helping users discover and act on newly posted opportunities as quickly and efficiently as possible.
