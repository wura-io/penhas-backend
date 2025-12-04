"""
CEP (Brazilian ZIP code) lookup services
Port from Perl Penhas::CEP
Supports multiple providers: ViaCep, Postmon, Correios
"""
import re
import httpx
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class CEPResult(Dict[str, Any]):
    """CEP lookup result matching Perl format"""
    pass


class CEPProvider(ABC):
    """Base class for CEP providers"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
    
    @abstractmethod
    async def find(self, cep: str) -> Optional[CEPResult]:
        """Find address by CEP"""
        pass


class ViaCep(CEPProvider):
    """
    ViaCep provider
    Port from Penhas::CEP::ViaCep
    """
    
    @property
    def name(self) -> str:
        return "ViaCep"
    
    async def find(self, cep: str) -> Optional[CEPResult]:
        """
        Lookup CEP using ViaCep API
        Returns dict with street, city, district, state, ibge
        """
        url = f"https://viacep.com.br/ws/{cep}/json/"
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url)
                
                if not response.is_success:
                    return None
                
                data = response.json()
                
                # ViaCep returns {"erro": true} if CEP not found
                if data.get('erro'):
                    return None
                
                return CEPResult({
                    'street': data.get('logradouro', ''),
                    'city': data.get('localidade', ''),
                    'district': data.get('bairro', ''),
                    'state': data.get('uf', ''),
                    'ibge': data.get('ibge', '')
                })
        except Exception:
            return None


class Postmon(CEPProvider):
    """
    Postmon provider
    Port from Penhas::CEP::Postmon
    """
    
    @property
    def name(self) -> str:
        return "Postmon"
    
    async def find(self, cep: str) -> Optional[CEPResult]:
        """
        Lookup CEP using Postmon API
        Returns dict with street, city, district, state
        """
        url = f"https://api.postmon.com.br/v1/cep/{cep}"
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url)
                
                if not response.is_success:
                    return None
                
                data = response.json()
                
                return CEPResult({
                    'street': data.get('logradouro', ''),
                    'city': data.get('cidade', ''),
                    'district': data.get('bairro', ''),
                    'state': data.get('estado', ''),
                    'ibge': data.get('cidade_info', {}).get('codigo_ibge', '')
                })
        except Exception:
            return None


class Correios(CEPProvider):
    """
    Correios provider (via BrasilAPI)
    Port from Penhas::CEP::Correios
    """
    
    @property
    def name(self) -> str:
        return "Correios"
    
    async def find(self, cep: str) -> Optional[CEPResult]:
        """
        Lookup CEP using BrasilAPI (Correios data)
        Returns dict with street, city, district, state
        """
        url = f"https://brasilapi.com.br/api/cep/v1/{cep}"
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url)
                
                if not response.is_success:
                    return None
                
                data = response.json()
                
                return CEPResult({
                    'street': data.get('street', ''),
                    'city': data.get('city', ''),
                    'district': data.get('neighborhood', ''),
                    'state': data.get('state', ''),
                    'ibge': ''
                })
        except Exception:
            return None


class CEPService:
    """
    CEP lookup service with multiple providers
    Port from Penhas::CEP behavior
    Tries providers in order: ViaCep, Postmon, Correios
    """
    
    def __init__(self):
        self.providers = [
            ViaCep(),
            Postmon(),
            Correios()
        ]
    
    def clean_cep(self, cep: str) -> str:
        """Remove non-numeric characters from CEP"""
        return re.sub(r'[^0-9]', '', cep)
    
    async def find(self, cep: str) -> Optional[CEPResult]:
        """
        Find address by CEP, trying multiple providers
        Matches Perl behavior: tries ViaCep, then Postmon, then Correios
        Returns first successful result with complete address fields
        """
        # Clean CEP
        cep_clean = self.clean_cep(cep)
        
        if len(cep_clean) != 8:
            return None
        
        # Try each provider in order
        for provider in self.providers:
            try:
                result = await provider.find(cep_clean)
                
                if result:
                    # Check if result has required fields (city and state minimum)
                    if result.get('city') and result.get('state'):
                        return result
            except Exception:
                # Continue to next provider on error
                continue
        
        return None


# Global service instance
_cep_service: Optional[CEPService] = None


def get_cep_service() -> CEPService:
    """Get CEP service singleton"""
    global _cep_service
    if _cep_service is None:
        _cep_service = CEPService()
    return _cep_service

