class ValidationResult:
    def __init__(self, is_valid: bool, errors: list[str]):
        self.is_valid = is_valid
        self.errors = errors

    def __str__(self):
        return f"ValidationResult(is_valid={self.is_valid}, errors={self.errors})"
