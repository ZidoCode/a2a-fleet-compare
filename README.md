# a2a-fleet-compare

**Audit a fleet of A2A Agent Cards for skill overlap, capability conflicts, and version drift. Offline, deterministic, zero dependencies.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]()

Part of the [a2a-doctor](https://github.com/ZidoCode/a2a-doctor) suite.

Single-agent card checks pass while the fleet fails: the spec does not define how orchestrators validate capability compatibility before delegating ([A2A#1377](https://github.com/a2aproject/A2A/issues/1377) — silent failure mid-orchestration), and intent routing across agents with overlapping skills is explicitly ambiguous ([A2A discussion #921](https://github.com/a2aproject/A2A/discussions/921)). In production, one team measured "205 active skill names duplicated" ([Automatos PRD-191](https://docs.automatos.app/automatos-ai-docs/design-docs/prds/prd-191-phase2-wave-1-agents-skills-repair)) — the duplicate-skill tax is real.

## Install

```bash
pip install a2a-fleet-compare   # or: copy the .py file
```

## Usage

```bash
$ a2a-fleet-compare card-a.json card-b.json card-c.json
a2a-fleet-compare — 3 agent(s), 7 skill(s) total
  [CRITICAL] skill id 'summarize' declared by 2 agents (card-a.json, card-b.json) — orchestrators routing on skill id will pick one arbitrarily (A2A#921 wrong-agent routing)
  [WARNING ] capability 'streaming': card-a.json declare it, card-b.json do not — callers assuming fleet-wide support will hit silent failures mid-orchestration (A2A#1377)
  [WARNING ] fleet speaks 2 protocol versions (0.3: card-a.json; 1.0: card-b.json) — one negotiator cannot serve all members uniformly

  verdict: 1 CRITICAL — the fleet will misroute or silently fail.
$ a2a-fleet-compare cards/*.json && echo fleet-ok   # CI gate: exit 2 on critical
```

## What it catches

| Finding | Severity |
|---|---|
| Duplicate skill id across agents — wrong-agent routing ([A2A#921](https://github.com/a2aproject/A2A/discussions/921)) | **CRITICAL** |
| Duplicate agent name or interface URL — discovery cannot disambiguate | **CRITICAL** |
| protocolVersion not a known A2A version | **CRITICAL** |
| Near-identical skill names across agents — intent routing ambiguity | warning |
| Capability declared by some members, absent in others ([A2A#1377](https://github.com/a2aproject/A2A/issues/1377)) | warning |
| Protocol version heterogeneity across the fleet | warning |

Exit codes: 0 clean, 1 warnings, 2 critical. Deterministic — same cards, same findings, byte for byte. MIT license.
