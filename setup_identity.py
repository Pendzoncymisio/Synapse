#!/usr/bin/env python3
# /// script
# dependencies = ["pyoqs"]
# ///
"""
Generate ML-DSA-87 identity for Synapse Protocol.

This script creates a post-quantum secure identity used for signing
and verifying memory shards in the HiveBrain network.
"""

import os
import sys
import base64
import hashlib
from pathlib import Path

try:
    import oqs
except ImportError:
    print("Error: pyoqs not installed")
    print("Install with: uv pip install pyoqs")
    sys.exit(1)


def generate_identity(identity_dir: str = None):
    """
    Generate ML-DSA-87 keypair for agent identity.
    
    Args:
        identity_dir: Directory to store keys (default: ~/.openclaw/identity)
    """
    # Default to OpenClaw identity directory
    if identity_dir is None:
        identity_dir = os.path.expanduser("~/.openclaw/identity")
    
    identity_path = Path(identity_dir)
    identity_path.mkdir(parents=True, exist_ok=True)
    
    # ML-DSA-87 is the high-security variant (NIST Level 5)
    sig_alg = "ML-DSA-87"
    
    print(f"Generating {sig_alg} identity...")
    
    try:
        with oqs.Signature(sig_alg) as signer:
            public_key = signer.generate_keypair()
            secret_key = signer.export_secret_key()
            
            # Save keys in binary format
            private_key_path = identity_path / "agent_private.key"
            public_key_path = identity_path / "agent_public.key"
            
            # Write private key (secure permissions)
            with open(private_key_path, "wb") as f:
                f.write(secret_key)
            os.chmod(private_key_path, 0o600)  # Read/write for owner only
            
            # Write public key
            with open(public_key_path, "wb") as f:
                f.write(public_key)
            os.chmod(public_key_path, 0o644)  # Readable by all
            
            # Generate agent ID (16-char hash from public key)
            pubkey_hash = hashlib.sha256(public_key).digest()
            agent_id = base64.b32encode(pubkey_hash[:10]).decode().lower().rstrip("=")
            
            # Save agent ID for quick lookup
            agent_id_path = identity_path / "agent_id.txt"
            with open(agent_id_path, "w") as f:
                f.write(agent_id)
            
            print(f"✅ Identity generated successfully!")
            print(f"   Private Key: {private_key_path}")
            print(f"   Public Key:  {public_key_path}")
            print(f"   Agent ID:    {agent_id}")
            print()
            print("⚠️  KEEP YOUR PRIVATE KEY SECRET!")
            print(f"   Permissions set to 0600 on {private_key_path}")
            
            return {
                "agent_id": agent_id,
                "private_key_path": str(private_key_path),
                "public_key_path": str(public_key_path),
                "algorithm": sig_alg
            }
            
    except Exception as e:
        print(f"❌ Failed to generate identity: {e}")
        sys.exit(1)


def check_identity_exists(identity_dir: str = None) -> bool:
    """Check if identity already exists."""
    if identity_dir is None:
        identity_dir = os.path.expanduser("~/.openclaw/identity")
    
    identity_path = Path(identity_dir)
    private_key = identity_path / "agent_private.key"
    public_key = identity_path / "agent_public.key"
    
    return private_key.exists() and public_key.exists()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate ML-DSA-87 identity for Synapse Protocol"
    )
    parser.add_argument(
        "--identity-dir",
        default=None,
        help="Directory to store keys (default: ~/.openclaw/identity)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing identity"
    )
    
    args = parser.parse_args()
    
    # Check if identity already exists
    if check_identity_exists(args.identity_dir) and not args.force:
        print("⚠️  Identity already exists!")
        identity_dir = args.identity_dir or os.path.expanduser("~/.openclaw/identity")
        print(f"   Location: {identity_dir}")
        print()
        print("To regenerate, use: --force")
        print("WARNING: This will overwrite your existing keys!")
        sys.exit(0)
    
    # Generate new identity
    generate_identity(args.identity_dir)


if __name__ == "__main__":
    main()
