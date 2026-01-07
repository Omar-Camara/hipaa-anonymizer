"""
Category Tagger for PHI.

Tags detected PHI with HIPAA categories and provides metadata
for anonymization strategies.
"""

from typing import List, Dict, Optional


class CategoryTagger:
    """
    Tags PHI detections with HIPAA categories and metadata.
    
    Maps detected PHI types to the 18 HIPAA identifier categories
    and provides additional metadata for anonymization.
    """
    
    # Mapping from detected types to HIPAA categories
    HIPAA_CATEGORIES = {
        # Direct mappings
        'ssn': 'social_security_number',
        'phone': 'telephone_number',
        'fax_number': 'fax_number',
        'email': 'email_address',
        'ip': 'ip_address',
        'url': 'web_url',
        'name': 'name',
        'location': 'geographic_subdivision',
        'date': 'date',
        'organization': 'name',  # Organization names are also names
        'medical_record_number': 'medical_record_number',
        'health_plan_beneficiary_number': 'health_plan_beneficiary_number',
        'account_number': 'account_number',
        'certificate_license_number': 'certificate_license_number',
        'zip_code': 'geographic_subdivision',  # Zip codes are geographic subdivisions
    }
    
    # HIPAA Safe Harbor requirements by category
    SAFE_HARBOR_REQUIREMENTS = {
        'social_security_number': 'remove',
        'telephone_number': 'remove',
        'fax_number': 'remove',
        'email_address': 'remove',
        'ip_address': 'remove',
        'web_url': 'remove',
        'name': 'remove',
        'geographic_subdivision': 'remove_if_smaller_than_state',
        'date': 'remove_except_year',
        'medical_record_number': 'remove',
        'health_plan_beneficiary_number': 'remove',
        'account_number': 'remove',
        'certificate_license_number': 'remove',
        'zip_code': 'remove',  # Zip codes are geographic subdivisions
    }
    
    def tag(self, detections: List[Dict]) -> List[Dict]:
        """
        Tag detections with HIPAA categories and metadata.
        
        Args:
            detections: List of PHI detections.
            
        Returns:
            List of detections with added HIPAA category and metadata.
        """
        tagged = []
        
        for detection in detections:
            tagged_detection = detection.copy()
            
            # Add HIPAA category
            phi_type = detection.get('type', '').lower()
            hipaa_category = self.HIPAA_CATEGORIES.get(phi_type, 'other_unique_identifier')
            tagged_detection['hipaa_category'] = hipaa_category
            
            # Add Safe Harbor requirement
            requirement = self.SAFE_HARBOR_REQUIREMENTS.get(
                hipaa_category, 
                'remove'
            )
            tagged_detection['safe_harbor_requirement'] = requirement
            
            # Add metadata
            tagged_detection['requires_removal'] = requirement in ['remove', 'remove_if_smaller_than_state', 'remove_except_year']
            
            tagged.append(tagged_detection)
        
        return tagged
    
    def get_hipaa_category(self, phi_type: str) -> str:
        """
        Get HIPAA category for a PHI type.
        
        Args:
            phi_type: Detected PHI type.
            
        Returns:
            HIPAA category name.
        """
        return self.HIPAA_CATEGORIES.get(phi_type.lower(), 'other_unique_identifier')
    
    def requires_removal(self, detection: Dict) -> bool:
        """
        Check if detection requires removal per Safe Harbor.
        
        Args:
            detection: PHI detection dictionary.
            
        Returns:
            True if should be removed.
        """
        hipaa_category = self.get_hipaa_category(detection.get('type', ''))
        requirement = self.SAFE_HARBOR_REQUIREMENTS.get(hipaa_category, 'remove')
        return requirement in ['remove', 'remove_if_smaller_than_state', 'remove_except_year']

