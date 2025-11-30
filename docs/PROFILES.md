# User Profile Configuration Guide

This guide explains how to configure your professional profile for personalized content generation.

## Table of Contents

- [Quick Start](#quick-start)
- [Profile Fields](#profile-fields)
- [Validation](#validation)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Initialize Your Profile

```bash
python main.py --init-profile
```

This creates a default profile at `~/.agentic-content-generation/profile.yaml`.

### 2. Edit Your Profile

Open the file in your editor:

```bash
# macOS/Linux
nano ~/.agentic-content-generation/profile.yaml

# Or use your preferred editor
code ~/.agentic-content-generation/profile.yaml
vim ~/.agentic-content-generation/profile.yaml
```

### 3. Validate Your Profile

```bash
python main.py --validate-profile
```

Fix any errors or warnings before generating content.

## Profile Fields

### Professional Identity

#### `name` (string, required)
**Your full professional name** used for attribution and session tracking.

```yaml
name: Jane Smith
```

**Validation:**
- ⚠️ Warning if set to default "Your Name"
- ⚠️ Warning if empty

#### `target_role` (string, required)
**Your target professional role** - what you want to be known for.

```yaml
target_role: AI Consultant
```

**Common roles:**
- AI Consultant
- ML Engineer
- Data Scientist
- AI Architect
- Research Scientist
- MLOps Engineer
- AI Product Manager

#### `expertise_areas` (list, required)
**Your areas of expertise** (3-5 recommended). These will be emphasized in content generation.

```yaml
expertise_areas:
  - Machine Learning
  - Natural Language Processing
  - Computer Vision
  - MLOps
  - AI Strategy
```

**Validation:**
- ❌ Error if empty
- ⚠️ Warning if using default values

---

### Professional Goals

#### `content_goals` (list, required)
**What you want to achieve with your content.**

```yaml
content_goals:
  - opportunities  # Attract freelance/consulting/job opportunities
  - credibility    # Build professional credibility
  - visibility     # Increase visibility in the field
```

**Valid options:**
- `opportunities` - Attract professional opportunities
- `credibility` - Build scientific credibility
- `visibility` - Increase industry visibility
- `thought-leadership` - Establish thought leadership
- `networking` - Expand professional network

**Validation:**
- ⚠️ Warning for unrecognized goals

---

### Geographic & Market

#### `region` (string)
**Your primary region** - affects industry trends and SEO.

```yaml
region: Europe
```

**Examples:** `Europe`, `US`, `Asia`, `Global`, `UK`, `Canada`, `Australia`

#### `languages` (list)
**Languages you create content in.**

```yaml
languages:
  - English
  - French
```

#### `target_industries` (list)
**Target industries for your content.**

```yaml
target_industries:
  - Technology
  - Finance
  - Healthcare
  - Consulting
  - E-commerce
```

**Validation:**
- ⚠️ Warning if empty

---

### Portfolio & Online Presence

#### `github_username` (string, optional)
**Your GitHub username** (not the full URL, just username).

```yaml
github_username: janesmit
h
```

**Validation:**
- ⚠️ Warning if contains slashes (should be username only, not URL)

#### `linkedin_url` (string, optional)
**Your LinkedIn profile URL** (full URL).

```yaml
linkedin_url: https://www.linkedin.com/in/janesmith
```

**Validation:**
- ❌ Error if not a valid URL (must start with http:// or https://)

#### `portfolio_url` (string, optional)
**Your personal portfolio/website URL** (full URL).

```yaml
portfolio_url: https://janesmith.com
```

**Validation:**
- ❌ Error if not a valid URL

#### `kaggle_username` (string, optional)
**Your Kaggle username** (not the full URL, just username).

```yaml
kaggle_username: janesmith
```

**Validation:**
- ⚠️ Warning if contains slashes

---

### Notable Projects

#### `notable_projects` (list of dicts)
**Key projects to mention in your content** (3-5 recommended).

```yaml
notable_projects:
  - name: AI-Powered Recommendation Engine
    description: Built a scalable recommendation system serving 1M+ users
    technologies: PyTorch, FastAPI, Redis, Kubernetes
    url: https://github.com/janesmith/recommendation-engine

  - name: Medical Image Classification System
    description: Deep learning model for detecting pneumonia from X-rays (95% accuracy)
    technologies: TensorFlow, OpenCV, Docker, AWS SageMaker
    url: https://github.com/janesmith/medical-imaging
```

**Required keys for each project:**
- `name` - Project name
- `description` - Brief description
- `technologies` - Technologies used
- `url` - Project URL (GitHub, live demo, etc.)

**Validation:**
- ⚠️ Warning if missing keys
- ⚠️ Warning if using default placeholder project

---

### Technical Skills

#### `primary_skills` (list)
**Your primary technical skills** (top 5-10). Used for SEO keywords and skills matching.

```yaml
primary_skills:
  - Python
  - PyTorch
  - TensorFlow
  - Scikit-learn
  - Transformers
  - FastAPI
  - Docker
  - Kubernetes
  - AWS
  - MLflow
```

**Validation:**
- ⚠️ Warning if empty

---

### Content Preferences

#### `content_tone` (string, required)
**Tone for your content.**

```yaml
content_tone: professional-conversational
```

**Valid options:**
- `professional-formal` - Formal business language
- `professional-conversational` - Approachable but professional (recommended)
- `technical` - Technical, detailed language
- `casual` - Relaxed, informal tone

**Validation:**
- ❌ Error if not a valid option

#### `use_emojis` (boolean)
**Whether to use emojis in LinkedIn posts.**

```yaml
use_emojis: true
```

#### `posting_frequency` (string)
**Your target posting frequency.**

```yaml
posting_frequency: 2-3x per week
```

**Valid options:**
- `daily`
- `2-3x per week` (recommended)
- `weekly`
- `biweekly`
- `monthly`

**Validation:**
- ⚠️ Warning for unrecognized frequency

---

### SEO & Positioning

#### `unique_value_proposition` (string, required)
**Your unique value proposition** (1-2 sentences). What makes you different? What specific problem do you solve?

```yaml
unique_value_proposition: I help companies bridge the gap between AI research and production by building scalable, reliable ML systems that deliver measurable business value.
```

**Validation:**
- ⚠️ Warning if using default value

#### `key_differentiators` (list)
**Key differentiators** (3-5 bullet points). What sets you apart?

```yaml
key_differentiators:
  - End-to-end ML pipeline design and implementation
  - 5+ years scaling ML systems in production
  - Strong focus on business ROI and practical impact
  - Research-backed approach with real-world pragmatism
  - Expert in both cloud-native and edge ML deployment
```

---

## Validation

The profile validation system checks for:

### Errors (❌)
**Must be fixed before generating content:**
- Empty required fields (expertise_areas)
- Invalid URLs (linkedin_url, portfolio_url)
- Invalid enum values (content_tone, content_goals, posting_frequency)

### Warnings (⚠️)
**Recommended to fix but not blocking:**
- Default placeholder values
- Incomplete optional fields
- Username format issues
- Empty recommended lists

### Running Validation

```bash
# Check your profile
python main.py --validate-profile

# Example output:
# 🔍 Validating profile...
#
# 📋 Profile Validation Warnings:
#    ⚠️  Name is not set. Please update 'name' field in profile.yaml
#    ⚠️  Using default expertise areas. Update 'expertise_areas' with your specific skills
#    ⚠️  Using default value proposition. Update 'unique_value_proposition' with your unique offering
#
# ✅ Profile validation complete!
```

---

## Examples

### Example 1: AI Consultant

```yaml
name: Sarah Johnson
target_role: AI Consultant
expertise_areas:
  - Machine Learning Strategy
  - MLOps Architecture
  - Business AI Integration
  - Team Leadership
content_goals:
  - opportunities
  - thought-leadership
region: US
linkedin_url: https://linkedin.com/in/sarahjohnson
github_username: sarahj
primary_skills:
  - Python
  - TensorFlow
  - AWS
  - Docker
  - Kubernetes
content_tone: professional-conversational
unique_value_proposition: I help Fortune 500 companies transform AI prototypes into production systems that drive $10M+ in annual value.
```

### Example 2: ML Research Engineer

```yaml
name: Alex Chen
target_role: ML Research Engineer
expertise_areas:
  - Deep Learning
  - Computer Vision
  - Reinforcement Learning
content_goals:
  - credibility
  - visibility
region: Global
github_username: alexchen
kaggle_username: alexchen
primary_skills:
  - PyTorch
  - JAX
  - CUDA
  - Python
  - C++
content_tone: technical
use_emojis: false
unique_value_proposition: Bridging cutting-edge ML research and real-world applications with published papers and production deployments.
```

### Example 3: AI Product Manager

```yaml
name: Maria Garcia
target_role: AI Product Manager
expertise_areas:
  - AI Product Strategy
  - ML Product Development
  - Cross-functional Leadership
content_goals:
  - opportunities
  - networking
region: Europe
linkedin_url: https://linkedin.com/in/mariagarcia
portfolio_url: https://mariagarcia.io
primary_skills:
  - Product Management
  - ML Systems
  - Stakeholder Management
  - Agile/Scrum
  - Data Strategy
content_tone: professional-conversational
posting_frequency: weekly
unique_value_proposition: I turn AI research into customer-loved products that drive revenue growth and user engagement.
```

---

## Best Practices

### 1. Be Specific with Expertise
❌ `expertise_areas: [AI, ML]`
✅ `expertise_areas: [Natural Language Processing, LLM Fine-tuning, Prompt Engineering]`

### 2. Quantify Your Value Proposition
❌ `unique_value_proposition: I help companies with AI`
✅ `unique_value_proposition: I help Series A startups build ML systems that scale from 1K to 1M users without technical debt`

### 3. Showcase Real Projects
Include actual projects with:
- Specific metrics (95% accuracy, 1M+ users, 10x faster)
- Technologies used
- Business impact
- Live URLs when possible

### 4. Update Regularly
- Review your profile every 3-6 months
- Add new projects as you complete them
- Update skills as you learn new technologies
- Refine your value proposition based on market feedback

### 5. Match Content Goals to Current Phase
- **Job seeking:** Focus on `opportunities`, `visibility`
- **Established:** Focus on `thought-leadership`, `credibility`
- **Building agency:** Focus on `opportunities`, `networking`

---

## Troubleshooting

### "Profile validation failed with X error(s)"

Check the error messages and fix:
- Invalid URLs: Ensure they start with `http://` or `https://`
- Invalid enums: Use exact values from valid options
- Empty required fields: Add at least one item to lists

### "Using default profile (no custom profile found)"

Solution:
```bash
python main.py --init-profile
# Then edit ~/.agentic-content-generation/profile.yaml
```

### Profile changes not reflected

Solution:
1. Check file location: `~/.agentic-content-generation/profile.yaml`
2. Validate syntax: `python main.py --validate-profile`
3. Restart any running ADK web servers

### Too many warnings

Don't worry! Warnings are suggestions, not blockers. Focus on:
1. Adding your real name
2. Customizing expertise areas
3. Adding portfolio links
4. Writing your unique value proposition

---

## Advanced Topics

### Profile in Code

Access profile programmatically:

```python
from src.profile import load_user_profile

profile = load_user_profile()
print(f"Generating content for: {profile.name}")
print(f"Expertise: {', '.join(profile.expertise_areas)}")
print(f"Goals: {', '.join(profile.content_goals)}")
```

### Custom Profile Paths

Load from a custom location:

```python
from pathlib import Path
from src.profile import load_profile_from_yaml

custom_path = Path("./my_profile.yaml")
profile = load_profile_from_yaml(custom_path)
```

### Profile Templates

Create templates for different personas:
- `~/.agentic-content-generation/consultant.yaml`
- `~/.agentic-content-generation/researcher.yaml`
- `~/.agentic-content-generation/engineer.yaml`

Copy the active one to `profile.yaml` as needed.

---

## See Also

- [SESSIONS.md](SESSIONS.md) - Session management guide
- [profile.example.yaml](../profile.example.yaml) - Complete example profile
- [README.md](../README.md) - Main documentation
