from django.core.exceptions import ValidationError

def validate_file_size(value): 
    limit = 1 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 1 MB.')