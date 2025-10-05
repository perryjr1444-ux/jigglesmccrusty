import uuid
from typing import Dict, List, Any
from pydantic import BaseModel


class Artifact(BaseModel):
    artifact_id: uuid.UUID
    case_id: str
    kind: str
    sha256: str
    s3_path: str
    redaction_map: Dict[str, str]
    custody_chain: List[Dict[str, Any]]
