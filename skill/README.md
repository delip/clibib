# clibib Agent Skill

An [Agent Skill](https://agentskills.io) that lets you fetch BibTeX citations by asking naturally or using the `/clibib` slash command. Compatible with any agent that supports the agentskills.io open standard — Claude Code, Codex CLI, Gemini CLI, OpenHands, GitHub Copilot, and [others](https://agentskills.io).

## What It Does

Fetches BibTeX entries from any of these inputs:

| Input Type | Example |
|---|---|
| DOI | `10.1038/nature12373` |
| arXiv ID | `2301.07041` |
| ISBN | `978-0-13-468599-1` |
| PMID | `23624526` |
| URL | `https://academic.oup.com/bib/article/25/1/bbad467/7512647` |
| Paper title | `"Attention Is All You Need"` |

**Note:** Title searches are less reliable than identifier-based lookups. If you only have a title, the skill instructs agents to first find the paper's publication venue, then search for the DOI at that venue — this avoids retrieving the wrong version when a paper has multiple DOIs.

## Installation

Copy the skill directory into your agent's skills location. For example:

**Claude Code (personal):**

```bash
cp -r skill/clibib ~/.claude/skills/clibib
```

**Claude Code (project-specific):**

```bash
cp -r skill/clibib .claude/skills/clibib
```

For other agents, consult their documentation on where to install agentskills.io-compatible skills.

## Usage

**Natural language** (auto-triggers from context):

```
Get me the bibtex for 10.1038/nature12373
```

```
Fetch the citation for arxiv 2301.07041 and save it to bibs/
```

```
Add the reference for "Attention Is All You Need" to my refs.bib
```

**Slash command:**

```
/clibib 10.1038/nature12373
```

```
/clibib 2301.07041
```

## Skill Structure

```
clibib/
├── SKILL.md                 # Main skill instructions
└── references/
    └── api-guide.md         # Detailed input/output/error reference
```

## License

MIT
