from typing import List, Dict

def scan_watermarks(file_path: str, modality: str) -> List[Dict]:
    return [{"type": "synthid", "detected": False, "confidence": 0.01}]
