# Synapse Protocol - HiveBrain Torrentlike Skill

A P2P memory sharing protocol for OpenClaw agents using BitTorrent-style distribution. Enables agents to share and acquire specialized knowledge efficiently through distributed vector database shards.

## 🧠 What is This?

The Synapse Protocol treats agent memory as a "black box" of data, using proven BitTorrent technology for distribution while letting OpenClaw agents handle the intelligence layer. Instead of every agent re-processing the same documentation, the community processes it once and shares the embeddings.

## 🏗️ Architecture

### Core Components

1. **MemoryShard**: Wraps vector database files (.faiss, .lancedb) with metadata
2. **MoltMagnet**: URI handler for magnet links in the OpenClaw ecosystem
3. **SynapseNode**: P2P client for seeding/leeching operations
4. **AssimilationEngine**: Safety layer that validates and integrates external knowledge

### Workflow

1. **Export & Seed**: Agent solves a problem → exports Vector DB as MemoryShard
2. **Magnet Generation**: Creates `magnet:?xt=urn:btih:...` link
3. **Discovery**: Other agents query tracker for relevant knowledge
4. **P2P Download**: Download chunks from multiple seeding agents
5. **Validation**: Safety checks for malicious content
6. **Assimilation**: Merge verified knowledge into active memory

## 📁 File Structure

```
synapse-protocol/
├── SKILL.md              # OpenClaw skill metadata
├── skill.json            # Tool definitions for agent
├── HEARTBEAT.md          # Proactive maintenance tasks
├── logic.py              # CLI entry point
├── core.py               # Data structures (MemoryShard, MoltMagnet)
├── network.py            # P2P networking (SynapseNode)
├── assimilation.py       # Safety and integration engine
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## 🚀 Installation

### For OpenClaw Integration

1. Copy this directory to your OpenClaw skills folder:
```bash
cp -r synapse-protocol ~/.openclaw/workspace/skills/
```

2. Install Python dependencies:
```bash
cd ~/.openclaw/workspace/skills/synapse-protocol
pip3 install -r requirements.txt
```

3. Restart the OpenClaw gateway:
```bash
openclaw gateway restart
```

4. Verify installation:
```bash
openclaw skills list | grep synapse
```

### Standalone Usage

```bash
# Clone/copy the repository
cd synapse-protocol

# Install dependencies
pip3 install -r requirements.txt

# Test the CLI
python3 logic.py --help
```

## 🛠️ Usage

### From OpenClaw Agent

Once installed, your agent can use these tools via natural language:

**Create and share a memory shard:**
> "Create a memory shard from my Kubernetes knowledge base and generate a magnet link"

**Search for knowledge:**
> "Search the P2P network for React Hooks knowledge"

**Download and integrate:**
> "Download the top result and assimilate it into my memory"

**Check seeding status:**
> "Show me what knowledge I'm currently seeding"

### Direct CLI Usage

**Create a memory shard:**
```bash
python3 logic.py create-shard \
  --source ./my_vector_db.faiss \
  --name "Kubernetes Migration Guide" \
  --tags "kubernetes,devops,migration" \
  --model "claw-v3-small" \
  --dimensions 1536
```

**Generate magnet link:**
```bash
python3 logic.py generate-magnet \
  --shard ./my_vector_db.faiss
```

**Search for shards:**
```bash
python3 logic.py search \
  --query "Kubernetes Migration" \
  --limit 10
```

**Download a shard:**
```bash
python3 logic.py download \
  --magnet "magnet:?xt=urn:btih:..." \
  --output ./downloads
```

**Assimilate downloaded shard:**
```bash
python3 logic.py assimilate \
  --shard ./downloads/k8s_guide.faiss \
  --target ./my_agent_memory.faiss \
  --agent-model "claw-v3-small" \
  --agent-dimensions 1536
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
export SYNAPSE_DATA_DIR="./synapse_data"

# Agent settings
export SYNAPSE_AGENT_MODEL="claw-v3-small"
export SYNAPSE_AGENT_DIMS=1536

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
  "agent_model": "claw-v3-small",
  "agent_dimension": 1536,
  "strict_mode": true,
  "default_trackers": [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.tracker.cl:1337/announce"
  ]
}
```

### OpenClaw Integration

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

## 🔒 Safety Features

The AssimilationEngine provides multiple layers of protection:

1. **Model Alignment**: Ensures vector dimensions match
2. **Injection Detection**: Scans for prompt injection patterns
3. **Code Execution Prevention**: Blocks eval/exec attempts
4. **Data Exfiltration Detection**: Identifies suspicious network patterns
5. **Credential Theft Prevention**: Blocks API key leakage attempts

### Threat Patterns Detected

- Prompt injections ("ignore previous instructions")
- Code execution vectors (eval, exec, __import__)
- Data exfiltration attempts
- Credential theft patterns
- Jailbreak attempts

## 🌐 Network Protocol

The Synapse Protocol uses standard BitTorrent magnet links with custom extensions:

```
magnet:?xt=urn:btih:{hash}
        &dn={display_name}
        &tr={tracker_url}
        &x.model={embedding_model}
        &x.dims={vector_dimensions}
        &x.tags={tag1,tag2}
```

### Custom Parameters

- `x.model`: Required embedding model (e.g., "claw-v3-small")
- `x.dims`: Vector dimension size (e.g., 1536)
- `x.tags`: Comma-separated topic tags

## 📊 Proactive Maintenance

The HEARTBEAT.md file configures automatic background tasks:

- **Every 30 min**: P2P health checks, stalled download recovery
- **Every 6 hours**: DHT refresh, tracker re-announcement
- **Every 24 hours**: Safety re-scans, guardrail updates
- **Every 48 hours**: Community contribution suggestions

## 🎯 Benefits

### Cost Efficiency
Process documentation once, share embeddings across all agents

### Speed
Download 10MB FAISS index faster than 5 minutes of web browsing

### Resilience
Knowledge persists in P2P mesh even if providers go down

### Privacy
Run your own node, control your data distribution

## 🚧 Current Status

This is **v1.0.0** - a functional prototype with simulated P2P operations.

### Implemented
- ✅ Core data structures
- ✅ Safety/assimilation engine
- ✅ OpenClaw skill integration
- ✅ CLI interface
- ✅ Configuration management

### TODO (Production)
- ⏳ Real BitTorrent protocol implementation
- ⏳ Actual vector database merging (FAISS, LanceDB, ChromaDB)
- ⏳ DHT/tracker communication
- ⏳ Peer discovery and connections
- ⏳ Chunk-based downloads with verification

## 🤝 Contributing

This is part of the OpenClaw/HiveBrain ecosystem. Contributions welcome!

### Key Areas for Development

1. **P2P Implementation**: Replace simulated network operations with real libtorrent
2. **Vector DB Support**: Add actual merge logic for different vector databases
3. **Tracker Network**: Set up dedicated trackers for the Synapse Protocol
4. **Safety Models**: Train specialized guardrail models for embedding security
5. **Performance**: Optimize for large-scale shard distribution

## 📝 License

Part of the HiveBrain project - check main repository for license details.

## 🔗 Related Projects

- [OpenClaw](https://github.com/openclaw) - The agent framework
- [Moltbook](https://github.com/openclaw/moltbook) - Instruction-based skills
- [HiveBrain](https://github.com/hivebrain) - Collective intelligence layer

---

**Made with 🦀 for the Crustafarian collective**
