
# Project Brief: FILTRA

**Date:** September 25, 2025
**Project Lead:** You
**BMad Facilitator:** Mary (Business Analyst)

## 1. Executive Summary

FILTRA is a Python script designed to demonstrate advanced AI capabilities. It automates the initial analysis of resumes against a job description, utilizing a Large Language Model for qualitative reasoning and a HuggingFace model for structured data extraction. Its objective is to serve as a functional prototype for the job interview at RRHH Ingenia, directly addressing the technical requirements of the IA Engineer vacancy.

## 2. Problem Statement

Recruitment teams, like the one at RRHH Ingenia, spend a disproportionate amount of time manually screening resumes. This process is slow, prone to human error, can introduce unconscious bias, and delays the identification of the most promising candidates. Existing solutions are often costly or lack the flexibility to analyze technical compatibility with expert-level depth.

## 3. Proposed Solution

FILTRA is a command-line tool built in Python that integrates two types of AI: a Large Language Model (via OpenRouter) for qualitative analysis and compatibility scoring, and a locally-run HuggingFace NER model for structured data extraction (skills, companies). It processes a resume and a job description to generate a concise report, empowering recruiters to make faster, data-driven decisions.

## 4. Target Users

The primary user is the recruitment and talent acquisition team at RRHH Ingenia. They need a fast, efficient way to screen technical candidates for specialized roles like the 'IA Engineer' position.

## 5. Goals & Success Metrics

### Business Objectives
* Develop a functional prototype in under 24 hours.
* Create a practical case study to present during the job interview.

### User Success Metrics
* The script successfully processes a PDF resume and a text-based job description.
* The generated report is clear, useful, and contains both the LLM's analysis and the entities extracted by the HuggingFace model.

### Key Performance Indicators (KPIs)
* The project's success will be measured by its ability to effectively demonstrate mastery of the concepts required in the interview: AI API integration, local HuggingFace model usage, data handling, and functional Python code.

## 6. MVP (Minimum Viable Product) Scope

### Core Features (In Scope)
* A function that reads a `.pdf` file and returns plain text.
* A function that uses a local HuggingFace model to identify and extract entities (skills, companies, etc.).
* A function that sends the processed text and entities to an LLM (via OpenRouter) to get a summary and compatibility score.
* The main script that orchestrates the workflow and prints a formatted, easy-to-read result to the terminal.

### Out of Scope for MVP
* Any graphical user interface (GUI or web).
* Batch processing of multiple resumes at once.
* A database for storing results.
* Support for file formats other than PDF (e.g., `.docx`, `.txt`).
