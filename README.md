# Based LLM Preferences

This repository contains my opinionated LLM preferences. It's based on stuff I've found on
reddit and just general stuff I've encountered while working with Claude Code. You can see some
of my sources in `sources.md`. A lot of my work is on high-performance computing clusters, so
you'll see some SLURM rules in here too. The entry point is `main.md`, which the LLM should
read.

A brief (and not necessarily exhaustive) list of stuff in this repo is:
- Hooks for linting (e.g. `ruff`/`ty` for Python)
- Language guidelines, some of which are mechanically checked in markdown files, such as
no em-dashes, no fancy jargon etc.
- Some structure in how the model should reply (actionable items for the user)
- A setup file so that your agent can easily reproduce the rules from this repo

This has been written for myself, and it's very opinionated and tailored to how I like to
work, so I don't expect anyone to copy everything. However, maybe you find a rule or two that
you like. Also, this repo has obviously been produced in its entirety by coding agents, 
except this README.


This is by no means done, and so I'll keep pushing any updates I find useful. 
