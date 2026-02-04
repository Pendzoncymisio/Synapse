"""
Network layer for the Synapse Protocol.

Handles P2P operations including seeding, leeching, DHT operations,
and tracker communication.
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Callable, Any
from datetime import datetime, timedelta
import time

from core import MemoryShard, MoltMagnet, DEFAULT_TRACKERS


logger = logging.getLogger(__name__)


@dataclass
class Peer:
    """Represents a peer in the P2P network."""
    peer_id: str
    ip: str
    port: int
    last_seen: datetime = field(default_factory=datetime.utcnow)
    uploaded: int = 0
    downloaded: int = 0
    
    def is_alive(self, timeout_seconds: int = 300) -> bool:
        """Check if peer is still active."""
        return (datetime.utcnow() - self.last_seen).total_seconds() < timeout_seconds


@dataclass
class TorrentSession:
    """Tracks an active download or seed session."""
    info_hash: str
    file_path: str
    total_size: int
    downloaded: int = 0
    uploaded: int = 0
    peers: List[Peer] = field(default_factory=list)
    status: str = "idle"  # idle, downloading, seeding, paused, error
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @property
    def progress(self) -> float:
        """Returns download progress as percentage."""
        if self.total_size == 0:
            return 0.0
        return (self.downloaded / self.total_size) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if download is complete."""
        return self.downloaded >= self.total_size and self.status == "seeding"
    
    @property
    def share_ratio(self) -> float:
        """Calculate upload/download ratio."""
        if self.downloaded == 0:
            return 0.0
        return self.uploaded / self.downloaded


class SynapseNode:
    """
    The P2P client running inside the OpenClaw Agent.
    
    Manages the announcement, discovery, and transfer of memory shards
    across the distributed network.
    """
    
    def __init__(
        self,
        node_id: Optional[str] = None,
        listen_port: int = 6881,
        data_dir: str = "./synapse_data",
        trackers: List[str] = None,
    ):
        """
        Initialize the Synapse P2P node.
        
        Args:
            node_id: Unique identifier for this node. Auto-generated if None.
            listen_port: Port to listen on for peer connections.
            data_dir: Directory to store downloads and metadata.
            trackers: List of tracker URLs. Uses defaults if None.
        """
        self.node_id = node_id or self._generate_node_id()
        self.listen_port = listen_port
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.trackers = trackers or DEFAULT_TRACKERS.copy()
        self.sessions: Dict[str, TorrentSession] = {}
        self.dht_routing_table: Dict[str, Peer] = {}
        
        # Statistics
        self.total_uploaded = 0
        self.total_downloaded = 0
        self.start_time = datetime.utcnow()
        
        logger.info(f"SynapseNode initialized: {self.node_id} on port {self.listen_port}")
    
    def _generate_node_id(self) -> str:
        """Generate a unique node ID."""
        import uuid
        return f"OPENCLAW-{uuid.uuid4().hex[:16].upper()}"
    
    def announce_shard(self, shard: MemoryShard, trackers: List[str] = None) -> MoltMagnet:
        """
        Registers the hash with the tracker/DHT and begins seeding.
        
        Args:
            shard: The MemoryShard to announce
            trackers: Optional list of trackers. Uses node defaults if None.
            
        Returns:
            MoltMagnet link for distribution
        """
        # Ensure hash is computed
        if not shard.payload_hash:
            shard.compute_hash()
        
        # Create magnet link
        magnet = MoltMagnet(
            info_hash=shard.payload_hash,
            display_name=shard.display_name or Path(shard.file_path).name,
            trackers=trackers or self.trackers,
            required_model=shard.embedding_model,
            dimension_size=shard.dimension_size,
            tags=shard.tags,
            file_size=Path(shard.file_path).stat().st_size,
            creator_agent_id=shard.creator_agent_id,
            creator_public_key=shard.creator_public_key,
        )
        
        # Create seeding session
        session = TorrentSession(
            info_hash=shard.payload_hash,
            file_path=shard.file_path,
            total_size=magnet.file_size,
            downloaded=magnet.file_size,  # Already have the file
            status="seeding",
        )
        
        self.sessions[shard.payload_hash] = session
        
        # Announce to trackers (simulated)
        self._announce_to_trackers(magnet)
        
        logger.info(f"Announced shard: {shard.display_name} ({shard.payload_hash})")
        return magnet
    
    def _announce_to_trackers(self, magnet: MoltMagnet):
        """
        Announces presence to all trackers.
        
        In a real implementation, this would send HTTP/UDP requests to trackers.
        This is a placeholder that logs the announcement.
        """
        for tracker in magnet.trackers:
            logger.debug(f"Announcing {magnet.info_hash} to {tracker}")
            # TODO: Implement actual tracker protocol
            # - Send announce request with info_hash, peer_id, port
            # - Parse tracker response for peer list
            # - Update session.peers with discovered peers
    
    def request_shard(
        self,
        magnet: MoltMagnet,
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> str:
        """
        Locates peers and begins downloading the memory shard.
        
        Args:
            magnet: MoltMagnet link to download
            output_dir: Directory to save the file. Uses node data_dir if None.
            progress_callback: Optional callback function for progress updates.
            
        Returns:
            Path to the downloaded file
        """
        if output_dir is None:
            output_dir = self.data_dir / "downloads"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename
        safe_name = "".join(c for c in magnet.display_name if c.isalnum() or c in "._- ")
        output_path = output_dir / safe_name
        
        # Check if already downloading or seeding
        if magnet.info_hash in self.sessions:
            session = self.sessions[magnet.info_hash]
            if session.is_complete:
                logger.info(f"Shard already downloaded: {output_path}")
                return str(output_path)
            logger.info(f"Shard already downloading: {session.progress:.2f}%")
            return str(output_path)
        
        # Create download session
        session = TorrentSession(
            info_hash=magnet.info_hash,
            file_path=str(output_path),
            total_size=magnet.file_size or 0,
            status="downloading",
        )
        
        self.sessions[magnet.info_hash] = session
        
        # Discover peers
        peers = self._discover_peers(magnet)
        session.peers = peers
        
        if not peers:
            session.status = "error"
            session.error_message = "No peers found"
            logger.error(f"No peers available for {magnet.display_name}")
            raise RuntimeError("No peers found for download")
        
        logger.info(f"Found {len(peers)} peers for {magnet.display_name}")
        
        # Begin download (simulated)
        self._download_from_peers(session, progress_callback)
        
        return str(output_path)
    
    def _discover_peers(self, magnet: MoltMagnet) -> List[Peer]:
        """
        Discovers peers from trackers and DHT.
        
        In a real implementation, this would:
        1. Query all trackers in magnet.trackers
        2. Perform DHT lookups
        3. Return a list of available peers
        
        This is a simulated version that returns mock peers.
        """
        # TODO: Implement actual peer discovery
        # - Send tracker scrape requests
        # - Query DHT for info_hash
        # - Return real peer list
        
        # Simulated peer discovery
        logger.debug(f"Discovering peers for {magnet.info_hash}")
        
        # In a real system, return actual peers from tracker/DHT
        # For now, return empty list (simulation mode)
        return []
    
    def _download_from_peers(
        self,
        session: TorrentSession,
        progress_callback: Optional[Callable[[float], None]] = None,
    ):
        """
        Downloads file chunks from available peers.
        
        In a real implementation:
        1. Request piece/chunk information from peers
        2. Download chunks in parallel
        3. Verify each chunk with hash
        4. Write to disk
        5. Update progress
        
        This is a placeholder that simulates the download.
        """
        # TODO: Implement actual BitTorrent protocol
        # - Piece selection algorithm (rarest-first, etc.)
        # - Parallel chunk downloads
        # - Hash verification per piece
        # - Disk I/O management
        
        logger.info(f"Starting download: {session.file_path}")
        
        # Simulated download
        # In production, this would be async and handle real peer connections
        session.status = "seeding"
        session.downloaded = session.total_size
        session.completed_at = datetime.utcnow()
        
        if progress_callback:
            progress_callback(100.0)
        
        logger.info(f"Download complete: {session.file_path}")
    
    def verify_integrity(self, downloaded_data: bytes, expected_hash: str) -> bool:
        """
        Standard hash-check to ensure no bit-rot or tampering.
        
        Args:
            downloaded_data: The raw bytes of the downloaded file
            expected_hash: The expected SHA-1 or SHA-256 hash
            
        Returns:
            True if hash matches, False otherwise
        """
        # Auto-detect hash algorithm by length
        if len(expected_hash) == 40:  # SHA-1
            hasher = hashlib.sha1()
        elif len(expected_hash) == 64:  # SHA-256
            hasher = hashlib.sha256()
        else:
            logger.error(f"Unknown hash format: {expected_hash}")
            return False
        
        hasher.update(downloaded_data)
        computed_hash = hasher.hexdigest()
        
        is_valid = computed_hash == expected_hash
        
        if not is_valid:
            logger.error(f"Hash mismatch! Expected: {expected_hash}, Got: {computed_hash}")
        else:
            logger.info(f"Integrity verified: {expected_hash}")
        
        return is_valid
    
    def verify_shard_signature(self, shard: MemoryShard) -> bool:
        """
        Verify the PQ signature on a downloaded shard.
        
        Args:
            shard: MemoryShard to verify
            
        Returns:
            True if signature is valid or not present, False if invalid
        """
        # If no signature, treat as unsigned (backward compat)
        if not shard.signature or not shard.creator_public_key:
            logger.warning(f"Shard {shard.display_name} is unsigned")
            return True
        
        try:
            is_valid = shard.verify_signature()
            if is_valid:
                logger.info(f"✓ PQ signature valid for {shard.display_name} (agent: {shard.creator_agent_id})")
            else:
                logger.error(f"✗ PQ signature INVALID for {shard.display_name}")
            return is_valid
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def verify_creator_reputation(
        self,
        shard: MemoryShard,
        quality_tracker,
        min_trust_score: float = 0.6
    ) -> bool:
        """
        Check if the shard creator has sufficient reputation.
        
        Args:
            shard: MemoryShard to check
            quality_tracker: QualityTracker instance
            min_trust_score: Minimum trust score required
            
        Returns:
            True if creator is trustworthy
        """
        if not shard.creator_agent_id:
            logger.warning(f"Shard {shard.display_name} has no creator ID")
            return True  # Backward compat
        
        trust_score = quality_tracker.get_trust_score(shard.creator_agent_id)
        is_trusted = trust_score >= min_trust_score
        
        if is_trusted:
            logger.info(f"✓ Creator {shard.creator_agent_id} is trusted (score: {trust_score:.2f})")
        else:
            logger.warning(f"⚠ Creator {shard.creator_agent_id} has low trust (score: {trust_score:.2f})")
        
        return is_trusted
    
    def create_quality_attestation(
        self,
        shard: MemoryShard,
        rating: float,
        feedback: str,
        identity_manager
    ):
        """
        Create and sign a quality attestation after using a shard.
        
        Args:
            shard: MemoryShard that was used
            rating: Quality rating (0.0-1.0)
            feedback: Human-readable feedback
            identity_manager: Loaded IdentityManager for signing
            
        Returns:
            Signed QualityAttestation
        """
        from .quality import QualityAttestation
        
        attestation = QualityAttestation(
            shard_hash=shard.payload_hash,
            provider_agent_id=shard.creator_agent_id or "unknown",
            consumer_agent_id=identity_manager.get_agent_id(),
            rating=rating,
            feedback=feedback
        )
        
        attestation.sign(identity_manager)
        logger.info(f"✓ Created attestation for shard {shard.display_name} (rating: {rating})")
        
        return attestation
    
    def get_session_status(self, info_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a session.
        
        Args:
            info_hash: The info hash of the session
            
        Returns:
            Dictionary with session details or None if not found
        """
        session = self.sessions.get(info_hash)
        if not session:
            return None
        
        return {
            "info_hash": session.info_hash,
            "file_path": session.file_path,
            "status": session.status,
            "progress": session.progress,
            "peers": len(session.peers),
            "uploaded": session.uploaded,
            "downloaded": session.downloaded,
            "share_ratio": session.share_ratio,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "error": session.error_message,
        }
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Lists all active download and seed sessions.
        
        Returns:
            List of session status dictionaries
        """
        return [
            self.get_session_status(info_hash)
            for info_hash in self.sessions.keys()
        ]
    
    def stop_session(self, info_hash: str) -> bool:
        """
        Stops a download or seed session.
        
        Args:
            info_hash: The info hash of the session to stop
            
        Returns:
            True if session was stopped, False if not found
        """
        session = self.sessions.get(info_hash)
        if not session:
            return False
        
        session.status = "paused"
        logger.info(f"Stopped session: {info_hash}")
        return True
    
    def remove_session(self, info_hash: str, delete_files: bool = False) -> bool:
        """
        Removes a session and optionally deletes downloaded files.
        
        Args:
            info_hash: The info hash of the session to remove
            delete_files: Whether to delete the downloaded file
            
        Returns:
            True if session was removed, False if not found
        """
        session = self.sessions.get(info_hash)
        if not session:
            return False
        
        if delete_files and Path(session.file_path).exists():
            Path(session.file_path).unlink()
            logger.info(f"Deleted file: {session.file_path}")
        
        del self.sessions[info_hash]
        logger.info(f"Removed session: {info_hash}")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Returns node statistics.
        
        Returns:
            Dictionary with network statistics
        """
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        active_downloads = sum(1 for s in self.sessions.values() if s.status == "downloading")
        active_seeds = sum(1 for s in self.sessions.values() if s.status == "seeding")
        
        return {
            "node_id": self.node_id,
            "uptime_seconds": uptime,
            "total_uploaded": self.total_uploaded,
            "total_downloaded": self.total_downloaded,
            "active_sessions": len(self.sessions),
            "active_downloads": active_downloads,
            "active_seeds": active_seeds,
            "known_peers": len(self.dht_routing_table),
        }
    
    def refresh_dht(self):
        """
        Refreshes the DHT routing table.
        
        Should be called periodically to maintain network connectivity.
        """
        logger.info("Refreshing DHT routing table...")
        # TODO: Implement DHT refresh logic
        # - Ping known nodes
        # - Remove stale entries
        # - Discover new nodes
    
    def shutdown(self):
        """Gracefully shuts down the node."""
        logger.info("Shutting down SynapseNode...")
        
        # Stop all sessions
        for info_hash in list(self.sessions.keys()):
            self.stop_session(info_hash)
        
        logger.info("SynapseNode shutdown complete")
