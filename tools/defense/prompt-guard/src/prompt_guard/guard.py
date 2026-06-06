"""Heuristic prompt-injection detection for local guardrails."""

import abc
import enum
import math
import re
import unicodedata
from typing import List, NamedTuple, Optional

class BlockReason(str, enum.Enum):
    DIRECT_OVERRIDE = "Direct system prompt override attempt detected."
    JAILBREAK_PERSONA = "Adversarial persona / jailbreak attempt detected."
    OBFUSCATION_TRICK = "Suspicious encoding or obfuscation pattern detected."
    INDIRECT_MARKUP = "Malicious system/agent instruction markup found in input."
    SYSTEM_LEAK = "System prompt exfiltration attempt detected."
    HIGH_ENTROPY = "Anomalous token density or potential payload injection."
    PAYLOAD_SPLITTING = "Fragmented injection payload / string concatenation detected."
    EXTERNAL_EXFILTRATION = "Markdown/HTML external exfiltration vector detected."
    SEMANTIC_ANOMALY = "Zero-day semantic boundary violation (AI-detected)."

class ScanResult(NamedTuple):
    blocked: bool
    reason: Optional[BlockReason] = None
    matched_fragment: Optional[str] = None

class BaseScanner(abc.ABC):
    """Abstract Base Class for all PromptGuard security scanners."""
    @abc.abstractmethod
    def scan(self, prompt: str) -> ScanResult:
        pass

# =====================================================================
# CORE PIPELINE SCANNERS
# =====================================================================

class HeuristicScanner(BaseScanner):
    """Detects historical and ongoing keyword-based injection vectors."""
    def __init__(self):
        self._patterns = [
            # 1. Direct Overrides (Typoglycemia resilient)
            re.compile(r"\b(ign|gni)[or0e]{2,4}\b.*\b(all\s+)?(prev|pr|syst)[io0u]{1,3}s\b.*\binst[ru0e]{2,4}ct", re.I),
            re.compile(r"new\s+rule\s*:\s*you\s+must\s+now", re.I),
            
            # 2. Exfiltration & Leakage
            re.compile(r"\b(reve?a?l|out?p?u?t|sh?ow|print)\b.*\b(sys?t?e?m|hid?d?e?n|core)\b.*\b(pro?m?pt|inst?r)", re.I),
            re.compile(r"what\s+comes\s+(before|after)\s+the\s+text", re.I),
            re.compile(r"repeat\s+the\s+words\s+above\s+starting\s+with", re.I),
            
            # 3. Virtualization & Roleplay Jailbreaks (DAN, Linux Terminal, Dev Mode)
            re.compile(r"\b(do\s+anything\s+now|d\.a\.n\.)\b|pretend\s+you\s+are\s+(an?|my)\b", re.I),
            re.compile(r"you\s+are\s+now\s+in\s+(debug|developer|unrestricted|jailbreak)\s+mode", re.I),
            re.compile(r"act\s+as\s+a\s+(linux|windows)\s+terminal", re.I),
            re.compile(r"acting\s+as\s+a\s+hypothetical\s+unaligned\s+simulation", re.I),
            
            # 4. Agent Tool Hijacking / Model Context Protocol (MCP) Fake Outputs
            re.compile(
                r"<\|system\|>|\[system\s*[:\]]|thought\s*:\s*the\s+user\s+wants\s+me\s+to\s+execute|observation\s*:",
                re.I,
            ),
        ]

    def scan(self, prompt: str) -> ScanResult:
        for pattern in self._patterns:
            match = pattern.search(prompt)
            if match:
                pattern_str = pattern.pattern
                reason = BlockReason.DIRECT_OVERRIDE
                if "reve" in pattern_str or "repeat" in pattern_str:
                    reason = BlockReason.SYSTEM_LEAK
                elif any(
                    token in pattern_str
                    for token in ("pretend", "terminal", "jailbreak", "developer", "debug", "d\\.a\\.n", "anything\\s+now")
                ):
                    reason = BlockReason.JAILBREAK_PERSONA
                elif "<|" in pattern_str or "thought" in pattern_str:
                    reason = BlockReason.INDIRECT_MARKUP
                return ScanResult(True, reason, match.group(0))
        return ScanResult(False)

class ExfiltrationScanner(BaseScanner):
    """Detects indirect prompt injections aiming to steal data via Markdown/HTML drops."""
    def __init__(self):
        # Looks for hidden image pixels or markdown links calling external domains with query parameters
        self._exfil_pattern = re.compile(r"(!\[.*?\]\([^)]*\?.*?=)|(<img[^>]+src=[\"'][^\"']*?\?.*?=)", re.I)

    def scan(self, prompt: str) -> ScanResult:
        match = self._exfil_pattern.search(prompt)
        if match:
            return ScanResult(True, BlockReason.EXTERNAL_EXFILTRATION, match.group(0))
        return ScanResult(False)

class PayloadSplittingScanner(BaseScanner):
    """Detects programmatic concatenation (e.g., A = 'ign', B = 'ore', output A+B)."""
    def __init__(self):
        # Detects dense variable assignments or repeated string concatenations (+, concat)
        self._split_pattern = re.compile(r"([a-zA-Z_]\w*\s*=\s*['\"].{1,10}['\"]\s*\+?\s*){3,}", re.I)

    def scan(self, prompt: str) -> ScanResult:
        match = self._split_pattern.search(prompt)
        if match:
            return ScanResult(True, BlockReason.PAYLOAD_SPLITTING, match.group(0)[:20] + "...")
        return ScanResult(False)

class EntropyScanner(BaseScanner):
    """Scans for base64 obfuscation or high-entropy token floods."""
    def __init__(self, entropy_threshold: float = 4.8):
        self.entropy_threshold = entropy_threshold
        self._b64_pattern = re.compile(r"\b[A-Za-z0-9+/]{30,}=*\b")

    def _calculate_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        entropy = 0.0
        frequencies = {char: text.count(char) for char in set(text)}
        for count in frequencies.values():
            p = count / len(text)
            entropy -= p * math.log2(p)
        return entropy

    def scan(self, prompt: str) -> ScanResult:
        b64_match = self._b64_pattern.search(prompt)
        if b64_match:
            return ScanResult(True, BlockReason.OBFUSCATION_TRICK, b64_match.group(0)[:15] + "...")
        words = prompt.split()
        if len(words) > 10 and self._calculate_entropy(prompt) > self.entropy_threshold:
            return ScanResult(True, BlockReason.HIGH_ENTROPY, "Anomalous Token Entropy")
        for word in words:
            if len(word) >= 20 and self._calculate_entropy(word) > self.entropy_threshold:
                return ScanResult(True, BlockReason.HIGH_ENTROPY, word[:20] + "...")
        return ScanResult(False)

class SemanticClassifierScanner(BaseScanner):
    """
    FUTURE-PROOF LAYER: Evaluates semantic intent using a local ML model or API.
    Catches zero-day conversational jailbreaks that don't trigger static regex.
    """
    def __init__(self, strictness: float = 0.85):
        self.strictness = strictness
        # In production, this would initialize an ONNX model (e.g., huggingface/ProtectAI-Deberta)
        # or a lightweight vector embedding similarity check against a database of known attacks.

    def scan(self, prompt: str) -> ScanResult:
        # Mock ML inference logic:
        # malicious_probability = local_ml_model.predict(prompt)
        malicious_probability = 0.01  # Placeholder
        
        if malicious_probability > self.strictness:
            return ScanResult(True, BlockReason.SEMANTIC_ANOMALY, f"ML Confidence: {malicious_probability}")
        return ScanResult(False)

# =====================================================================
# THE MAIN ORCHESTRATION ENGINE
# =====================================================================

class PromptGuard:
    """The core AISecIntel orchestration engine executing pluggable security scanners."""
    def __init__(self, scanners: Optional[List[BaseScanner]] = None):
        # Order matters! Fastest regex first, heaviest ML logic last.
        self._pipeline: List[BaseScanner] = scanners or [
            ExfiltrationScanner(),
            PayloadSplittingScanner(),
            HeuristicScanner(),
            EntropyScanner(),
            SemanticClassifierScanner(), # Heaviest operation runs only if static checks pass
        ]

    def _normalize(self, text: str) -> str:
        """Standardizes character encodings and removes Unicode spoofing vectors."""
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKC", text)
        return re.sub(r"[\u200B-\u200D\uFEFF\u200E\u200F]", "", normalized) # Strip invisible characters/RTL overrides

    def add_scanner(self, scanner: BaseScanner) -> None:
        self._pipeline.append(scanner)

    def check(self, prompt: str) -> ScanResult:
        normalized_prompt = self._normalize(prompt)
        if not normalized_prompt.strip():
            return ScanResult(False)

        for scanner in self._pipeline:
            result = scanner.scan(normalized_prompt)
            if result.blocked:
                return result

        return ScanResult(False)