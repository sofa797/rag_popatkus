# RAG System for "Popatkus" Regulation Analysis

This project is the implementation of a term paper focused on automating information retrieval and Q&A for the "Popatkus" regulation (the university policy on student assessment and grading).

## Product Overview
The system is built upon the Retrieval-Augmented Generation (RAG) architecture. It allows users to ask questions in natural language and receive precise answers supported by references to specific sections of the regulation.

## Key Features
* **Accuracy:** Utilizes domain-specific embeddings optimized for legal and regulatory documentation.
* **Context Awareness:** The system respects document structure during retrieval, significantly reducing model hallucinations.
* **Interface:** A user-friendly web interface powered by Gradio for seamless testing and interaction.

## Getting Started

### Requirements
* Docker and Docker Compose installed on your system.

### Installation
1. clone repository
   ```bash
   git clone https://github.com/sofa797/rag_popatkus.git
   cd rag_popatkus
   ```
2. create .env
   ```bash
   cp .env.example .env
   ```
3. run app
   ```bash
   docker-compose up -d
   ```
4. open in browser
   ```bash
   http://localhost:7860
   ```
