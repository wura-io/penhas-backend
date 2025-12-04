"""
Encryption utilities
Port from Perl Penhas::CryptCBC2x
Provides CBC mode encryption compatible with Perl's Crypt::CBC
"""
from Crypto.Cipher import AES, DES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import hashlib
import base64
from typing import Optional, Tuple, Callable


class CryptCBC:
    """
    CBC mode encryption/decryption
    Compatible with Perl's Crypt::CBC for guardian token encryption
    """
    
    # Padding methods
    PADDING_STANDARD = 'standard'
    PADDING_NULL = 'null'
    PADDING_SPACE = 'space'
    PADDING_NONE = 'none'
    
    # Header modes
    HEADER_SALT = 'salt'
    HEADER_RANDOMIV = 'randomiv'
    HEADER_NONE = 'none'
    
    def __init__(
        self,
        passphrase: str,
        cipher: str = 'DES',
        header_mode: str = HEADER_SALT,
        padding: str = PADDING_STANDARD,
        keysize: Optional[int] = None,
        blocksize: Optional[int] = None,
        iv: Optional[bytes] = None,
        salt: Optional[bytes] = None
    ):
        """
        Initialize encryption
        
        Args:
            passphrase: Encryption passphrase
            cipher: Cipher algorithm ('DES' or 'AES')
            header_mode: Header mode (salt, randomiv, none)
            padding: Padding method
            keysize: Key size in bytes (default: cipher default)
            blocksize: Block size in bytes (default: cipher default)
            iv: Initialization vector (optional)
            salt: Salt for key derivation (optional)
        """
        self.passphrase = passphrase
        self.header_mode = header_mode
        self.padding_method = padding
        self.iv = iv
        self.salt = salt
        
        # Set cipher defaults
        if cipher.upper() == 'AES':
            self.cipher_class = AES
            self.keysize = keysize or 32  # AES-256
            self.blocksize = blocksize or 16
        elif cipher.upper() == 'DES':
            self.cipher_class = DES
            self.keysize = keysize or 8
            self.blocksize = blocksize or 8
        else:
            raise ValueError(f"Unsupported cipher: {cipher}")
        
        # Validate IV length if provided
        if self.iv and len(self.iv) != self.blocksize:
            raise ValueError(f"IV must be {self.blocksize} bytes long")
        
        # Validate salt length if provided
        if self.salt and len(self.salt) != 8:
            raise ValueError("Salt must be 8 bytes long")
    
    def _pad_standard(self, data: bytes) -> bytes:
        """PKCS#7 padding"""
        pad_length = self.blocksize - (len(data) % self.blocksize)
        return data + bytes([pad_length] * pad_length)
    
    def _unpad_standard(self, data: bytes) -> bytes:
        """Remove PKCS#7 padding"""
        if not data:
            return data
        pad_length = data[-1]
        if pad_length > self.blocksize or pad_length == 0:
            return data
        # Verify all padding bytes are correct
        if all(b == pad_length for b in data[-pad_length:]):
            return data[:-pad_length]
        return data
    
    def _pad_null(self, data: bytes) -> bytes:
        """Null byte padding"""
        pad_length = self.blocksize - (len(data) % self.blocksize)
        return data + b'\x00' * pad_length
    
    def _unpad_null(self, data: bytes) -> bytes:
        """Remove null byte padding"""
        return data.rstrip(b'\x00')
    
    def _pad_space(self, data: bytes) -> bytes:
        """Space padding"""
        pad_length = self.blocksize - (len(data) % self.blocksize)
        return data + b' ' * pad_length
    
    def _unpad_space(self, data: bytes) -> bytes:
        """Remove space padding"""
        return data.rstrip(b' ')
    
    def _pad(self, data: bytes) -> bytes:
        """Apply padding based on padding method"""
        if self.padding_method == self.PADDING_STANDARD:
            return self._pad_standard(data)
        elif self.padding_method == self.PADDING_NULL:
            return self._pad_null(data)
        elif self.padding_method == self.PADDING_SPACE:
            return self._pad_space(data)
        elif self.padding_method == self.PADDING_NONE:
            if len(data) % self.blocksize != 0:
                raise ValueError("Data length must be multiple of block size when using no padding")
            return data
        else:
            raise ValueError(f"Unknown padding method: {self.padding_method}")
    
    def _unpad(self, data: bytes) -> bytes:
        """Remove padding based on padding method"""
        if self.padding_method == self.PADDING_STANDARD:
            return self._unpad_standard(data)
        elif self.padding_method == self.PADDING_NULL:
            return self._unpad_null(data)
        elif self.padding_method == self.PADDING_SPACE:
            return self._unpad_space(data)
        elif self.padding_method == self.PADDING_NONE:
            return data
        else:
            raise ValueError(f"Unknown padding method: {self.padding_method}")
    
    def _key_from_passphrase(self, passphrase: str) -> bytes:
        """
        Derive key from passphrase using MD5 (matches Perl's method)
        """
        material = hashlib.md5(passphrase.encode()).digest()
        while len(material) < self.keysize:
            material += hashlib.md5(material).digest()
        return material[:self.keysize]
    
    def _salted_key_and_iv(self, passphrase: str, salt: bytes) -> Tuple[bytes, bytes]:
        """
        Derive key and IV from passphrase and salt (matches Perl's method)
        Uses OpenSSL's EVP_BytesToKey algorithm
        """
        if len(salt) != 8:
            raise ValueError("Salt must be 8 bytes long")
        
        desired_len = self.keysize + self.blocksize
        data = b''
        d = b''
        
        while len(data) < desired_len:
            d = hashlib.md5(d + passphrase.encode() + salt).digest()
            data += d
        
        key = data[:self.keysize]
        iv = data[self.keysize:self.keysize + self.blocksize]
        
        return key, iv
    
    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypt data
        
        Args:
            plaintext: Data to encrypt (bytes)
            
        Returns:
            Encrypted data with header (bytes)
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()
        
        # Generate salt/IV and header
        if self.header_mode == self.HEADER_SALT:
            salt = self.salt or get_random_bytes(8)
            key, iv = self._salted_key_and_iv(self.passphrase, salt)
            header = b'Salted__' + salt
        elif self.header_mode == self.HEADER_RANDOMIV:
            if self.blocksize != 8:
                raise ValueError("RandomIV mode requires 8-byte block cipher")
            key = self._key_from_passphrase(self.passphrase)
            iv = self.iv or get_random_bytes(8)
            header = b'RandomIV' + iv
        elif self.header_mode == self.HEADER_NONE:
            if not self.iv:
                raise ValueError("IV must be provided when using header_mode='none'")
            key = self._key_from_passphrase(self.passphrase)
            iv = self.iv
            header = b''
        else:
            raise ValueError(f"Invalid header mode: {self.header_mode}")
        
        # Pad plaintext
        padded_data = self._pad(plaintext)
        
        # Encrypt using CBC mode
        cipher = self.cipher_class.new(key, self.cipher_class.MODE_CBC, iv)
        ciphertext = cipher.encrypt(padded_data)
        
        return header + ciphertext
    
    def decrypt(self, ciphertext: bytes) -> bytes:
        """
        Decrypt data
        
        Args:
            ciphertext: Encrypted data with header (bytes)
            
        Returns:
            Decrypted plaintext (bytes)
        """
        # Parse header and extract key/IV
        if self.header_mode == self.HEADER_SALT:
            if not ciphertext.startswith(b'Salted__'):
                raise ValueError("Invalid ciphertext header for 'salt' mode")
            salt = ciphertext[8:16]
            ciphertext = ciphertext[16:]
            key, iv = self._salted_key_and_iv(self.passphrase, salt)
        elif self.header_mode == self.HEADER_RANDOMIV:
            if not ciphertext.startswith(b'RandomIV'):
                raise ValueError("Invalid ciphertext header for 'randomiv' mode")
            iv = ciphertext[8:16]
            ciphertext = ciphertext[16:]
            key = self._key_from_passphrase(self.passphrase)
        elif self.header_mode == self.HEADER_NONE:
            if not self.iv:
                raise ValueError("IV must be provided when using header_mode='none'")
            key = self._key_from_passphrase(self.passphrase)
            iv = self.iv
        else:
            raise ValueError(f"Invalid header mode: {self.header_mode}")
        
        # Decrypt using CBC mode
        cipher = self.cipher_class.new(key, self.cipher_class.MODE_CBC, iv)
        padded_data = cipher.decrypt(ciphertext)
        
        # Remove padding
        plaintext = self._unpad(padded_data)
        
        return plaintext
    
    def encrypt_hex(self, plaintext: bytes) -> str:
        """Encrypt and return as hex string"""
        return self.encrypt(plaintext).hex()
    
    def decrypt_hex(self, hex_string: str) -> bytes:
        """Decrypt from hex string"""
        return self.decrypt(bytes.fromhex(hex_string))
    
    def encrypt_base64(self, plaintext: bytes) -> str:
        """Encrypt and return as base64 string"""
        return base64.b64encode(self.encrypt(plaintext)).decode()
    
    def decrypt_base64(self, b64_string: str) -> bytes:
        """Decrypt from base64 string"""
        return self.decrypt(base64.b64decode(b64_string))


def encrypt_guardian_token(token: str, passphrase: str) -> str:
    """
    Encrypt guardian token
    Matches Perl's guardian token encryption
    """
    cbc = CryptCBC(
        passphrase=passphrase,
        cipher='DES',
        header_mode=CryptCBC.HEADER_SALT
    )
    return cbc.encrypt_hex(token.encode())


def decrypt_guardian_token(encrypted_hex: str, passphrase: str) -> str:
    """
    Decrypt guardian token
    Matches Perl's guardian token decryption
    """
    cbc = CryptCBC(
        passphrase=passphrase,
        cipher='DES',
        header_mode=CryptCBC.HEADER_SALT
    )
    return cbc.decrypt_hex(encrypted_hex).decode()

