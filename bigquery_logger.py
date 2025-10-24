# File: bigquery_logger.py
# ======================
"""BigQuery logger for agent conversations"""

from google.cloud import bigquery
from datetime import datetime
import json
from typing import Dict, Any, Optional
import os

class ConversationLogger:
    """Logs agent conversations to BigQuery"""
    
    def __init__(self, project_id: str = None, dataset_id: str = None, table_id: str = None):
        """Initialize BigQuery logger"""
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT not found in environment")
        
        self.dataset_id = dataset_id or os.getenv("BIGQUERY_DATASET_ID", "simnet_aero_bot")
        self.table_id = table_id or os.getenv("BIGQUERY_TABLE_ID", "simnet_conversations")
        
        self.client = bigquery.Client(project=self.project_id)
        self.table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        
        self._ensure_dataset_exists()
        self._ensure_table_exists()
    
    def _ensure_dataset_exists(self):
        """Create dataset if it doesn't exist"""
        dataset_ref = f"{self.project_id}.{self.dataset_id}"
        
        try:
            self.client.get_dataset(dataset_ref)
        except Exception:
            try:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
                self.client.create_dataset(dataset, timeout=30)
                print(f"✓ Created dataset '{self.dataset_id}'")
            except Exception:
                pass  # Dataset might exist or lack permissions
    
    def _ensure_table_exists(self):
        """Create table if it doesn't exist"""
        schema = [
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("agent_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("user_query", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("agent_response", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("has_image_input", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("response_time_ms", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("model_used", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("metadata", "STRING", mode="NULLABLE"),
        ]
        
        table = bigquery.Table(self.table_ref, schema=schema)
        
        try:
            self.client.create_table(table, exists_ok=True)
        except Exception:
            pass  # Table might exist
    
    def log_conversation(
        self,
        session_id: str,
        user_query: str,
        agent_response: str,
        agent_name: str = "SimnetAgent",
        has_image_input: bool = False,
        response_time_ms: Optional[float] = None,
        model_used: str = "gemini-2.5-pro",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a conversation turn to BigQuery"""
        row = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_name": agent_name,
            "user_query": user_query,
            "agent_response": agent_response,
            "has_image_input": has_image_input,
            "response_time_ms": response_time_ms,
            "model_used": model_used,
            "metadata": json.dumps(metadata) if metadata else None,
        }
        
        errors = self.client.insert_rows_json(self.table_ref, [row])
        
        if errors:
            raise Exception(f"Failed to log: {errors}")
        
        return session_id