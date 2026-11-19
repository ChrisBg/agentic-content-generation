# TODO & Roadmap — `agentic-content-generation`

> Suivi opérationnel des prochaines actions et évolutions du **Research-to-Brand Multi-LLM Engine**.
> Règle de sécurité active : voir [AGENTS.md](./AGENTS.md) (`make gate` avant tout commit/merge).

---

## Demain — Mise en route & Premier Run Réel

- [ ] **GitHub / Git**
  - [ ] Vérifier le CI vert sur la **PR #6** (`feat/v2.1-research-sources`) et la merger dans `main`
  - [ ] Passer le remote `origin` en SSH (`git remote set-url origin git@github.com:ChrisBg/agentic-content-generation.git`) et synchroniser `main` en local
  - [ ] Monter l'environnement local Python 3.11 (`uv venv --python 3.11 .venv && source .venv/bin/activate && uv pip install -e ".[dev,ui]"`)
  - [ ] Installer le hook de sécurité pre-commit local (`make install-hooks`)
- [ ] **Clés API dédiées (avec plafonds mensuels)** dans `.env`
  - [x] `ALPHAXIV_API_KEY` ajoutée
  - [ ] `GOOGLE_API_KEY` *(obligatoire — Google AI Studio + alerte budget)*
  - [ ] `ANTHROPIC_API_KEY` *(recommandé — Claude Sonnet pour LinkedIn & YouTube + hard spending limit)*
  - [ ] `OPENAI_API_KEY` *(optionnel — GPT-4.1 pour X & critique croisée + hard spending limit)*
  - [ ] `XAI_API_KEY` / `SEMANTIC_SCHOLAR_API_KEY` / `OPENALEX_EMAIL` *(optionnels)*
  - [ ] Vérifier le routage détecté : `python main.py --models`
- [ ] **Premier test end-to-end & calibrage de la voix**
  - [ ] Relire/ajuster `knowledge/voice_dna.md` et `knowledge/case_studies.yaml` (dossier local ignoré par Git)
  - [ ] Lancer un premier run test sur `examples/sample_mfa_experiment` (CLI ou Gradio `python ui_app.py` sur `http://127.0.0.1:7860`)
  - [ ] Évaluer la qualité réelle des livrables générés (`linkedin_post.txt`, `linkedin_carousel.pdf`, `x_thread.md`, `youtube_package.md`, vidéos MP4 16:9 & 9:16, `references.bib`) et noter les ajustements de prompts/voix

---

## Sprint v2.2 — alphaXiv MCP, OpenResearch & Veille Automatisée

- [ ] **Connecteur MCP officiel alphaXiv en lecture seule** (`https://api.alphaxiv.org/mcp/v1`)
  - [ ] Brancher `MCPToolset` (Streamable HTTP) sur `HybridLiteratureAgent` quand `ALPHAXIV_API_KEY` est présent
  - [ ] Restreindre via `tool_filter` aux seuls outils read-only (`discover_papers`, `get_paper_content`, `answer_pdf_queries`, `read_files_from_github_repository`, `find_researchers`) — bloquer `delete_folder` / `unfollow_researcher`
  - [ ] Ajouter les tests unitaires & sécurité correspondants
- [ ] **Pont OpenResearch (`openresearch.sh`)**
  - [ ] Installer et tester `openresearch.sh` (`orx`) sur une première expérimentation R&D locale
  - [ ] Ajouter un parseur d'exports d'expériences OpenResearch (logs/SQL/métriques) dans `src/ingestion.py`
- [ ] **Radar de veille hebdomadaire automatisé**
  - [ ] Script / agent de veille (arXiv + HF Daily Papers + OpenAlex + RSS AdTech/AI) générant chaque lundi **5 idées d'angles contrariants**
  - [ ] Flux "1 clic / graine humaine" pour transformer l'angle choisi en pack LinkedIn + X + YouTube
- [ ] **Améliorations Média & Feedback**
  - [ ] Option de narration audio TTS (ou import rapide d'une note vocale perso) sur les courtes vidéos MP4 16:9 & 9:16
  - [ ] Suivi des performances réelles des posts (impressions, commentaires qualifiés, DMs entrants) dans SQLite pour ajuster le `StrategyAgent`
- [ ] **Workflow GitHub**
  - [ ] Persister dans `AGENTS.md` la préférence : création automatique de la PR via `gh pr create` après push d'une branche

---

## Objectifs Business — Research-to-Brand Flywheel (Q4 / Trimestre 1)

- [ ] **Statut chercheur actif & dossier CIR/CII**
  - [ ] Définir les **2 sujets d'articles de recherche** (ex. détection MFA hybride frugale / évaluation d'agents AdTech sous contrainte de coût)
  - [ ] Chaîner `OpenResearch` (expériences tracées Git/SQL) → `PaperOrchestra` (manuscrit LaTeX + biblio vérifiée)
- [ ] **Réactivation des 30 000 contacts LinkedIn & lancement X / YouTube**
  - [ ] Publier un premier cycle régulier de **4 semaines** (2–3 posts LinkedIn/semaine FR & EN + 1 carrousel ou courte démo vidéo 60s/semaine sur X et YouTube Shorts)
  - [ ] Transformer 1 expérimentation R&D en **premier actif digital public** (benchmark open-source ou micro-outil AdTech/Anti-Fraude)
