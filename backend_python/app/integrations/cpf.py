"""
CPF validation service
Port from Perl Penhas::Helpers::CPF
Integrates with iWebService API for CPF validation
"""
import httpx
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.config import settings
from app.models.onboarding import CpfErro


class CPFValidationService:
    """
    CPF validation using iWebService API
    Matches Perl's Penhas::Helpers::CPF
    """
    
    def __init__(self):
        self.api_token = settings.IWEBSERVICE_CPF_TOKEN or settings.IWEB_SERVICE_CHAVE
        self.api_url = "https://ws.iwebservice.com.br/consultacpf"
        self.timeout = 30
    
    async def validate_cpf(
        self,
        db: AsyncSession,
        cpf: str,
        nome: str,
        dt_nasc: str
    ) -> Dict[str, Any]:
        """
        Validate CPF with name and birth date using iWebService
        
        Args:
            cpf: CPF number (only digits)
            nome: Full name
            dt_nasc: Birth date in YYYY-MM-DD format
            
        Returns:
            Dict with validation result:
            - valid: bool
            - status: str (valid, invalid, error, etc.)
            - message: str
        """
        if not self.api_token:
            return {
                "valid": False,
                "status": "no_api_token",
                "message": "CPF validation service not configured"
            }
        
        # Clean CPF (only digits)
        cpf_clean = "".join(filter(str.isdigit, cpf))
        
        if len(cpf_clean) != 11:
            return {
                "valid": False,
                "status": "invalid_format",
                "message": "CPF deve conter 11 dígitos"
            }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.api_url,
                    params={
                        "token": self.api_token,
                        "cpf": cpf_clean,
                        "nome": nome,
                        "nasc": dt_nasc  # Format: YYYY-MM-DD or DD/MM/YYYY
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse iWebService response
                # Expected format: {"Status": "OK", "Situacao": "Regular", ...}
                status = data.get("Status", "").upper()
                situacao = data.get("Situacao", "").upper()
                
                if status == "OK" and situacao == "REGULAR":
                    return {
                        "valid": True,
                        "status": "valid",
                        "message": "CPF válido"
                    }
                elif status == "ERRO":
                    error_msg = data.get("Mensagem", "Erro desconhecido")
                    
                    # Log error to database
                    await self._log_cpf_error(
                        db=db,
                        cpf=cpf_clean,
                        nome=nome,
                        dt_nasc=dt_nasc,
                        error_message=error_msg,
                        api_response=data
                    )
                    
                    return {
                        "valid": False,
                        "status": "invalid",
                        "message": error_msg
                    }
                else:
                    # Unknown status
                    await self._log_cpf_error(
                        db=db,
                        cpf=cpf_clean,
                        nome=nome,
                        dt_nasc=dt_nasc,
                        error_message=f"Status desconhecido: {status}",
                        api_response=data
                    )
                    
                    return {
                        "valid": False,
                        "status": "unknown",
                        "message": "Não foi possível validar o CPF"
                    }
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error: {e.response.status_code}"
            await self._log_cpf_error(
                db=db,
                cpf=cpf_clean,
                nome=nome,
                dt_nasc=dt_nasc,
                error_message=error_msg,
                api_response={"http_error": str(e)}
            )
            
            return {
                "valid": False,
                "status": "api_error",
                "message": "Erro ao validar CPF (serviço temporariamente indisponível)"
            }
            
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            await self._log_cpf_error(
                db=db,
                cpf=cpf_clean,
                nome=nome,
                dt_nasc=dt_nasc,
                error_message=error_msg,
                api_response={"request_error": str(e)}
            )
            
            return {
                "valid": False,
                "status": "network_error",
                "message": "Erro de rede ao validar CPF"
            }
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            await self._log_cpf_error(
                db=db,
                cpf=cpf_clean,
                nome=nome,
                dt_nasc=dt_nasc,
                error_message=error_msg,
                api_response={"exception": str(e)}
            )
            
            return {
                "valid": False,
                "status": "error",
                "message": "Erro inesperado ao validar CPF"
            }
    
    async def _log_cpf_error(
        self,
        db: AsyncSession,
        cpf: str,
        nome: str,
        dt_nasc: str,
        error_message: str,
        api_response: Dict[str, Any]
    ) -> None:
        """
        Log CPF validation errors to database
        Matches Perl's cpf_erro table logging
        """
        import json
        
        cpf_erro = CpfErro(
            cpf=cpf,
            nome=nome,
            dt_nasc=dt_nasc,
            error_message=error_message,
            api_response=json.dumps(api_response),
            created_at=datetime.utcnow()
        )
        db.add(cpf_erro)
        try:
            await db.commit()
        except Exception as e:
            print(f"Error logging CPF error: {e}")
            await db.rollback()
    
    def validate_cpf_format(self, cpf: str) -> bool:
        """
        Basic CPF format validation (checksum)
        Doesn't check with external API
        """
        # Clean CPF
        cpf_clean = "".join(filter(str.isdigit, cpf))
        
        if len(cpf_clean) != 11:
            return False
        
        # Check for all same digits (invalid)
        if cpf_clean == cpf_clean[0] * 11:
            return False
        
        # Calculate checksum digits
        def calculate_digit(cpf_partial: str) -> str:
            total = 0
            for i, digit in enumerate(cpf_partial):
                total += int(digit) * (len(cpf_partial) + 1 - i)
            remainder = total % 11
            return '0' if remainder < 2 else str(11 - remainder)
        
        # Validate first digit
        first_digit = calculate_digit(cpf_clean[:9])
        if first_digit != cpf_clean[9]:
            return False
        
        # Validate second digit
        second_digit = calculate_digit(cpf_clean[:10])
        if second_digit != cpf_clean[10]:
            return False
        
        return True


# Singleton instance
cpf_validation_service = CPFValidationService()

