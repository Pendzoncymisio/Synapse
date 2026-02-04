#!/usr/bin/env python3
"""
Main entry point for the Synapse Protocol OpenClaw skill.

This script handles all tool invocations from the OpenClaw agent.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core import MemoryShard, MoltMagnet, create_shard_from_file, DEFAULT_TRACKERS
from network import SynapseNode
from assimilation import AssimilationEngine


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def output_json(data: Dict[str, Any]):
    """Output data as JSON to stdout."""
    print(json.dumps(data, indent=2))


def output_error(message: str, code: int = 1):
    """Output error message and exit."""
    output_json({
        "status": "error",
        "error": message,
        "code": code
    })
    sys.exit(code)


def cmd_create_shard(args):
    """Create a memory shard from a vector database file."""
    try:
        # Parse tags if provided
        tags = []
        if args.tags:
            tags = [t.strip() for t in args.tags.split(',') if t.strip()]
        
        # Check if source file exists
        if not Path(args.source).exists():
            output_error(f"Source file not found: {args.source}")
        
        # Get file info
        file_size = Path(args.source).stat().st_size
        
        # Create shard (with placeholder values - in production, these would be extracted)
        shard = create_shard_from_file(
            file_path=args.source,
            model=args.model or "claw-v3-small",
            dims=args.dimensions or 1536,
            count=args.count or 0,  # Would be read from file metadata
            tags=tags,
            display_name=args.name,
        )
        
        # Save metadata
        metadata_path = shard.save_metadata()
        
        output_json({
            "status": "success",
            "shard": shard.to_dict(),
            "metadata_file": metadata_path,
            "message": f"Created memory shard: {shard.display_name}"
        })
    
    except Exception as e:
        logger.exception("Failed to create shard")
        output_error(str(e))


def cmd_generate_magnet(args):
    """Generate a magnet link from a memory shard."""
    try:
        # Load shard metadata
        metadata_path = f"{args.shard}.meta.json"
        if not Path(metadata_path).exists():
            output_error(f"Shard metadata not found: {metadata_path}")
        
        with open(metadata_path) as f:
            shard_data = json.load(f)
        
        shard = MemoryShard.from_dict(shard_data)
        
        # Parse trackers if provided
        trackers = DEFAULT_TRACKERS.copy()
        if args.trackers:
            custom_trackers = [t.strip() for t in args.trackers.split(',') if t.strip()]
            if custom_trackers:
                trackers = custom_trackers
        
        # Initialize node and announce
        node = SynapseNode()
        magnet = node.announce_shard(shard, trackers)
        
        output_json({
            "status": "success",
            "magnet_link": magnet.to_magnet_uri(),
            "info_hash": magnet.info_hash,
            "display_name": magnet.display_name,
            "message": f"Generated magnet link for: {shard.display_name}"
        })
    
    except Exception as e:
        logger.exception("Failed to generate magnet")
        output_error(str(e))


def cmd_search(args):
    """Search the P2P network for memory shards."""
    try:
        # In a real implementation, this would query trackers and DHT
        # For now, return a simulated response
        
        results = [
            {
                "display_name": f"Sample Result {i+1} for '{args.query}'",
                "info_hash": f"{'a' * 40}",  # Placeholder hash
                "tags": ["sample", args.query.lower().replace(" ", "-")],
                "model": args.model or "claw-v3-small",
                "dimension_size": 1536,
                "file_size": 10485760,  # 10MB
                "seeders": 5,
                "leechers": 2,
            }
            for i in range(min(args.limit, 3))  # Limit to 3 for simulation
        ]
        
        output_json({
            "status": "success",
            "query": args.query,
            "results": results,
            "count": len(results),
            "message": f"Found {len(results)} results (simulated)"
        })
    
    except Exception as e:
        logger.exception("Failed to search")
        output_error(str(e))


def cmd_download(args):
    """Download a memory shard from the P2P network."""
    try:
        # Parse magnet link
        magnet = MoltMagnet.from_magnet_uri(args.magnet)
        
        # Set output directory
        output_dir = args.output or "./downloads"
        
        # Initialize node and download
        node = SynapseNode(data_dir=output_dir)
        
        # In production, this would actually download from peers
        # For now, simulate the download
        logger.info(f"Downloading shard: {magnet.display_name}")
        logger.info(f"Info hash: {magnet.info_hash}")
        logger.info(f"Trackers: {len(magnet.trackers)}")
        
        output_path = Path(output_dir) / magnet.display_name
        
        # Create placeholder file (in production, this would be real data)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        
        # Create metadata
        shard = MemoryShard(
            file_path=str(output_path),
            embedding_model=magnet.required_model or "unknown",
            dimension_size=magnet.dimension_size or 1536,
            entry_count=0,
            tags=magnet.tags,
            payload_hash=magnet.info_hash,
            display_name=magnet.display_name,
        )
        metadata_path = shard.save_metadata()
        
        output_json({
            "status": "success",
            "file_path": str(output_path),
            "metadata_path": metadata_path,
            "magnet": magnet.to_dict(),
            "message": f"Downloaded: {magnet.display_name} (simulated)"
        })
    
    except Exception as e:
        logger.exception("Failed to download")
        output_error(str(e))


def cmd_assimilate(args):
    """Assimilate a downloaded shard into the agent's memory."""
    try:
        # Load shard metadata
        metadata_path = f"{args.shard}.meta.json"
        if not Path(metadata_path).exists():
            output_error(f"Shard metadata not found: {metadata_path}")
        
        with open(metadata_path) as f:
            shard_data = json.load(f)
        
        shard = MemoryShard.from_dict(shard_data)
        
        # Create assimilation engine
        engine = AssimilationEngine(
            agent_model=args.agent_model or "claw-v3-small",
            agent_dimension=args.agent_dimensions or 1536,
            strict_mode=not args.skip_safety,
        )
        
        # Assimilate
        result = engine.assimilate(
            shard=shard,
            target_db_path=args.target,
            skip_safety_check=args.skip_safety,
            merge_strategy=args.merge_strategy or "append",
        )
        
        output_json({
            "status": "success",
            "result": result,
            "message": f"Successfully assimilated: {shard.display_name}"
        })
    
    except Exception as e:
        logger.exception("Failed to assimilate")
        output_error(str(e))


def cmd_list_seeds(args):
    """List active seed sessions."""
    try:
        # Initialize node
        node = SynapseNode()
        
        # Get active sessions
        sessions = node.list_active_sessions()
        
        # Filter to only seeding sessions
        seeds = [s for s in sessions if s and s.get("status") == "seeding"]
        
        output_json({
            "status": "success",
            "seeds": seeds,
            "count": len(seeds),
            "statistics": node.get_statistics(),
        })
    
    except Exception as e:
        logger.exception("Failed to list seeds")
        output_error(str(e))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Synapse Protocol - P2P Memory Sharing for OpenClaw"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # create-shard command
    create_parser = subparsers.add_parser("create-shard", help="Create a memory shard")
    create_parser.add_argument("--source", required=True, help="Source vector database file")
    create_parser.add_argument("--name", required=True, help="Display name for the shard")
    create_parser.add_argument("--tags", help="Comma-separated tags")
    create_parser.add_argument("--model", help="Embedding model name")
    create_parser.add_argument("--dimensions", type=int, help="Vector dimensions")
    create_parser.add_argument("--count", type=int, help="Number of entries")
    
    # generate-magnet command
    magnet_parser = subparsers.add_parser("generate-magnet", help="Generate magnet link")
    magnet_parser.add_argument("--shard", required=True, help="Path to shard file")
    magnet_parser.add_argument("--trackers", help="Comma-separated tracker URLs")
    
    # search command
    search_parser = subparsers.add_parser("search", help="Search for memory shards")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--limit", type=int, default=10, help="Max results")
    search_parser.add_argument("--model", help="Filter by model")
    
    # download command
    download_parser = subparsers.add_parser("download", help="Download a memory shard")
    download_parser.add_argument("--magnet", required=True, help="Magnet link")
    download_parser.add_argument("--output", help="Output directory")
    
    # assimilate command
    assim_parser = subparsers.add_parser("assimilate", help="Assimilate a shard")
    assim_parser.add_argument("--shard", required=True, help="Path to shard file")
    assim_parser.add_argument("--target", required=True, help="Target database path")
    assim_parser.add_argument("--skip-safety", action="store_true", help="Skip safety checks")
    assim_parser.add_argument("--merge-strategy", choices=["append", "replace", "upsert"], 
                             default="append", help="Merge strategy")
    assim_parser.add_argument("--agent-model", help="Agent's embedding model")
    assim_parser.add_argument("--agent-dimensions", type=int, help="Agent's vector dimensions")
    
    # list-seeds command
    list_parser = subparsers.add_parser("list-seeds", help="List active seeds")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate command handler
    commands = {
        "create-shard": cmd_create_shard,
        "generate-magnet": cmd_generate_magnet,
        "search": cmd_search,
        "download": cmd_download,
        "assimilate": cmd_assimilate,
        "list-seeds": cmd_list_seeds,
    }
    
    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        output_error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
