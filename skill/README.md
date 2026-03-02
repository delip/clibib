# clibib Skill for Claude Code

A [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code/skills) that lets you fetch BibTeX citations by asking naturally or using the `/clibib` slash command.

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

## Installation

**For all projects (personal):**

```bash
cp -r skill/clibib ~/.claude/skills/clibib
```

**For a specific project:**

```bash
cp -r skill/clibib .claude/skills/clibib
```

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
