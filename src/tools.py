"""Custom tools for the content generation agent system."""

from typing import Any

import requests


def search_papers(topic: str, max_results: int = 5) -> dict[str, Any]:
    """Search for academic papers and research articles on a given topic.

    This tool searches for recent academic papers, research articles, and
    scientific publications related to the specified topic. It provides
    summaries and links to help build credible, research-backed content.

    Args:
        topic: The research topic or subject to search for (e.g., "machine learning interpretability")
        max_results: Maximum number of papers to return (default: 5)

    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - papers: List of paper dictionaries with title, authors, summary, link
        - error_message: Error description if status is "error"
    """
    try:
        # Use arXiv API for academic papers
        # Format: http://export.arxiv.org/api/query?search_query=all:{topic}&max_results={max_results}
        base_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{topic}",
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()

        # Parse XML response (simplified - in production use proper XML parser)
        content = response.text

        # Extract papers (basic parsing - improve with xml.etree.ElementTree in production)
        papers = []
        entries = content.split("<entry>")[1:]  # Skip header

        for entry in entries[:max_results]:
            try:
                # Extract title
                title_start = entry.find("<title>") + 7
                title_end = entry.find("</title>")
                title = entry[title_start:title_end].strip().replace("\n", " ")

                # Extract summary
                summary_start = entry.find("<summary>") + 9
                summary_end = entry.find("</summary>")
                summary = entry[summary_start:summary_end].strip().replace("\n", " ")[:300] + "..."

                # Extract link
                link_start = entry.find("<id>") + 4
                link_end = entry.find("</id>")
                link = entry[link_start:link_end].strip()

                # Extract authors
                authors = []
                author_sections = entry.split("<author>")[1:]
                for author_section in author_sections[:3]:  # First 3 authors
                    name_start = author_section.find("<name>") + 6
                    name_end = author_section.find("</name>")
                    if name_start > 5 and name_end > name_start:
                        authors.append(author_section[name_start:name_end].strip())

                papers.append(
                    {
                        "title": title,
                        "authors": ", ".join(authors) if authors else "Unknown",
                        "summary": summary,
                        "link": link,
                    }
                )
            except Exception:
                continue  # Skip malformed entries

        if not papers:
            return {"status": "error", "error_message": f"No papers found for topic: {topic}"}

        return {"status": "success", "papers": papers, "count": len(papers)}

    except requests.RequestException as e:
        return {"status": "error", "error_message": f"Failed to search papers: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def format_for_platform(content: str, platform: str, topic: str = "") -> dict[str, Any]:
    """Format content appropriately for different social media platforms.

    Adjusts content length, structure, and style based on platform requirements:
    - Blog: Long-form, structured with headings (1000-2000 words)
    - LinkedIn: Professional, medium-length with key takeaways (300-800 words)
    - Twitter: Concise thread format, engaging hooks (280 chars per tweet)

    Args:
        content: The raw content to format
        platform: Target platform ("blog", "linkedin", or "twitter")
        topic: Optional topic for context (used for hashtags, etc.)

    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - formatted_content: Platform-optimized content
        - metadata: Platform-specific metadata (hashtags, structure, etc.)
        - error_message: Error description if status is "error"
    """
    try:
        platform = platform.lower()

        if platform not in ["blog", "linkedin", "twitter"]:
            return {
                "status": "error",
                "error_message": f"Unsupported platform: {platform}. Use 'blog', 'linkedin', or 'twitter'.",
            }

        metadata = {}

        if platform == "blog":
            # Blog: Add structure with markdown
            metadata = {
                "format": "markdown",
                "target_length": "1000-2000 words",
                "structure": "Title → Introduction → Main sections with H2/H3 → Conclusion → References",
            }
            formatted = f"""# {topic if topic else "Article Title"}

{content}

## References
[Add citations here]
"""

        elif platform == "linkedin":
            # LinkedIn: Professional tone with emojis and key takeaways
            metadata = {
                "format": "plain text with limited formatting",
                "target_length": "300-800 words",
                "best_practices": "Start with hook, use line breaks, end with call-to-action",
            }

            # Add structure
            formatted = f"""🔬 {topic if topic else "Professional Insight"}

{content}

💡 Key Takeaways:
[Summarize 3-5 bullet points]

What are your thoughts? Share in the comments below! 👇

#Research #Science #Innovation
"""

        elif platform == "twitter":
            # Twitter: Break into thread
            metadata = {
                "format": "thread (multiple tweets)",
                "target_length": "280 characters per tweet",
                "best_practices": "Number tweets (1/n), use hooks, add relevant hashtags",
            }

            # Basic thread structure
            formatted = f"""🧵 Thread: {topic if topic else "Key Insights"}

1/🧵 {content[:250]}...

[Continue thread - AI will expand this into full thread]

#Research #Science
"""

        return {
            "status": "success",
            "formatted_content": formatted,
            "platform": platform,
            "metadata": metadata,
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Formatting error: {str(e)}"}


def generate_citations(sources: list[dict[str, str]], style: str = "apa") -> dict[str, Any]:
    """Generate properly formatted citations from source information.

    Creates academic-style citations from paper/article metadata to ensure
    content credibility and proper attribution.

    Args:
        sources: List of source dictionaries with keys: title, authors, link, year (optional)
        style: Citation style ("apa", "mla", or "chicago") - default is "apa"

    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - citations: List of formatted citation strings
        - inline_format: Example of how to cite inline
        - error_message: Error description if status is "error"
    """
    try:
        if not sources:
            return {"status": "error", "error_message": "No sources provided for citation"}

        style = style.lower()
        if style not in ["apa", "mla", "chicago"]:
            style = "apa"  # Default to APA

        citations = []

        for i, source in enumerate(sources, 1):
            title = source.get("title", "Untitled")
            authors = source.get("authors", "Unknown")
            link = source.get("link", "")
            year = source.get("year", "n.d.")

            if style == "apa":
                # APA: Authors (Year). Title. Retrieved from URL
                citation = f"{authors} ({year}). {title}. {link}"
            elif style == "mla":
                # MLA: Authors. "Title." Web. URL
                citation = f'{authors}. "{title}." Web. {link}'
            else:  # chicago
                # Chicago: Authors. "Title." Accessed URL
                citation = f'{authors}. "{title}." {link}'

            citations.append(f"[{i}] {citation}")

        inline_format = {"apa": "(Author, Year)", "mla": "(Author)", "chicago": "(Author Year)"}

        return {
            "status": "success",
            "citations": citations,
            "style": style,
            "inline_format": inline_format.get(style, "(Author, Year)"),
            "count": len(citations),
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Citation generation error: {str(e)}"}


def extract_key_findings(research_text: str, max_findings: int = 5) -> dict[str, Any]:
    """Extract key findings and insights from research text.

    Parses research summaries to identify the most important findings,
    conclusions, and actionable insights for content creation.

    Args:
        research_text: Raw research text to analyze
        max_findings: Maximum number of key findings to extract (default: 5)

    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - findings: List of key finding strings
        - summary: Brief overall summary
        - error_message: Error description if status is "error"
    """
    try:
        if not research_text or len(research_text.strip()) < 50:
            return {"status": "error", "error_message": "Insufficient research text provided"}

        # Simple keyword-based extraction (in production, use NLP/LLM)
        sentences = research_text.replace("\n", " ").split(". ")

        # Look for sentences with key indicator words
        indicators = [
            "found",
            "discovered",
            "showed",
            "demonstrated",
            "revealed",
            "concluded",
            "suggests",
            "indicates",
            "proves",
            "confirms",
            "important",
            "significant",
            "key",
            "main",
            "primary",
        ]

        findings = []
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in indicators):
                findings.append(sentence if sentence.endswith(".") else sentence + ".")
                if len(findings) >= max_findings:
                    break

        # If not enough findings, take first few substantial sentences
        if len(findings) < max_findings:
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 30 and sentence not in findings:
                    findings.append(sentence if sentence.endswith(".") else sentence + ".")
                    if len(findings) >= max_findings:
                        break

        summary = f"Analysis of research text identified {len(findings)} key findings and insights."

        return {
            "status": "success",
            "findings": findings[:max_findings],
            "summary": summary,
            "count": len(findings[:max_findings]),
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Key finding extraction error: {str(e)}"}


def search_industry_trends(
    field: str, region: str = "global", max_results: int = 5
) -> dict[str, Any]:
    """Search for industry trends, job market demands, and hiring patterns in AI/ML.

    Identifies what companies are looking for, hot skills in demand, and
    industry pain points that professionals can address. Useful for aligning
    content with market opportunities.

    Args:
        field: The AI/ML field to analyze (e.g., "Machine Learning", "NLP", "Computer Vision")
        region: Geographic region for job market analysis (default: "global")
        max_results: Maximum number of trends to return (default: 5)

    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - trends: List of current industry trends and demands
        - hot_skills: Technologies/frameworks in high demand
        - pain_points: Common business challenges to address
        - error_message: Error description if status is "error"
    """
    try:
        # Simulated industry trends based on common AI/ML patterns
        # In production, could integrate with job boards APIs (LinkedIn, Indeed)
        # or use Google Trends API

        skill_mapping = {
            "machine learning": ["PyTorch", "TensorFlow", "Scikit-learn", "MLflow", "Kubeflow"],
            "nlp": ["Transformers", "LangChain", "OpenAI API", "HuggingFace", "spaCy"],
            "computer vision": ["OpenCV", "YOLO", "SAM", "Detectron2", "PIL"],
            "llm": ["LangChain", "LlamaIndex", "Vector Databases", "Prompt Engineering", "RAG"],
            "mlops": ["MLflow", "Kubeflow", "Docker", "Kubernetes", "AWS SageMaker"],
        }

        field_lower = field.lower()
        hot_skills = []
        for key in skill_mapping:
            if key in field_lower:
                hot_skills.extend(skill_mapping[key][:3])

        if not hot_skills:
            hot_skills = ["Python", "PyTorch", "Cloud Platforms", "API Development"]

        trends = [
            f"Growing demand for {field} expertise in {region}",
            f"Companies seeking production-ready {field} solutions",
            "Emphasis on practical implementation over pure research",
            f"Need for professionals who can explain {field} to non-technical stakeholders",
            f"Integration of {field} with existing business systems is top priority",
        ]

        pain_points = [
            f"Difficulty finding experienced {field} professionals",
            f"Bridging gap between research papers and production code in {field}",
            f"Scaling {field} solutions from prototype to enterprise",
            f"Explaining ROI of {field} investments to executives",
            f"Maintaining and monitoring {field} systems in production",
        ]

        return {
            "status": "success",
            "trends": trends[:max_results],
            "hot_skills": list(set(hot_skills)),
            "pain_points": pain_points[:max_results],
            "region": region,
            "field": field,
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Industry trends search error: {str(e)}"}


def generate_seo_keywords(topic: str, role: str = "AI Consultant") -> dict[str, Any]:
    """Generate LinkedIn SEO keywords that recruiters search for.

    Creates role-specific keywords and technology terms that improve
    visibility in recruiter searches and LinkedIn's algorithm.

    Args:
        topic: The content topic or expertise area
        role: Target professional role (e.g., "AI Consultant", "ML Engineer")

    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - primary_keywords: Main role-based keywords
        - technical_keywords: Technology and framework terms
        - action_keywords: Skill-based action verbs
        - combined_phrases: Optimized keyword combinations
        - error_message: Error description if status is "error"
    """
    try:
        # Role-based keywords
        role_keywords = {
            "consultant": ["AI Consultant", "ML Consultant", "AI Strategy", "Technical Advisor"],
            "engineer": ["ML Engineer", "AI Engineer", "Machine Learning Engineer"],
            "specialist": ["AI Specialist", "ML Specialist", "Data Science Specialist"],
            "expert": ["AI Expert", "ML Expert", "Subject Matter Expert"],
            "architect": ["AI Architect", "ML Architect", "Solutions Architect"],
        }

        role_lower = role.lower()
        primary_keywords = [role]
        for key in role_keywords:
            if key in role_lower:
                primary_keywords.extend(role_keywords[key][:2])

        # Technical keywords based on topic
        technical_keywords = []
        topic_lower = topic.lower()

        tech_mapping = {
            "language": ["NLP", "LLM", "Transformers", "GPT", "BERT"],
            "vision": ["Computer Vision", "CNN", "Object Detection", "Image Recognition"],
            "learning": ["Deep Learning", "Neural Networks", "PyTorch", "TensorFlow"],
            "agent": ["AI Agents", "Multi-Agent Systems", "LangChain", "Autonomous Systems"],
            "data": ["Data Science", "Feature Engineering", "Model Training"],
        }

        for key in tech_mapping:
            if key in topic_lower:
                technical_keywords.extend(tech_mapping[key][:3])

        if not technical_keywords:
            technical_keywords = ["Machine Learning", "Artificial Intelligence", "Python"]

        # Action keywords (skills)
        action_keywords = [
            "AI Development",
            "Model Deployment",
            "MLOps",
            "Production ML",
            "Algorithm Design",
            "Technical Leadership",
            "AI Strategy",
        ]

        # Combined optimized phrases
        combined_phrases = [
            f"{primary_keywords[0]} | {technical_keywords[0]}",
            f"Expert in {technical_keywords[0]} and {technical_keywords[1] if len(technical_keywords) > 1 else 'ML'}",
            f"{action_keywords[0]} | {action_keywords[1]}",
        ]

        return {
            "status": "success",
            "primary_keywords": list(set(primary_keywords))[:5],
            "technical_keywords": list(set(technical_keywords))[:5],
            "action_keywords": action_keywords[:5],
            "combined_phrases": combined_phrases,
            "total_keywords": len(set(primary_keywords + technical_keywords + action_keywords)),
        }

    except Exception as e:
        return {"status": "error", "error_message": f"SEO keyword generation error: {str(e)}"}


def create_engagement_hooks(topic: str, goal: str = "opportunities") -> dict[str, Any]:
    """Create engagement hooks that invite professional connections and opportunities.

    Generates calls-to-action, questions, and portfolio mentions that
    encourage recruiters and potential clients to connect.

    Args:
        topic: The content topic
        goal: Content goal ("opportunities", "discussion", "credibility", "visibility")

    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - opening_hooks: Attention-grabbing opening lines
        - closing_ctas: Strong calls-to-action
        - discussion_questions: Questions that spark engagement
        - portfolio_prompts: Ways to mention your work
        - error_message: Error description if status is "error"
    """
    try:
        goal = goal.lower()

        # Opening hooks based on goal
        opening_hooks = {
            "opportunities": [
                f"Working with companies on {topic}? Here's what I've learned...",
                f"After implementing {topic} for multiple clients, one thing is clear:",
                f"Most {topic} projects fail because of this one mistake:",
            ],
            "discussion": [
                f"Hot take on {topic}:",
                f"Here's what nobody tells you about {topic}:",
                f"The {topic} landscape just shifted. Here's why it matters:",
            ],
            "credibility": [
                f"Deep dive into {topic} based on hands-on experience:",
                f"Technical breakdown of {topic} that actually works in production:",
                f"What I learned implementing {topic} at scale:",
            ],
            "visibility": [
                f"🔥 {topic} is evolving faster than ever. Here's what you need to know:",
                f"Everyone's talking about {topic}, but here's what they're missing:",
                f"3 things about {topic} that changed how I work:",
            ],
        }

        # Closing CTAs based on goal
        closing_ctas = {
            "opportunities": [
                "Looking to implement this in your organization? Let's connect and discuss your needs.",
                "Need help with your {topic} project? DM me to explore collaboration.",
                "Building something similar? I'd love to hear about your approach. Drop a comment or message me.",
            ],
            "discussion": [
                "What's your take on this? Agree or disagree? Let's discuss in the comments!",
                "Have you encountered this in your work? Share your experience below.",
                "Curious how this applies to your use case? Let's chat!",
            ],
            "credibility": [
                "Want to dive deeper into the technical details? Connect with me.",
                "Questions about the implementation? Happy to share insights.",
                "Follow for more technical deep-dives on {topic}.",
            ],
            "visibility": [
                "🔔 Follow for more insights on {topic} and AI/ML trends.",
                "👉 Repost if you found this valuable. Tag someone who needs to see this.",
                "💬 What would you add to this list? Comment below!",
            ],
        }

        # Discussion questions
        discussion_questions = [
            f"What's been your biggest challenge with {topic}?",
            f"Are you seeing similar trends with {topic} in your industry?",
            f"Which aspect of {topic} should I cover next?",
            f"What's your hot take on the future of {topic}?",
            f"Have you tried implementing {topic}? What were your results?",
        ]

        # Portfolio prompts
        portfolio_prompts = [
            f"In my recent project on {topic}, I discovered...",
            f"While building a {topic} solution, here's what worked:",
            f"My open-source work on {topic} taught me...",
            f"Check out my GitHub for {topic} implementations that...",
            f"Drawing from my Kaggle competition on {topic}...",
        ]

        return {
            "status": "success",
            "opening_hooks": opening_hooks.get(goal, opening_hooks["credibility"])[:3],
            "closing_ctas": [
                cta.replace("{topic}", topic)
                for cta in closing_ctas.get(goal, closing_ctas["opportunities"])[:3]
            ],
            "discussion_questions": discussion_questions[:3],
            "portfolio_prompts": portfolio_prompts[:3],
            "goal": goal,
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Engagement hook creation error: {str(e)}"}


def analyze_content_for_opportunities(
    content: str, target_role: str = "AI Consultant"
) -> dict[str, Any]:
    """Analyze content for recruiter appeal and opportunity generation potential.

    Scores content based on factors that attract professional opportunities:
    SEO keywords, engagement hooks, portfolio mentions, and business value.

    Args:
        content: The content to analyze
        target_role: Target professional role for scoring

    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - opportunity_score: Overall score (0-100)
        - seo_score: SEO keyword presence (0-100)
        - engagement_score: Engagement hook effectiveness (0-100)
        - value_score: Business value communication (0-100)
        - suggestions: List of improvement suggestions
        - error_message: Error description if status is "error"
    """
    try:
        if not content or len(content) < 100:
            return {
                "status": "error",
                "error_message": "Content too short for meaningful analysis (minimum 100 characters)",
            }

        content_lower = content.lower()

        # SEO keyword scoring
        seo_keywords = [
            "ai",
            "machine learning",
            "ml",
            "deep learning",
            "neural network",
            "python",
            "tensorflow",
            "pytorch",
            "consulting",
            "engineer",
            "architect",
            "specialist",
            "expert",
        ]
        seo_hits = sum(1 for keyword in seo_keywords if keyword in content_lower)
        seo_score = min(100, (seo_hits / len(seo_keywords)) * 200)

        # Engagement hooks scoring
        engagement_indicators = [
            "?",
            "let's",
            "connect",
            "dm",
            "message",
            "discuss",
            "share",
            "comment",
            "what's your",
            "have you",
            "follow",
        ]
        engagement_hits = sum(
            1 for indicator in engagement_indicators if indicator in content_lower
        )
        engagement_score = min(100, (engagement_hits / 5) * 100)

        # Business value scoring
        value_indicators = [
            "production",
            "scale",
            "roi",
            "business",
            "solution",
            "impact",
            "results",
            "improve",
            "optimize",
            "problem",
            "challenge",
        ]
        value_hits = sum(1 for indicator in value_indicators if indicator in content_lower)
        value_score = min(100, (value_hits / 5) * 100)

        # Portfolio mention detection
        portfolio_indicators = ["project", "github", "kaggle", "built", "developed", "implemented"]
        portfolio_mentions = sum(
            1 for indicator in portfolio_indicators if indicator in content_lower
        )
        portfolio_score = min(100, (portfolio_mentions / 3) * 100)

        # Calculate overall opportunity score
        opportunity_score = int(
            seo_score * 0.3 + engagement_score * 0.3 + value_score * 0.25 + portfolio_score * 0.15
        )

        # Generate suggestions
        suggestions = []
        if seo_score < 50:
            suggestions.append(
                f"Add more {target_role} keywords and technical terms for better visibility"
            )
        if engagement_score < 50:
            suggestions.append(
                "Include stronger calls-to-action and questions to invite connections"
            )
        if value_score < 50:
            suggestions.append("Emphasize business value and practical impact over pure theory")
        if portfolio_mentions == 0:
            suggestions.append(
                "Mention your projects or portfolio to demonstrate hands-on expertise"
            )
        if len(content) < 300:
            suggestions.append(
                "Consider expanding content for better engagement (aim for 300+ words)"
            )

        return {
            "status": "success",
            "opportunity_score": opportunity_score,
            "seo_score": int(seo_score),
            "engagement_score": int(engagement_score),
            "value_score": int(value_score),
            "portfolio_score": int(portfolio_score),
            "suggestions": suggestions
            if suggestions
            else ["Content looks great for opportunities!"],
            "grade": "Excellent"
            if opportunity_score >= 80
            else "Good"
            if opportunity_score >= 60
            else "Needs Improvement",
        }

    except Exception as e:
        return {"status": "error", "error_message": f"Content analysis error: {str(e)}"}
