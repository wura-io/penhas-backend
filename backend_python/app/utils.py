"""
Utility functions module
Port from Perl Penhas::Utils
100% compatible with Perl API logic
"""
import os
import re
import secrets
import string
from hashlib import sha256, md5
from typing import Optional, Tuple
from datetime import datetime
import dns.resolver
from email_validator import validate_email, EmailNotValidError


def random_string(length: int = 32) -> str:
    """
    Generate a random string of specified length
    Matches Perl's random_string from Crypt::PRNG
    """
    return secrets.token_urlsafe(length)[:length]


def random_string_from(charset: str, length: int) -> str:
    """
    Generate a random string from specified charset
    Matches Perl's random_string_from
    """
    return ''.join(secrets.choice(charset) for _ in range(length))


def is_test() -> bool:
    """
    Check if running in test environment
    Matches Perl's is_test()
    """
    return bool(os.getenv('HARNESS_ACTIVE') or os.getenv('PYTEST_CURRENT_TEST'))


def cpf_hash_with_salt(cpf: str) -> str:
    """
    Hash CPF with salt for storage
    Matches Perl's cpf_hash_with_salt
    """
    cpf_salt = os.getenv('CPF_CACHE_HASH_SALT')
    if not cpf_salt:
        raise ValueError('CPF_CACHE_HASH_SALT is not defined')
    
    combined = cpf_salt + cpf
    return sha256(combined.encode('utf-8')).hexdigest()


def is_uuid_v4(uuid_str: str) -> bool:
    """
    Check if string is a valid UUID v4
    Matches Perl's is_uuid_v4
    """
    pattern = r'^[0-9A-F]{8}-[0-9A-F]{4}-[4][0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$'
    return bool(re.match(pattern, uuid_str, re.IGNORECASE))


def time_seconds_fmt(seconds: int) -> str:
    """
    Format seconds as Xm Ys
    Matches Perl's time_seconds_fmt
    """
    minutes = (seconds // 60) % 60
    secs = seconds % 60
    return f'{minutes}m{secs:02d}s'


def trunc_to_meter(value: float) -> float:
    """
    Truncate coordinate to meter precision
    Matches Perl's trunc_to_meter for geo caching
    """
    import math
    targ = 0.00009
    return targ * math.ceil((value - 0.50000000000008 * targ) / targ)


def pg_timestamp2iso_8601(timestamp: str) -> str:
    """
    Convert PostgreSQL timestamp to ISO 8601 format
    Matches Perl's pg_timestamp2iso_8601
    """
    timestamp = timestamp.replace(' ', 'T')
    timestamp = re.sub(r'\+.+$', '', timestamp)
    timestamp = re.sub(r'\..+$', '', timestamp)
    timestamp += 'Z'
    return timestamp


def pg_timestamp2iso_8601_second(timestamp: str) -> str:
    """
    Convert PostgreSQL timestamp to ISO 8601 format (without Z)
    Matches Perl's pg_timestamp2iso_8601_second
    """
    timestamp = timestamp.replace(' ', 'T')
    timestamp = re.sub(r'\+.+$', '', timestamp)
    timestamp = re.sub(r'\..+$', '', timestamp)
    return timestamp


def db_epoch_to_etag(timestamp: str) -> str:
    """
    Convert database timestamp to ETag
    Matches Perl's db_epoch_to_etag
    """
    # Remove timezone
    timestamp = re.sub(r'\+\d+$', '', timestamp)
    
    # Validate format
    pattern = r'^2\d{3}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}(\.\d{1,8})?$'
    if not re.match(pattern, timestamp):
        raise ValueError(f"{timestamp} is not in expected format")
    
    return md5(timestamp.encode('utf-8')).hexdigest()[:6]


def notifications_enabled() -> bool:
    """
    Check if notifications are enabled
    Matches Perl's notifications_enabled
    """
    return bool(os.getenv('NOTIFICATIONS_ENABLED', '0') == '1')


class PasswordValidationError(Exception):
    """Custom exception for password validation errors"""
    def __init__(self, error: str, message: str, field: str = 'senha', reason: str = 'invalid'):
        self.error = error
        self.message = message
        self.field = field
        self.reason = reason
        super().__init__(message)


def check_password_or_die(password: str) -> None:
    """
    Validate password strength
    Matches Perl's check_password_or_die
    Raises PasswordValidationError if invalid
    """
    if not password or password.startswith(' ') or password.endswith(' '):
        raise PasswordValidationError(
            'warning_space_password',
            'A senha não pode iniciar ou terminar com espaço'
        )
    
    # Check for weak passwords
    weak_patterns = [r'^12345', r'^picture1$', r'^password$', r'^111111', r'^123123', r'^senha$']
    for pattern in weak_patterns:
        if re.match(pattern, password, re.IGNORECASE):
            raise PasswordValidationError(
                'pass_too_weak',
                'A senha utilizada é muito simples, utilize uma senha melhor.'
            )
    
    txt = 'É necessário pelo menos 8 caracteres, pelo menos 1 letra, 1 número, e 1 carácter especial'
    
    if len(password) < 8:
        raise PasswordValidationError(
            'pass_too_weak/size',
            f'A senha utilizada é muito curta! {txt}'
        )
    
    if not re.search(r'[0-9]', password):
        raise PasswordValidationError(
            'pass_too_weak/number',
            f'A senha utilizada não usou números! {txt}'
        )
    
    if not re.search(r'[A-Z]', password, re.IGNORECASE):
        raise PasswordValidationError(
            'pass_too_weak/letter',
            f'A senha utilizada não usou letras! {txt}'
        )
    
    if not re.search(r'[^0-9A-Z]', password, re.IGNORECASE):
        raise PasswordValidationError(
            'pass_too_weak/char',
            f'A senha utilizada não usou caracteres especiais! {txt}'
        )


def linkfy(text: str) -> str:
    """
    Convert URLs in text to HTML links
    Matches Perl's linkfy
    """
    def replace_url(match):
        href = match.group(1)
        if not href.startswith('http'):
            href = f'https://{href}'
        return f'<a href="{href}">{match.group(1)}</a>'
    
    pattern = r'(https?://(?:www\.|(?!www))[^\s.]+\.[^\s]{2,}|www\.[^\s]+\.[^\s]{2,})'
    return re.sub(pattern, replace_url, text)


def nl2br(text: str) -> str:
    """
    Convert newlines to HTML <br/> tags
    Matches Perl's nl2br
    """
    text = re.sub(r'(\r\n|\n\r|\n|\r)', r' <br/> \1', text)
    text = text.replace('  ', ' &nbsp;&nbsp; ')
    return text


def check_email_mx(email: str) -> bool:
    """
    Check if email domain has valid MX records
    Matches Perl's check_email_mx
    """
    # Common domains don't need MX check
    common_domains = [
        '@gmail.com', '@hotmail.com', '@icloud.com', '@outlook.com',
        '@msn.com', '@live.com', '@globo.com',
        '@terra.com.br', '@uol.com.br', '@yahoo.com.br',
        '@outlook.com.br', '@bol.com.br'
    ]
    
    if is_test():
        return True
    
    email_lower = email.lower()
    for domain in common_domains:
        if email_lower.endswith(domain):
            return True
    
    # Validate email format and check MX
    try:
        # Validate email format
        validate_email(email, check_deliverability=False)
        
        # Extract domain
        domain = email.split('@')[1]
        
        # Check MX records
        try:
            dns.resolver.resolve(domain, 'MX')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return False
    except EmailNotValidError:
        return False


def test_cpf(cpf: str) -> bool:
    """
    Validate Brazilian CPF
    Matches Perl's Business::BR::CPF::test_cpf
    """
    # Remove non-digits
    cpf = re.sub(r'[^\d]', '', cpf)
    
    # Check length
    if len(cpf) != 11:
        return False
    
    # Check for known invalid CPFs (all same digit)
    if cpf == cpf[0] * 11:
        return False
    
    # Calculate first check digit
    sum_val = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = 11 - (sum_val % 11)
    if digit1 >= 10:
        digit1 = 0
    
    if int(cpf[9]) != digit1:
        return False
    
    # Calculate second check digit
    sum_val = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = 11 - (sum_val % 11)
    if digit2 >= 10:
        digit2 = 0
    
    if int(cpf[10]) != digit2:
        return False
    
    return True


def remove_pi(content: str) -> str:
    """
    Remove personal information (PI) from content
    Masks phone numbers, emails, CPFs, and UUIDs
    Matches Perl's remove_pi
    """
    # Replace phone numbers (Brazilian format)
    def replace_number(match):
        content = match.group(1)
        if '0800' in content:
            return content
        return re.sub(r'\d', '*', content)
    
    # Phone pattern (Brazilian area codes and numbers)
    phone_pattern = r'((?:\(?(11|12|13|14|15|16|17|18|19|21|22|24|27|28|31|32|33|34|35|37|38|41|42|43|44|45|46|47|48|49|51|53|54|55|61|62|63|64|65|66|67|68|69|71|73|74|75|77|79|81|82|83|84|85|86|87|88|89|91|92|93|94|95|96|97|98|99)\)?\s*)?[^\d]{0,3}(?:11|12|13|14|15|16|17|18|19|21|22|24|27|28|31|32|33|34|35|37|38|41|42|43|44|45|46|47|48|49|51|53|54|55|61|62|63|64|65|66|67|68|69|71|73|74|75|77|79|81|82|83|84|85|86|87|88|89|91|92|93|94|95|96|97|98|99)?\d{4,5}[^\d]?\d{4,10}[^\d]{0,3})'
    content = re.sub(phone_pattern, lambda m: replace_number(m), content)
    
    # Replace emails
    def replace_chars(match):
        return re.sub(r'[\d\w0-9]', '*', match.group(1))
    
    email_pattern = r'(\w+(?:[-+.\']\w+)*@\w+(?:[-.]\w+)*\.\w+(?:[-.]\w+)*)'
    content = re.sub(email_pattern, lambda m: replace_chars(m), content)
    
    # Replace CPFs
    def check_cpf(match):
        cpf_candidate = match.group(1)
        only_digits = re.sub(r'[^\d]', '', cpf_candidate)
        if test_cpf(only_digits):
            return re.sub(r'[0-9]', '*', cpf_candidate)
        return cpf_candidate
    
    cpf_pattern = r'(\d(?:[\w\s\.\-\*]{1,4}\d){1,5})\b'
    content = re.sub(cpf_pattern, lambda m: check_cpf(m), content)
    
    # Replace UUIDs
    content = re.sub(r'[\w]{8}(-[\w]{4}){3}-[\w]{12}', '*******-****-****-****-************', content)
    
    return content


def get_semver_numeric(user_agent: str) -> Optional[Tuple[str, int]]:
    """
    Extract OS and numeric version from user agent
    Matches Perl's get_semver_numeric
    Returns (os, numeric_version) or None
    """
    pattern = r'((Android|iOS)\s[^\/]+\/[^\/\"]+\/([^\/\"]+))'
    match = re.search(pattern, user_agent)
    
    if match:
        os_name = match.group(2)
        version = match.group(3)
        
        parts = version.split('.')
        if len(parts) >= 3:
            try:
                major = int(parts[0])
                minor = int(parts[1])
                patch = int(parts[2])
                
                super_number = (major * 1_000_000_000) + (minor * 1_000_000) + patch
                return (os_name, super_number)
            except ValueError:
                pass
    
    return None


def is_legacy_app(os_name: Optional[str], numeric_version: Optional[int]) -> bool:
    """
    Check if app version is legacy (< 3.6.0)
    Matches Perl's is_legacy_app
    """
    if not os_name or not numeric_version:
        return False
    
    # Android and iOS both use same threshold: 3.6.0 => 3006000000
    if os_name in ('Android', 'iOS'):
        return numeric_version < 3006000000
    
    return False


def filename_cache_three(filename: str) -> str:
    """
    Generate three-level cache directory structure from filename
    Matches Perl's filename_cache_three
    Example: 'abcdefgh' -> 'ab/cd/efg'
    """
    if len(filename) < 7:
        return filename
    
    return f"{filename[:2]}/{filename[2:4]}/{filename[4:7]}"


def get_media_filepath(filename: str) -> str:
    """
    Get full filepath for media file with cache directory structure
    Matches Perl's get_media_filepath
    """
    media_cache_dir = os.getenv('MEDIA_CACHE_DIR', '/tmp/media')
    path = os.path.join(media_cache_dir, filename_cache_three(filename))
    
    # Create directory if it doesn't exist
    os.makedirs(path, exist_ok=True)
    
    return os.path.join(path, filename)

