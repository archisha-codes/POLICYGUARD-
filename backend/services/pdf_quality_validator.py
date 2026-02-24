# backend/services/pdf_quality_validator.py
# PDF Extraction Quality Validation
# Validates text extraction from RBI PDFs and detects OCR errors

from typing import Dict, List, Tuple
from dataclasses import dataclass
import re
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ExtractionQuality(str, Enum):
    """Quality assessment of PDF text extraction"""
    EXCELLENT = "excellent"  # <2% errors
    GOOD = "good"  # 2-5% errors
    ACCEPTABLE = "acceptable"  # 5-10% errors
    POOR = "poor"  # >10% errors


@dataclass
class ExtractionMetrics:
    """Metrics for PDF extraction quality"""
    document_id: str
    total_characters: int
    detected_errors: int
    confidence_score: float  # 0.0 - 1.0
    quality_level: ExtractionQuality
    error_types: Dict[str, int]
    recommendations: List[str]


class PDFQualityValidator:
    """
    Validates text extraction quality from RBI PDFs.
    Detects common OCR errors and low-quality extractions.
    """

    def __init__(self):
        # Common OCR error patterns
        self.ocr_error_patterns = {
            "garbled_text": r"[^\w\s\.,;:()'\-\"]",  # Non-standard chars
            "character_confusion": r"\b[l|1I][l|1I]+\b|[O0]{2,}",  # 0/O, 1/l/I confusion
            "spacing_issues": r"\s{2,}",  # Multiple spaces
            "line_breaks": r"\n{2,}",  # Excessive line breaks
            "special_chars": r"[\x00-\x1f\x7f-\x9f]",  # Control characters
        }

        # Regulatory keywords that should be present in RBI documents
        self.regulatory_keywords = {
            "KYC", "AML", "RBI", "Circular", "Transaction",
            "Compliance", "Due Diligence", "Customer", "Verification"
        }

    def validate_extraction(self, text: str, document_id: str) -> ExtractionMetrics:
        """
        Validate PDF text extraction quality.
        Returns metrics and confidence score.
        """
        if not text:
            return ExtractionMetrics(
                document_id=document_id,
                total_characters=0,
                detected_errors=0,
                confidence_score=0.0,
                quality_level=ExtractionQuality.POOR,
                error_types={},
                recommendations=["Document appears empty"]
            )

        detected_errors = 0
        error_types = {}

        # Check 1: Garbled text detection
        garbled_matches = len(re.findall(self.ocr_error_patterns["garbled_text"], text))
        if garbled_matches > len(text) * 0.05:  # >5% unusual chars
            detected_errors += garbled_matches
            error_types["garbled_text"] = garbled_matches

        # Check 2: Character confusion (0/O, 1/l/I)
        char_confusion = len(re.findall(self.ocr_error_patterns["character_confusion"], text))
        if char_confusion > 0:
            detected_errors += char_confusion
            error_types["character_confusion"] = char_confusion

        # Check 3: Spacing issues
        spacing_issues = len(re.findall(self.ocr_error_patterns["spacing_issues"], text))
        error_types["spacing_issues"] = spacing_issues

        # Check 4: Control characters (indicates corruption)
        control_chars = len(re.findall(self.ocr_error_patterns["special_chars"], text))
        if control_chars > 0:
            detected_errors += control_chars
            error_types["control_characters"] = control_chars

        # Check 5: Regulatory keyword presence
        found_keywords = sum(1 for kw in self.regulatory_keywords if kw.lower() in text.lower())
        keyword_coverage = found_keywords / len(self.regulatory_keywords)

        # Check 6: Readability score (average line length)
        lines = text.split('\n')
        avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
        if avg_line_length < 20 or avg_line_length > 200:  # Suspicious line lengths
            error_types["unusual_line_length"] = len(lines)

        # Calculate metrics
        total_chars = len(text)
        error_rate = detected_errors / max(total_chars, 1)
        confidence_score = (
            (1.0 - error_rate) * 0.6 +  # Error rate weight
            keyword_coverage * 0.4  # Keyword coverage weight
        )

        # Determine quality level
        if error_rate < 0.02:  # <2% errors
            quality = ExtractionQuality.EXCELLENT
        elif error_rate < 0.05:  # <5% errors
            quality = ExtractionQuality.GOOD
        elif error_rate < 0.10:  # <10% errors
            quality = ExtractionQuality.ACCEPTABLE
        else:
            quality = ExtractionQuality.POOR

        # Generate recommendations
        recommendations = self._generate_recommendations(
            quality, error_types, keyword_coverage, confidence_score
        )

        return ExtractionMetrics(
            document_id=document_id,
            total_characters=total_chars,
            detected_errors=detected_errors,
            confidence_score=max(0.0, min(1.0, confidence_score)),
            quality_level=quality,
            error_types=error_types,
            recommendations=recommendations
        )

    def _generate_recommendations(self, quality: ExtractionQuality, error_types: Dict,
                                 keyword_coverage: float, confidence_score: float) -> List[str]:
        """
        Generate recommendations based on extraction quality.
        """
        recommendations = []

        if quality == ExtractionQuality.POOR:
            recommendations.append("⚠️ Document quality is poor - consider re-scanning")
            if "garbled_text" in error_types:
                recommendations.append("Large amount of garbled text detected")
            if "control_characters" in error_types:
                recommendations.append("Document may be corrupted - use original file")
            recommendations.append("Manual review strongly recommended before using for embeddings")

        elif quality == ExtractionQuality.ACCEPTABLE:
            recommendations.append("Document quality is acceptable but needs attention")
            if "character_confusion" in error_types:
                recommendations.append("Character confusion detected - review sensitive numbers")
            recommendations.append("Use with caution in RAG pipeline")

        elif quality == ExtractionQuality.GOOD:
            recommendations.append("✅ Document quality is good")
            if error_types:
                recommendations.append("Minor errors detected - proceed with confidence")
            recommendations.append("Suitable for RAG embeddings")

        elif quality == ExtractionQuality.EXCELLENT:
            recommendations.append("✅ Document quality is excellent")
            recommendations.append("Safe to use directly in RAG pipeline")
            recommendations.append("High confidence in retrieval accuracy")

        if keyword_coverage < 0.3:
            recommendations.append(f"⚠️ Low regulatory keyword coverage ({keyword_coverage:.0%})")
            recommendations.append("Verify this is a valid RBI document")

        return recommendations

    def batch_validate(self, documents: Dict[str, str]) -> Dict[str, ExtractionMetrics]:
        """
        Validate multiple documents.
        Returns metrics for each document.
        """
        results = {}
        for doc_id, text in documents.items():
            results[doc_id] = self.validate_extraction(text, doc_id)
            logger.info(f"Document {doc_id}: {results[doc_id].quality_level.value} quality")
        return results

    def get_quality_report(self, metrics: ExtractionMetrics) -> Dict:
        """
        Generate detailed quality report.
        """
        return {
            "document_id": metrics.document_id,
            "quality_level": metrics.quality_level.value,
            "confidence_score": round(metrics.confidence_score, 3),
            "total_characters": metrics.total_characters,
            "detected_errors": metrics.detected_errors,
            "error_rate_percent": round((metrics.detected_errors / max(metrics.total_characters, 1)) * 100, 2),
            "error_breakdown": metrics.error_types,
            "recommendations": metrics.recommendations,
            "safe_for_embeddings": metrics.quality_level.value in ["excellent", "good"]
        }
