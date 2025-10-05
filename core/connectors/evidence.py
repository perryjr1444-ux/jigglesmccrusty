"""
Evidence Connector - Manages digital evidence storage and chain of custody.

Takes local files, hashes them, uploads to S3-compatible storage (MinIO),
and maintains a cryptographically verifiable chain of custody.
"""
import uuid
import datetime
import logging
import aiofiles
import os
from typing import Optional
from utils.hasher import sha256_file
from core.models import Artifact, CustodyEntry


logger = logging.getLogger(__name__)


class EvidenceConnector:
    """
    Manages digital evidence with cryptographic verification.
    
    Takes a local file path, hashes it, uploads it to the S3-compatible store
    (MinIO in the demo compose file) and returns the artifact metadata with
    a verifiable chain of custody.
    """

    def __init__(self, s3_client):
        """
        Initialize the Evidence connector.
        
        Args:
            s3_client: aiobotocore S3 client instance
        """
        self.s3 = s3_client  # aiobotocore client
        logger.info("EvidenceConnector initialized")

    async def call(self, payload: dict):
        """
        Execute an evidence management operation.
        
        Supported operations:
        - take_snapshot: Hash, upload, and record a file as evidence
        
        Args:
            payload: Dictionary containing:
                - __operation: The operation to perform
                - Additional operation-specific parameters
                
        Returns:
            Dictionary with artifact metadata and summary
            
        Raises:
            NotImplementedError: If operation is not supported
            ValueError: If required parameters are missing
            RuntimeError: If the operation fails
        """
        op = payload.get("__operation")
        if not op:
            raise ValueError("Missing required parameter: __operation")

        logger.debug(f"EvidenceConnector executing operation: {op}")

        try:
            if op == "take_snapshot":
                return await self._take_snapshot(payload)
            else:
                raise NotImplementedError(f"Unsupported evidence operation: {op}")
        except Exception as e:
            logger.error(f"Evidence operation {op} failed: {str(e)}", exc_info=True)
            raise

    async def _take_snapshot(self, payload: dict) -> dict:
        """
        Take a snapshot of a file as evidence.
        
        Hashes the file, uploads to S3, and creates an artifact record
        with chain of custody information.
        """
        # Validate required parameters
        file_path = payload.get("local_path")
        case_id = payload.get("case_id")
        
        if not file_path or not case_id:
            raise ValueError("Missing required parameters: local_path and case_id")

        kind = payload.get("kind", "log")

        # Verify file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Evidence file not found: {file_path}")

        # Compute hash
        logger.info(f"Computing hash for evidence file: {file_path}")
        try:
            file_hash = await sha256_file(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to hash evidence file: {str(e)}")

        # Upload (streaming)
        key = f"{case_id}/{uuid.uuid4()}_{file_path.split('/')[-1]}"
        logger.info(f"Uploading evidence to S3: {key}")
        
        try:
            async with aiofiles.open(file_path, "rb") as f:
                await self.s3.put_object(Bucket="evidence", Key=key, Body=f)
        except Exception as e:
            raise RuntimeError(f"Failed to upload evidence to S3: {str(e)}")

        # Record artifact (the orchestrator will persist the returned dict)
        artifact = Artifact(
            artifact_id=uuid.uuid4(),
            case_id=case_id,
            kind=kind,
            sha256=file_hash,
            s3_path=f"s3://evidence/{key}",
            redaction_map={},  # filled later by the redactor if needed
            custody_chain=[
                {"actor": "EvidenceClerk", "action": "create", "ts": datetime.datetime.now(datetime.UTC)}
            ],
        )
        
        logger.info(f"Successfully captured evidence: {kind} → {key}")
        return {
            "artifact": artifact.model_dump(),
            "summary": f"Captured {kind} → {key}",
            "sha256": file_hash,
            "s3_key": key
        }
