# PROJECT_INTRO.md

# JobPulse

## Project Overview

JobPulse is an open-source, real-time job discovery platform built specifically for students, fresh graduates, and early-career professionals. The goal of the platform is to eliminate the need for users to manually check dozens or hundreds of career websites every day.

Instead of functioning as another job board, JobPulse acts as a continuous job monitoring engine. Users define the job roles they are interested in (for example, Software Engineer, SDE I, Backend Engineer, AI Engineer, Graduate Engineer Trainee, Associate Software Engineer), and JobPulse continuously monitors supported public job sources for newly published opportunities.

Whenever a new matching job is discovered, the user receives an instant notification through Telegram (and later email, browser push, Discord, and Slack).

The platform **does not** automate job applications. Users remain fully in control of deciding where and when to apply. JobPulse's responsibility ends at discovering, organizing, and notifying users about relevant public job opportunities.

The project is designed to be completely open source and community driven. Contributors can add support for additional companies and Applicant Tracking Systems (ATS) through a modular connector architecture without modifying the core platform.

## Primary Mission

Become the fastest, most comprehensive, open-source platform for discovering newly posted software engineering jobs for students and fresh graduates.

## Target Audience

Primary users include:

* B.Tech students
* MCA students
* Final-year engineering students
* Fresh graduates
* Early-career software engineers
* Career switchers

The initial focus is software engineering opportunities within approximately the ₹8–15 LPA range, while still supporting all salary ranges and experience levels.

## Core Principles

* Open Source
* No paid APIs required
* Modular architecture
* Community-maintained source connectors
* Fast notifications
* Privacy-first
* Human-in-the-loop applications
* Extensible plugin ecosystem
* Production-ready engineering practices

## Core Features

* Real-time job discovery
* Continuous monitoring of supported job sources
* Saved searches
* Telegram notifications
* Smart filtering
* Duplicate detection
* Job bookmarking
* Search history
* Company tracking
* Analytics dashboard
* Open plugin architecture

## High-Level Architecture

Users

↓

Web Dashboard

↓

FastAPI Backend

↓

Scheduler

↓

Source Connectors

↓

Normalization Engine

↓

Duplicate Detection

↓

Database

↓

Notification Queue

↓

Telegram / Email / Browser Push

## Development Philosophy

Every component should be independently scalable.

Every scraper should function as a plugin.

Every notification service should be replaceable.

Every feature should be documented and tested.

The platform should be designed so that thousands of contributors can add new job sources without changing the core system.

## Long-Term Vision

JobPulse aims to become the largest open-source job indexing platform, capable of monitoring thousands of public career pages, ATS providers, startup hiring platforms, and company websites while notifying users within minutes of new job postings.

Rather than replacing existing job portals, JobPulse aggregates public opportunities into one intelligent, real-time discovery platform optimized for students and early-career professionals.
