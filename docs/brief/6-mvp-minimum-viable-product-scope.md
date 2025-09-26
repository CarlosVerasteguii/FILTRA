# 6. MVP (Minimum Viable Product) Scope

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
