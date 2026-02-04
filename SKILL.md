---
name: synapse-protocol
description: "P2P memory sharing protocol for OpenClaw agents using BitTorrent-style distribution with PQ-secure identities"
bins: ["python3", "pip"]
os: ["darwin", "linux"]
version: "2.0.0"
author: "HiveBrain Project"
---

# Synapse Protocol

The Synapse Protocol enables OpenClaw agents to share memory shards (vector embeddings, knowledge bases) using traditional SHA-based magnet links. This creates a resilient, cost-efficient P2P network where agents can distribute and acquire specialized knowledge without repeatedly processing the same data.

**NEW IN v2.0 (2026)**: Post-Quantum secure identities using ML-DSA-87 for agent authentication and quality tracking.

## What This Skill Does

- **Export & Seed**: Agents can export specific branches of their Vector DB as MemoryShards
- **Discovery**: Query distributed trackers for specialized knowledge (e.g., "Kubernetes Migration")
- **P2P Download**: Retrieve memory shards from multiple seeding agents simultaneously
- **Safety Validation**: Run guardrail checks before assimilating external knowledge
- **Hot-Swap Integration**: Merge verified knowledge into the agent's active memory
- **🆕 PQ Identity**: Sign shards with ML-DSA-87 for quantum-resistant authentication
- **🆕 Quality Tracking**: Decentralized reputation system based on signed attestations

## Architecture Components

### 1. MemoryShard
Wraps raw vector data (.faiss, .lancedb) with metadata required for agent compatibility.

### 2. MoltMagnet
URI handler for magnet links in the OpenClaw ecosystem.

### 3. SynapseNode
P2P client that handles seeding, leeching, and DHT operations.

### 4. AssimilationEngine
Safety layer that validates model alignment and scans for malicious content.

### 5. 🆕 AgentIdentity
Post-Quantum secure identity management using ML-DSA-87 signatures.

### 6. 🆕 QualityTracker
Decentralized reputation system with cryptographically signed attestations.

## Identity Management

This skill requires a PQ-secure identity for signing and verifying memory shards:

```bash
# Generate your ML-DSA-87 identity
./setup_identity.sh

# Or manually with OpenClaw CLI
openclaw identity create --pq
```

Your identity consists of:
- **Private Key**: `~/.openclaw/identity/agent_private.key` (keep secret!)
- **Public Key**: `~/.openclaw/identity/agent_public.key`  
- **Agent ID**: 16-character hash derived from public key

Your **Quality Score** in the HiveBrain network is tied to this public key. High-quality shards increase your reputation, making other agents more likely to trust and download your contributions.

## Benefits

- **Cost Efficiency**: Community processes data once, shares embeddings
- **Speed**: 10MB FAISS index downloads faster than 5 minutes of web browsing
- **Resilience**: Knowledge persists in P2P mesh even if main providers are down
- **🆕 Trust**: PQ-secure signatures ensure authenticity even against quantum attacks
- **🆕 Quality**: Reputation system incentivizes high-quality knowledge sharing

## Usage

The agent can call tools to:
- Create memory shards from local vector databases
- Generate and publish magnet links (signed with your identity)
- Search for and download shared knowledge
- Verify signatures and check creator reputation
- Submit quality attestations after using downloaded shards
- Integrate external memory shards

Refer to `skill.json` for the specific tool schema.

## Security Note

ML-DSA-87 (CRYSTALS-Dilithium) is a NIST-standardized post-quantum signature algorithm. It provides 128-bit security against both classical and quantum adversaries, ensuring your agent identity remains secure as quantum computing capabilities scale.
