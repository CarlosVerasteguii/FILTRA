# Source Tree
```
project-root/
├── config/
│   ├── alias_map.yaml
│   ├── rubric.yaml
│   └── settings.example.env
├── docs/
│   ├── architecture.md
│   └── prd.md
├── filtra/
│   ├── __init__.py
│   ├── cli.py
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   └── warmup.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── pdf_loader.py
│   ├── ner/
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   └── normalization.py
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── rubric.py
│   │   └── scorecard.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── prompts.py
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── composer.py
│   │   └── renderer.py
│   └── utils/
│       ├── __init__.py
│       ├── config_loader.py
│       ├── logging.py
│       └── language.py          # Locale detection & spanish defaults
├── samples/
│   ├── inputs/
│   │   ├── resume_windows_sample.txt
│   │   └── jd_windows_sample.txt
│   └── expected/
│       └── sample_report.json
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_pdf_loader.py
│   ├── test_ner_pipeline.py
│   ├── test_rubric.py
│   ├── test_llm_client.py
│   └── reporting/
│       ├── __init__.py
│       └── test_entities_section.py
├── scripts/
│   └── warmup_demo.ps1
├── requirements.in
├── requirements.txt
├── pyproject.toml
├── ruff.toml
├── README.md
└── .env.example
```



