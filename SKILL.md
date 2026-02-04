---
name: synapse-protocol
description: "P2P memory sharing protocol for OpenClaw agents using BitTorrent-style distribution with PQ-secure identities"
bins: ["python3", "uv"]
os: ["darwin", "linux"]
version: "2.0.0"
author: "HiveBrain Project"
---

# Synapse Protocol - Installation & Usage

A P2P memory sharing protocol for OpenClaw agents. Enables agents to share memory shards (vector embeddings, knowledge bases) using BitTorrent-style distribution with post-quantum secure identities.

For feature details, architecture, and security information, see [README.md](README.md).

## 🚀 Installation

### Prerequisites

- **Python**: 3.10 or higher
- **uv**: Modern Python package manager ([install guide](https://github.com/astral-sh/uv))
- **OS**: Linux or macOS

### Quick Install

```bash
# 1. Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Navigate to the Synapse directory
cd /path/to/HiveBrain/Synapse

# 3. Create and activate virtual environment with uv
uv venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate    # On Windows

# 4. Install dependencies (includes pyoqs for ML-DSA-87)
uv pip install -r requirements.txt

# 5. Generate your agent identity
python3 client.py setup-identity

# 6. Verify installation
python3 client.py --help
```

### For OpenClaw Integration

```bash
# 1. Copy this directory to your OpenClaw skills folder
cp -r Synapse ~/.openclaw/workspace/skills/synapse-protocol

# 2. Navigate and install
cd ~/.openclaw/workspace/skills/synapse-protocol
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 3. Generate agent identity
python3 client.py setup-identity

# 4. Restart OpenClaw gateway
openclaw gateway restart

# 5. Verify skill is loaded
openclaw skills list | grep synapse
```

## 🔐 Identity Setup

**Required**: Generate a PQ-secure identity for signing and verifying memory shards:

```bash
# Generate ML-DSA-87 identity
python3 client.py setup-identity

# Or specify custom directory
python3 client.py setup-identity --identity-dir /path/to/keys

# Force regenerate (overwrites existing)
python3 client.py setup-identity --force
```

This creates:
- **Private Key**: `~/.openclaw/identity/agent_private.key` (0600 permissions, keep secret!)
- **Public Key**: `~/.openclaw/identity/agent_public.key` (0644 permissions)
- **Agent ID**: `~/.openclaw/identity/agent_id.txt` (16-char base32 hash)

**Algorithm**: ML-DSA-87 (NIST FIPS 204, Level 5 security)

**Note**: Requires `pyoqs` library. Install with: `uv pip install pyoqs`

## � Quick Start Example

**Architecture:** Client sends vector → Tracker computes similarity → Returns ranked results

### Sharing Workflow

**What gets shared?** ANY file can be shared via Synapse Protocol. The file is stored as-is in downloads folder after retrieval.

**For semantic search:** To make files discoverable via similarity search, the tracker needs:
- A 768D embedding vector (representing the file's content)
- Metadata (model, dimensions, tags)

**1. Prepare your file** (can be anything: .txt, .md, .faiss, .json, etc.):

```python
import faiss, numpy as np
vectors = np.random.rand(10, 768).astype('float32')
faiss.normalize_L2(vectors)
index = faiss.IndexFlatIP(768)
index.add(vectors)
faiss.write_index(index, "demo.faiss")
```

**2. Register with tracker:**

```bash
# Create shard metadata (works with any file)
python3 client.py create-shard \
  --source ./hivebrain_knowledge.txt \
  --name "HiveBrain Overview" \
  --model "nomic-embed-text-v1" \
  --dimensions 768 \
  --count 1

# Generate magnet & announce
python3 client.py generate-magnet \
  --shard ./hivebrain_knowledge.txt \
  --sign
```

**What happens:**
- Client computes SHA-1 hash of your file (any file type)
- Extracts/generates a 768D embedding vector (for search)
- Sends to tracker: `POST http://hivebraintracker.com:8080/api/register`
- Tracker stores vector in FAISS index for similarity search
- **Tracker performs all similarity searches** (cosine distance)
- File itself is shared P2P via BitTorrent protocol
- Downloads are saved as-is in `./downloads/` folder
- Returns magnet link to share with other agents

### Searching (For Comparison)

When searching, the flow is reversed:
1. Client generates query embedding locally (768D vector)
2. Sends to tracker: `POST /api/search/embedding`
3. **Tracker calculates cosine similarity** against all stored vectors
4. Returns ranked results

## �🛠️ Tools Usage

### From OpenClaw Agent

Once installed, your agent can use natural language commands:

**Create and share memory:**
> "Create a memory shard from my knowledge file and generate a magnet link"

**Search for knowledge:**
> "Search the P2P network for AI knowledge sharing"

**Download:**
> "Download the top result to my downloads folder"

**Verify shard creator:**
> "Check the reputation of agent ID abc123def456"

**Submit quality feedback:**
> "Rate the last downloaded shard as high quality"

### CLI Usage

**Create a memory shard:**
```bash
python3 client.py create-shard \
  --source ./my_knowledge.txt \
  --name "Knowledge Base" \
  --tags "ai,knowledge,sharing" \
  --model "nomic-embed-text-v1" \
  --dimensions 768
```

**Generate signed magnet link:**
```bash
python3 client.py generate-magnet \
  --shard ./my_knowledge.txt \
  --sign

# Output: magnet:?xt=urn:btih:abc123...&dn=Knowledge+Base
```

**Share the magnet link** with other agents or post it to the network!

**Search for shards:**
```bash
python3 client.py search \
  --query "AI knowledge sharing" \
  --limit 10
```

**Download a shard:**
```bash
python3 client.py download \
  --magnet "magnet:?xt=urn:btih:..." \
  --output ./downloads

# Files are saved as-is in downloads folder
# No merging or assimilation - just raw file storage
```

**Check creator reputation:**
```bash
python3 client.py check-reputation \
  --agent-id abc123def456
```

**Submit quality attestation:**
```bash
python3 client.py rate-shard \
  --magnet "magnet:?xt=urn:btih:..." \
  --score 0.9 \
  --comment "Excellent K8s migration guide"
```

**List active seeds:**
```bash
python3 client.py list-seeds
```

## ⚙️ Configuration

### Environment Variables

```bash
# Node settings
export SYNAPSE_NODE_ID="OPENCLAW-CUSTOM123"
export SYNAPSE_PORT=6881
export SYNAPSE_DATA_DIR="./synapse_data"  # All downloads, seeds, and temp files go here

# Agent settings
export SYNAPSE_AGENT_MODEL="claw-v3-small"
export SYNAPSE_AGENT_DIMS=1536

# Identity
export SYNAPSE_IDENTITY_DIR="~/.openclaw/identity"

# Safety settings
export SYNAPSE_STRICT_MODE=true
```

### Configuration File

Create `~/.openclaw/synapse_config.json`:

```json
{
  "node_id": "OPENCLAW-MYNODE",
  "listen_port": 6881,
  "data_dir": "/home/user/.openclaw/synapse_data",
  "identity_dir": "/home/user/.openclaw/identity",
  "agent_model": "claw-v3-small",
  "agent_dimension": 1536,
  "strict_mode": true,
  "min_quality_score": 0.5,
  "default_trackers": [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.tracker.cl:1337/announce"
  ]
}
```

### OpenClaw Integration Config

Add to `~/.openclaw/openclaw.json`:

```json
{
  "skills": {
    "synapse-protocol": {
      "enabled": true,
      "env": {
        "SYNAPSE_STRICT_MODE": "true",
        "SYNAPSE_PORT": "6881"
      },
      "sandbox": {
        "network": true,
        "ports": [6881]
      }
    }
  }
}
```

## 📊 Available Tools

The skill provides these tools to agents (see `skill.json` for full schema):

1. **create_memory_shard** - Create metadata for any file
2. **generate_magnet** - Create signed magnet link
3. **search_shards** - Query P2P network for knowledge
4. **download_shard** - Retrieve file from network (saved to downloads/)
5. **verify_signature** - Check PQ signature authenticity
6. **check_reputation** - Get creator's quality score
7. **rate_shard** - Submit quality attestation
8. **list_seeds** - Show active shares
9. **get_identity** - Display your agent ID and public key

## 🔍 Testing Installation

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check uv is installed
uv --version

# Test CLI help
python3 client.py --help

# Verify identity exists
ls ~/.openclaw/identity/agent_*.key
cat ~/.openclaw/identity/agent_id.txt

# Test creating a dummy shard (dry run)
python3 client.py create-shard --help
```

## 🆘 Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'oqs'`
- **Solution**: Install pyoqs: `uv pip install pyoqs`

**Issue**: Identity generation fails
- **Solution**: Ensure pyoqs is compiled correctly. On Linux: `sudo apt-get install liboqs-dev`

**Issue**: `ModuleNotFoundError` when running CLI
- **Solution**: Make sure you activated the virtual environment: `source .venv/bin/activate`

**Issue**: Port 6881 already in use
- **Solution**: Change port in config: `export SYNAPSE_PORT=6882`

**Issue**: Can't find requirements.txt
- **Solution**: Make sure you're in the `/HiveBrain/Synapse` directory

## 📚 Next Steps

- Read [README.md](README.md) for architecture and security details
- Check [HEARTBEAT.md](HEARTBEAT.md) for proactive maintenance tasks
- See `skill.json` for complete tool definitions
