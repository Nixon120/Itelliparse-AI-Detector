from typing import Dict

DEFAULT_THRESHOLDS = {
    "likely_ai_or_manipulated": 0.80,
    "likely_human": 0.20,
}

def fuse(modality: str, parts: Dict) -> Dict:
    candidates = []
    if parts.get("image_gen"): candidates.append(parts["image_gen"].get("score", 0))
    if parts.get("video_deepfake"): candidates.append(parts["video_deepfake"].get("score", 0))
    if parts.get("audio_spoof"): candidates.append(parts["audio_spoof"].get("score", 0))
    final = max(candidates) if candidates else 0.0

    if final >= DEFAULT_THRESHOLDS["likely_ai_or_manipulated"]:
        label = "likely_ai_or_manipulated"
    elif final <= DEFAULT_THRESHOLDS["likely_human"]:
        label = "likely_human"
    else:
        label = "uncertain"

    return {"final_score": final, "label": label, "thresholds": DEFAULT_THRESHOLDS}
