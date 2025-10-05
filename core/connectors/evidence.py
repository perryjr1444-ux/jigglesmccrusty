import uuid
import datetime
import aiofiles
from utils.hasher import sha256_file
from core.models import Artifact, CustodyEntry


class EvidenceConnector:
    """
    Takes a local file path, hashes it, uploads it to the S3-compatible store
    (MinIO in the demo compose file) and returns the artifact metadata.
    """

    def __init__(self, s3_client):
        self.s3 = s3_client  # aiobotocore client

    async def call(self, payload: dict):
        op = payload["__operation"]
        if op != "take_snapshot":
            raise NotImplementedError

        file_path = payload["local_path"]
        case_id = payload["case_id"]
        kind = payload.get("kind", "log")

        # Compute hash
        file_hash = await sha256_file(file_path)

        # Upload (streaming)
        key = f"{case_id}/{uuid.uuid4()}_{file_path.split('/')[-1]}"
        async with aiofiles.open(file_path, "rb") as f:
            await self.s3.put_object(Bucket="evidence", Key=key, Body=f)

        # Record artifact (the orchestrator will persist the returned dict)
        artifact = Artifact(
            artifact_id=uuid.uuid4(),
            case_id=case_id,
            kind=kind,
            sha256=file_hash,
            s3_path=f"s3://evidence/{key}",
            redaction_map={},  # filled later by the redactor if needed
            custody_chain=[
                CustodyEntry(actor="EvidenceClerk", action="create")
            ],
        )
        return {"artifact": artifact.model_dump(), "summary": f"Captured {kind} → {key}"}
