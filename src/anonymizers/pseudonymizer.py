"""
Pseudonymization Module.

Provides consistent replacement of PHI with pseudonyms, allowing
the same entity to be replaced with the same pseudonym across documents.
"""

from typing import List, Dict, Optional
import hashlib
import random
import re
import string


class Pseudonymizer:
    """
    Pseudonymizes PHI by replacing it with consistent pseudonyms.
    
    The same PHI value will always be replaced with the same pseudonym,
    allowing for data analysis while maintaining privacy.
    """
    
    def __init__(self, seed: Optional[int] = None, preserve_format: bool = True):
        """
        Initialize pseudonymizer.
        
        Args:
            seed: Random seed for consistent pseudonym generation.
            preserve_format: If True, preserve format of original (e.g., phone format).
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        
        self.preserve_format = preserve_format
        self._pseudonym_cache: Dict[str, str] = {}
    
    def pseudonymize(self, text: str, detections: List[Dict]) -> str:
        """
        Pseudonymize text by replacing PHI with consistent pseudonyms.
        
        Args:
            text: Original text containing PHI.
            detections: List of PHI detections.
            
        Returns:
            Text with PHI replaced by pseudonyms.
        """
        if not detections:
            return text
        
        # Sort by start position (reverse to maintain indices)
        sorted_detections = sorted(detections, key=lambda x: x['start'], reverse=True)
        
        anonymized = text
        
        for detection in sorted_detections:
            start = detection['start']
            end = detection['end']
            phi_type = detection['type']
            value = detection['value']
            
            # Generate or retrieve pseudonym
            pseudonym = self._get_pseudonym(value, phi_type)
            
            # Replace
            anonymized = anonymized[:start] + pseudonym + anonymized[end:]
        
        return anonymized
    
    def _get_pseudonym(self, value: str, phi_type: str) -> str:
        """
        Get pseudonym for a PHI value.
        
        Args:
            value: Original PHI value.
            phi_type: Type of PHI.
            
        Returns:
            Pseudonym replacement.
        """
        # Create cache key
        cache_key = f"{phi_type}:{value}"
        
        # Return cached pseudonym if exists
        if cache_key in self._pseudonym_cache:
            return self._pseudonym_cache[cache_key]
        
        # Generate new pseudonym
        pseudonym = self._generate_pseudonym(value, phi_type)
        
        # Cache it
        self._pseudonym_cache[cache_key] = pseudonym
        
        return pseudonym
    
    def _generate_pseudonym(self, value: str, phi_type: str) -> str:
        """
        Generate a pseudonym for a PHI value.
        
        Args:
            value: Original PHI value.
            phi_type: Type of PHI.
            
        Returns:
            Generated pseudonym.
        """
        if self.preserve_format:
            return self._generate_formatted_pseudonym(value, phi_type)
        else:
            return self._generate_simple_pseudonym(phi_type)
    
    def _generate_formatted_pseudonym(self, value: str, phi_type: str) -> str:
        """Generate pseudonym that preserves original format."""
        # Use hash of value for deterministic but random-looking pseudonym
        hash_obj = hashlib.md5(value.encode())
        hash_int = int(hash_obj.hexdigest()[:8], 16)
        
        if phi_type == 'ssn':
            # Format: XXX-XX-XXXX
            part1 = str(hash_int % 900 + 100)  # 100-999
            part2 = str(hash_int % 90 + 10)     # 10-99
            part3 = str(hash_int % 9000 + 1000) # 1000-9999
            return f"{part1}-{part2}-{part3}"
        
        elif phi_type == 'phone':
            # Preserve phone format
            digits_only = re.sub(r'\D', '', value)
            if len(digits_only) == 10:
                # US format: (XXX) XXX-XXXX
                area = str(hash_int % 800 + 200)  # 200-999
                exchange = str(hash_int % 800 + 200)
                number = str(hash_int % 9000 + 1000)
                return f"({area}) {exchange}-{number}"
            else:
                # International - preserve length
                return ''.join([str((hash_int + i) % 10) for i in range(len(digits_only))])
        
        elif phi_type == 'email':
            # Format: user@domain.com
            username = self._generate_name(hash_int, length=8)
            domain = self._generate_name(hash_int + 1, length=6)
            return f"{username}@{domain}.com"
        
        elif phi_type == 'name':
            # Generate realistic name
            first = self._generate_name(hash_int, length=random.randint(4, 8))
            last = self._generate_name(hash_int + 1, length=random.randint(4, 8))
            return f"{first} {last}"
        
        elif phi_type == 'date':
            # Format: MM/DD/YYYY
            month = str((hash_int % 12) + 1).zfill(2)
            day = str((hash_int % 28) + 1).zfill(2)
            year = str(1900 + (hash_int % 100))
            return f"{month}/{day}/{year}"
        
        else:
            # Generic pseudonym
            return self._generate_simple_pseudonym(phi_type)
    
    def _generate_simple_pseudonym(self, phi_type: str) -> str:
        """Generate simple pseudonym without format preservation."""
        # Use type + random identifier
        identifier = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{phi_type.upper()}_{identifier}"
    
    def _generate_name(self, seed: int, length: int) -> str:
        """Generate a name-like string."""
        vowels = 'aeiou'
        consonants = 'bcdfghjklmnpqrstvwxyz'
        
        random.seed(seed)
        name = ''
        for i in range(length):
            if i % 2 == 0:
                name += random.choice(consonants)
            else:
                name += random.choice(vowels)
        
        return name.capitalize()
    
    def clear_cache(self):
        """Clear the pseudonym cache."""
        self._pseudonym_cache.clear()
    
    def get_cache_size(self) -> int:
        """Get number of cached pseudonyms."""
        return len(self._pseudonym_cache)

