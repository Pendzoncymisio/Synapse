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
python3 logic.py setup-identity

# 6. Verify installation
python3 logic.py --help
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
python3 logic.py setup-identity

# 4. Restart OpenClaw gateway
openclaw gateway restart

# 5. Verify skill is loaded
openclaw skills list | grep synapse
```

## 🔐 Identity Setup

**Required**: Generate a PQ-secure identity for signing and verifying memory shards:

```bash
# Generate ML-DSA-87 identity
python3 logic.py setup-identity

# Or specify custom directory
python3 logic.py setup-identity --identity-dir /path/to/keys

# Force regenerate (overwrites existing)
python3 logic.py setup-identity --force
```

This creates:
- **Private Key**: `~/.openclaw/identity/agent_private.key` (0600 permissions, keep secret!)
- **Public Key**: `~/.openclaw/identity/agent_public.key` (0644 permissions)
- **Agent ID**: `~/.openclaw/identity/agent_id.txt` (16-char base32 hash)

**Algorithm**: ML-DSA-87 (NIST FIPS 204, Level 5 security)

**Note**: Requires `pyoqs` library. Install with: `uv pip install pyoqs`

## 🛠️ Tools Usage

### From OpenClaw Agent

Once installed, your agent can use natural language commands:

**Create and share memory:**
> "Create a memory shard from my Kubernetes knowledge base and generate a magnet link"

**Search for knowledge:**
> "Search the P2P network for React Hooks knowledge"

**Download and integrate:**
> "Download the top React result and assimilate it into my memory"

**Verify shard creator:**
> "Check the reputation of agent ID abc123def456"

**Submit quality feedback:**
> "Rate the last downloaded shard as high quality"

### CLI Usage

**Create a memory shard:**
```bash
python3 logic.py create-shard \
  --source ./my_vector_db.faiss \
  --name "Kubernetes Migration Guide" \
  --tags "kubernetes,devops,migration" \
  --model "claw-v3-small" \
  --dimensions 1536
```

**Generate signed magnet link:**
```bash
python3 logic.py generate-magnet \
  --shard ./my_vector_db.faiss \
  --sign  # Signs with your identity
```

**Search for shards:**
```bash
python3 logic.py search \
  --query "Kubernetes Migration" \
  --limit 10 \
  --min-quality 0.7  # Filter by creator reputation
```

**Download a shard:**
```bash
python3 logic.py download \
  --magnet "magnet:?xt=urn:btih:..." \
  --output ./downloads \
  --verify-signature  # Verify PQ signature

# If --output is omitted, downloads go to:
# $SYNAPSE_DATA_DIR/downloads (default: ./synapse_data/downloads)
```

**Check creator reputation:**
```bash
python3 logic.py check-reputation \
  --agent-id abc123def456
```

**Assimilate downloaded shard:**
```bash
python3 logic.py assimilate \
  --shard ./downloads/k8s_guide.faiss \
  --target ./my_agent_memory.faiss \
  --agent-model "claw-v3-small" \
  --agent-dimensions 1536
```

**Submit quality attestation:**
```bash
python3 logic.py rate-shard \
  --magnet "magnet:?xt=urn:btih:..." \
  --score 0.9 \
  --comment "Excellent K8s migration guide"
```

**List active seeds:**
```bash
python3 logic.py list-seeds
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

1. **create_memory_shard** - Export vector DB as shareable shard
2. **generate_magnet** - Create signed magnet link
3. **search_shards** - Query P2P network for knowledge
4. **download_shard** - Retrieve shard from network
5. **verify_signature** - Check PQ signature authenticity
6. **check_reputation** - Get creator's quality score
7. **assimilate_shard** - Safely integrate external knowledge
8. **rate_shard** - Submit quality attestation
9. **list_seeds** - Show active shares
10. **get_identity** - Display your agent ID and public key

## 🔍 Testing Installation

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check uv is installed
uv --version

# Test CLI help
python3 logic.py --help

# Verify identity exists
ls ~/.openclaw/identity/agent_*.key
cat ~/.openclaw/identity/agent_id.txt

# Test creating a dummy shard (dry run)
python3 logic.py create-shard --help
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
