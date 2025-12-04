"""
Media processing utilities
Audio waveform extraction and image optimization
"""
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class MediaProcessor:
    """
    Media processing utilities
    Matches Perl's media processing functionality
    """
    
    @staticmethod
    async def extract_audio_waveform(
        audio_file_path: str,
        output_format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Extract waveform data from audio file using audiowaveform
        
        Args:
            audio_file_path: Path to audio file
            output_format: 'json' or 'dat'
            
        Returns:
            Dict with waveform data or error
        """
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as tmp:
                output_path = tmp.name
            
            # Run audiowaveform command
            # Install: apt-get install audiowaveform
            cmd = [
                'audiowaveform',
                '-i', audio_file_path,
                '-o', output_path,
                '--output-format', output_format,
                '--pixels-per-second', '20',
                '--bits', '8'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"audiowaveform failed: {result.stderr}"
                }
            
            # Read waveform data
            with open(output_path, 'r' if output_format == 'json' else 'rb') as f:
                waveform_data = f.read()
            
            # Cleanup
            os.unlink(output_path)
            
            return {
                "success": True,
                "waveform_data": waveform_data,
                "format": output_format
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "error": "audiowaveform not installed. Run: apt-get install audiowaveform"
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Waveform extraction timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    @staticmethod
    async def get_audio_duration(
        audio_file_path: str
    ) -> Optional[float]:
        """
        Get audio duration in seconds using ffmpeg
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Duration in seconds or None if error
        """
        try:
            # Use ffprobe (part of ffmpeg) to get duration
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            try:
                duration = float(result.stdout.strip())
                return duration
            except ValueError:
                return None
                
        except FileNotFoundError:
            print("ffprobe not installed. Run: apt-get install ffmpeg")
            return None
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return None
    
    @staticmethod
    async def convert_audio_format(
        input_path: str,
        output_path: str,
        output_format: str = 'aac',
        bitrate: str = '128k'
    ) -> Dict[str, Any]:
        """
        Convert audio to different format using ffmpeg
        
        Args:
            input_path: Input audio file path
            output_path: Output file path
            output_format: Output format (aac, mp3, wav, etc.)
            bitrate: Audio bitrate (e.g., '128k', '256k')
            
        Returns:
            Dict with success status
        """
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:a', 'aac' if output_format == 'aac' else 'libmp3lame',
                '-b:a', bitrate,
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"ffmpeg failed: {result.stderr}"
                }
            
            return {
                "success": True,
                "output_path": output_path
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "error": "ffmpeg not installed. Run: apt-get install ffmpeg"
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Audio conversion timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    @staticmethod
    async def optimize_image(
        input_path: str,
        output_path: str,
        max_width: int = 1920,
        max_height: int = 1080,
        quality: int = 85
    ) -> Dict[str, Any]:
        """
        Optimize and resize image using Pillow
        
        Args:
            input_path: Input image path
            output_path: Output image path
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            quality: JPEG quality (1-100)
            
        Returns:
            Dict with success status and image info
        """
        try:
            from PIL import Image
            
            with Image.open(input_path) as img:
                # Get original size
                original_size = img.size
                
                # Calculate new size maintaining aspect ratio
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Convert RGBA to RGB if saving as JPEG
                if img.mode == 'RGBA' and output_path.lower().endswith(('.jpg', '.jpeg')):
                    # Create white background
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                    img = rgb_img
                
                # Save optimized image
                save_kwargs = {}
                if output_path.lower().endswith(('.jpg', '.jpeg')):
                    save_kwargs = {'quality': quality, 'optimize': True}
                elif output_path.lower().endswith('.png'):
                    save_kwargs = {'optimize': True}
                
                img.save(output_path, **save_kwargs)
                
                # Get file sizes
                original_file_size = os.path.getsize(input_path)
                optimized_file_size = os.path.getsize(output_path)
                
                return {
                    "success": True,
                    "original_size": original_size,
                    "optimized_size": img.size,
                    "original_file_size": original_file_size,
                    "optimized_file_size": optimized_file_size,
                    "reduction_percent": round(
                        (1 - optimized_file_size / original_file_size) * 100, 2
                    )
                }
                
        except ImportError:
            return {
                "success": False,
                "error": "Pillow not installed. Run: pip install Pillow"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Image optimization failed: {str(e)}"
            }


# Singleton instance
media_processor = MediaProcessor()

