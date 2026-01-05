"""
Safe Harbor Anonymization Method.

Implements HIPAA Safe Harbor de-identification method which requires
removal of 18 specified identifiers or replacing them with generic placeholders.
"""

from typing import List, Dict, Optional
import re


class SafeHarborAnonymizer:
    """
    Implements HIPAA Safe Harbor de-identification method.
    
    Safe Harbor requires removal or replacement of 18 specified identifiers:
    1. Names
    2. Geographic subdivisions smaller than state
    3. Dates (except year)
    4. Telephone numbers
    5. Fax numbers
    6. Email addresses
    7. Social Security Numbers
    8. Medical record numbers
    9. Health plan beneficiary numbers
    10. Account numbers
    11. Certificate/license numbers
    12. Vehicle identifiers
    13. Device identifiers
    14. Web URLs
    15. IP addresses
    16. Biometric identifiers
    17. Full face photos
    18. Any other unique identifier
    """
    
    # Default replacement patterns by PHI type
    REPLACEMENTS = {
        'ssn': '[SSN]',
        'phone': '[PHONE]',
        'email': '[EMAIL]',
        'ip': '[IP_ADDRESS]',
        'url': '[URL]',
        'name': '[NAME]',
        'location': '[LOCATION]',
        'date': '[DATE]',
        'organization': '[ORGANIZATION]',
        'medical_record_number': '[MRN]',
        'account_number': '[ACCOUNT]',
    }
    
    def __init__(self, replacement_map: Optional[Dict[str, str]] = None):
        """
        Initialize Safe Harbor anonymizer.
        
        Args:
            replacement_map: Custom replacement patterns. If None, uses defaults.
        """
        self.replacement_map = replacement_map or self.REPLACEMENTS.copy()
    
    def anonymize(self, text: str, detections: List[Dict]) -> str:
        """
        Anonymize text using Safe Harbor method.
        
        Args:
            text: Original text containing PHI.
            detections: List of PHI detections from pipeline.
            
        Returns:
            Anonymized text with PHI replaced by placeholders.
        """
        if not detections:
            return text
        
        # Sort detections by start position (reverse to maintain indices)
        sorted_detections = sorted(detections, key=lambda x: x['start'], reverse=True)
        
        anonymized = text
        
        for detection in sorted_detections:
            start = detection['start']
            end = detection['end']
            phi_type = detection['type']
            
            # Get replacement text
            replacement = self._get_replacement(phi_type)
            
            # Replace the detected PHI
            anonymized = anonymized[:start] + replacement + anonymized[end:]
        
        return anonymized
    
    def _get_replacement(self, phi_type: str) -> str:
        """
        Get replacement text for a PHI type.
        
        Args:
            phi_type: Type of PHI (ssn, phone, email, etc.)
            
        Returns:
            Replacement text.
        """
        # Normalize type
        phi_type = phi_type.lower()
        
        # Direct mapping
        if phi_type in self.replacement_map:
            return self.replacement_map[phi_type]
        
        # Fallback to generic
        return f'[{phi_type.upper()}]'
    
    def anonymize_with_redaction(self, text: str, detections: List[Dict]) -> str:
        """
        Anonymize by redacting (removing) PHI entirely.
        
        Args:
            text: Original text containing PHI.
            detections: List of PHI detections.
            
        Returns:
            Text with PHI removed.
        """
        if not detections:
            return text
        
        # Sort by start position (reverse to maintain indices)
        sorted_detections = sorted(detections, key=lambda x: x['start'], reverse=True)
        
        anonymized = text
        
        for detection in sorted_detections:
            start = detection['start']
            end = detection['end']
            
            # Remove the PHI (replace with empty string)
            anonymized = anonymized[:start] + anonymized[end:]
        
        return anonymized
    
    def anonymize_with_tags(self, text: str, detections: List[Dict]) -> str:
        """
        Anonymize by replacing PHI with tagged placeholders.
        
        Args:
            text: Original text containing PHI.
            detections: List of PHI detections.
            
        Returns:
            Text with PHI replaced by tagged placeholders like [NAME:1], [SSN:2]
        """
        if not detections:
            return text
        
        # Sort by start position (reverse to maintain indices)
        sorted_detections = sorted(detections, key=lambda x: x['start'], reverse=True)
        
        anonymized = text
        type_counts = {}
        
        for detection in sorted_detections:
            start = detection['start']
            end = detection['end']
            phi_type = detection['type']
            
            # Count occurrences of this type
            type_counts[phi_type] = type_counts.get(phi_type, 0) + 1
            count = type_counts[phi_type]
            
            # Create tagged replacement
            replacement = f'[{phi_type.upper()}:{count}]'
            
            # Replace
            anonymized = anonymized[:start] + replacement + anonymized[end:]
        
        return anonymized

