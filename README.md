# CopyForge AI
## DecodeLabs Generative AI Project 2 — Automated Copywriting & Tone Transformer

CopyForge AI is a generative-AI based marketing copywriting application that transforms raw product descriptions into platform-specific marketing content.

The application supports LinkedIn, Instagram, and Email content generation with configurable tone, Temperature, and Top-P parameters.

---

## Project Objective

The objective of this project is to automatically transform a raw product description into professional marketing copy tailored to different platforms.

The application demonstrates:

- Dynamic prompt template compilation
- Generative AI text generation
- Temperature control
- Top-P control
- Platform-specific copy generation
- Tone transformation
- Character-limit validation
- Structured JSON output
- Batch generation
- Offline mock mode for testing and demonstration

---

## Features

### Supported Platforms

- LinkedIn
- Instagram
- Email

### Supported Tones

- Professional
- Creative
- Friendly
- Luxury
- Persuasive
- Minimal

### Generation Parameters

**Temperature**

Controls the creativity and variation of generated content.

**Top-P**

Controls the range of tokens considered during generation.

Both parameters can be adjusted directly from the web interface.

---

## Generated Output

Depending on the selected platform, the application generates:

- Subject
- Headline
- Body
- Call To Action
- Hashtags
- Character Count
- Compliance Notes

---

## Brand Safety

The prompt system instructs the model to use only information contained in the supplied product description.

The application avoids unsupported:

- Prices
- Awards
- Certifications
- Statistics
- Testimonials
- Guarantees
- Clinical claims
- Product performance claims

Final output is also validated against platform character limits.

---

## Technology Stack

### Backend

- Python
- Pydantic
- Google Gemini API
- python-dotenv
- asyncio

### Frontend

- HTML
- CSS
- JavaScript

### Testing

- Pytest

---

## Project Structure

```text
DecodeLabs-Generative-AI-Project-2/
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── prompts.py
│   ├── validators.py
│   ├── retry.py
│   ├── generator.py
│   ├── batch.py
│   ├── cli.py
│   ├── web_app.py
│   │
│   └── frontend/
│       ├── index.html
│       ├── style.css
│       └── app.js
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md