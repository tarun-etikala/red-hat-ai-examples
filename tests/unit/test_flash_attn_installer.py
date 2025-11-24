"""Unit tests for flash_attn_installer.py module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the module to test
training_utils = (
    Path(__file__).parent.parent.parent
    / "examples"
    / "knowledge-tuning"
    / "05_Model_Training"
    / "utils"
)
sys.path.insert(0, str(training_utils))

from flash_attn_installer import (
    download_flash_attention_wheel,
    get_flash_attention_url,
    get_latest,
)


class TestGetLatest:
    """Tests for get_latest function."""

    def test_cuda_not_available(self):
        """Test when CUDA is not available."""
        result = get_latest(
            python_version_short="312",
            torch_version_clean="2.8",
            cuda_version=None,
            platform_str="linux_x86_64",
            cxx11_abi="TRUE",
        )
        assert result is None

    def test_basic_url_construction_linux(self):
        """Test URL construction for Linux with CUDA 12."""
        result = get_latest(
            python_version_short="312",
            torch_version_clean="2.8",
            cuda_version="12.1.0",
            platform_str="linux_x86_64",
            cxx11_abi="TRUE",
        )

        assert result is not None
        assert "flash_attn" in result
        assert "cp312" in result
        assert "linux_x86_64" in result
        assert "cu12torch2.8cxx11abiTRUE" in result
        assert result.startswith("https://github.com/Dao-AILab/flash-attention/releases")

    def test_basic_url_construction_with_false_abi(self):
        """Test URL construction with CXX11 ABI FALSE."""
        result = get_latest(
            python_version_short="311",
            torch_version_clean="2.5",
            cuda_version="12.1.0",
            platform_str="linux_x86_64",
            cxx11_abi="FALSE",
        )

        assert result is not None
        assert "cxx11abiFALSE" in result
        assert "cp311" in result

    def test_cuda_version_parsing_short(self):
        """Test CUDA version parsing with short version."""
        result = get_latest(
            python_version_short="312",
            torch_version_clean="2.8",
            cuda_version="12.1",
            platform_str="linux_x86_64",
            cxx11_abi="TRUE",
        )

        assert result is not None
        assert "cu12" in result

    def test_cuda_version_parsing_long(self):
        """Test CUDA version parsing with long version."""
        result = get_latest(
            python_version_short="312",
            torch_version_clean="2.8",
            cuda_version="12.4.1",
            platform_str="linux_x86_64",
            cxx11_abi="TRUE",
        )

        assert result is not None
        assert "cu12" in result

    @patch("urllib.request.urlopen")
    def test_github_api_fallback(self, mock_urlopen):
        """Test fallback version when GitHub API fails."""
        # Simulate API failure
        mock_urlopen.side_effect = Exception("API Error")

        result = get_latest(
            python_version_short="312",
            torch_version_clean="2.8",
            cuda_version="12.1.0",
            platform_str="linux_x86_64",
            cxx11_abi="TRUE",
        )

        # Should still return a URL with fallback version
        assert result is not None
        assert "2.8.3" in result  # Fallback version

    @patch("urllib.request.urlopen")
    def test_github_api_success(self, mock_urlopen):
        """Test successful GitHub API call."""
        # Mock API response
        mock_response = Mock()
        mock_response.read.return_value = b'{"tag_name": "v2.9.0"}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = get_latest(
            python_version_short="312",
            torch_version_clean="2.8",
            cuda_version="12.1.0",
            platform_str="linux_x86_64",
            cxx11_abi="TRUE",
        )

        assert result is not None
        assert "2.9.0" in result

    def test_platform_variations(self):
        """Test URL construction with different platforms."""
        platforms = [
            "linux_x86_64",
            "linux_aarch64",
            "macosx_11_0_arm64",
        ]

        for platform_str in platforms:
            result = get_latest(
                python_version_short="312",
                torch_version_clean="2.8",
                cuda_version="12.1.0",
                platform_str=platform_str,
                cxx11_abi="TRUE",
            )
            assert result is not None
            assert platform_str in result

    def test_python_version_variations(self):
        """Test URL construction with different Python versions."""
        python_versions = ["38", "39", "310", "311", "312"]

        for py_ver in python_versions:
            result = get_latest(
                python_version_short=py_ver,
                torch_version_clean="2.8",
                cuda_version="12.1.0",
                platform_str="linux_x86_64",
                cxx11_abi="TRUE",
            )
            assert result is not None
            assert f"cp{py_ver}" in result


class TestGetFlashAttentionUrl:
    """Tests for get_flash_attention_url function."""

    @patch("torch.cuda.is_available")
    @patch("torch.version.cuda", "12.1.0")
    @patch("torch.__version__", "2.8.0")
    @patch("platform.system")
    @patch("platform.machine")
    def test_linux_x86_64_with_cuda(
        self, mock_machine, mock_system, mock_cuda_available
    ):
        """Test URL detection for Linux x86_64 with CUDA."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"
        mock_cuda_available.return_value = True

        result = get_flash_attention_url()

        assert result is not None
        assert "linux_x86_64" in result
        assert "cu12" in result

    @patch("torch.cuda.is_available")
    def test_no_cuda_returns_none(self, mock_cuda_available):
        """Test that function returns None when CUDA is unavailable."""
        mock_cuda_available.return_value = False

        result = get_flash_attention_url()

        assert result is None

    @patch("torch.cuda.is_available")
    @patch("torch.version.cuda", "12.1.0")
    @patch("torch.__version__", "2.8.0")
    @patch("platform.system")
    @patch("platform.machine")
    def test_linux_aarch64(self, mock_machine, mock_system, mock_cuda_available):
        """Test URL detection for Linux ARM64."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "aarch64"
        mock_cuda_available.return_value = True

        result = get_flash_attention_url()

        assert result is not None
        assert "linux_aarch64" in result

    @patch("torch.cuda.is_available")
    @patch("torch.version.cuda", "12.1.0")
    @patch("torch.__version__", "2.8.0+cu121")
    @patch("platform.system")
    @patch("platform.machine")
    def test_torch_version_with_suffix(
        self, mock_machine, mock_system, mock_cuda_available
    ):
        """Test PyTorch version parsing with CUDA suffix."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"
        mock_cuda_available.return_value = True

        result = get_flash_attention_url()

        assert result is not None
        assert "torch2.8" in result  # Should strip +cu121 suffix

    @patch("torch.cuda.is_available")
    @patch("torch.version.cuda", "12.1.0")
    @patch("torch.__version__", "2.8.0")
    @patch("platform.system")
    @patch("platform.machine")
    @patch("subprocess.run")
    def test_cxx11_abi_detection_true(
        self, mock_subprocess, mock_machine, mock_system, mock_cuda_available
    ):
        """Test CXX11 ABI detection returns TRUE."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"
        mock_cuda_available.return_value = True

        # Mock subprocess to return True
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "True"
        mock_subprocess.return_value = mock_result

        result = get_flash_attention_url()

        assert result is not None
        assert "cxx11abiTRUE" in result

    @patch("torch.cuda.is_available")
    @patch("torch.version.cuda", "12.1.0")
    @patch("torch.__version__", "2.8.0")
    @patch("platform.system")
    @patch("platform.machine")
    @patch("subprocess.run")
    def test_cxx11_abi_detection_false(
        self, mock_subprocess, mock_machine, mock_system, mock_cuda_available
    ):
        """Test CXX11 ABI detection returns FALSE."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"
        mock_cuda_available.return_value = True

        # Mock subprocess to return False
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "False"
        mock_subprocess.return_value = mock_result

        result = get_flash_attention_url()

        assert result is not None
        assert "cxx11abiFALSE" in result

    @patch("torch.cuda.is_available")
    @patch("torch.version.cuda", "12.1.0")
    @patch("torch.__version__", "2.8.0")
    @patch("platform.system")
    @patch("platform.machine")
    @patch("subprocess.run")
    def test_cxx11_abi_detection_failure_defaults_true(
        self, mock_subprocess, mock_machine, mock_system, mock_cuda_available
    ):
        """Test CXX11 ABI defaults to TRUE on detection failure."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"
        mock_cuda_available.return_value = True

        # Mock subprocess to fail
        mock_subprocess.side_effect = Exception("Subprocess failed")

        result = get_flash_attention_url()

        assert result is not None
        assert "cxx11abiTRUE" in result  # Should default to TRUE


class TestDownloadFlashAttentionWheel:
    """Tests for download_flash_attention_wheel function."""

    @patch("flash_attn_installer.get_flash_attention_url")
    @patch("urllib.request.urlretrieve")
    @patch("pathlib.Path.mkdir")
    def test_successful_download(self, mock_mkdir, mock_urlretrieve, mock_get_url):
        """Test successful wheel download."""
        mock_url = "https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3+cu12torch2.8cxx11abiTRUE-cp312-cp312-linux_x86_64.whl"
        mock_get_url.return_value = mock_url

        result = download_flash_attention_wheel()

        assert result is not None
        assert "flash_attn" in result
        assert result.endswith(".whl")
        mock_urlretrieve.assert_called_once()
        mock_mkdir.assert_called_once()

    @patch("flash_attn_installer.get_flash_attention_url")
    def test_no_compatible_wheel(self, mock_get_url):
        """Test when no compatible wheel is found."""
        mock_get_url.return_value = None

        result = download_flash_attention_wheel()

        assert result is None

    @patch("flash_attn_installer.get_flash_attention_url")
    @patch("urllib.request.urlretrieve")
    @patch("pathlib.Path.mkdir")
    def test_download_path_creation(self, mock_mkdir, mock_urlretrieve, mock_get_url):
        """Test that download directory is created."""
        mock_url = "https://example.com/flash_attn-2.8.3-cp312-cp312-linux_x86_64.whl"
        mock_get_url.return_value = mock_url

        download_flash_attention_wheel()

        # Verify mkdir was called with correct arguments
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("flash_attn_installer.get_flash_attention_url")
    @patch("urllib.request.urlretrieve")
    @patch("pathlib.Path.mkdir")
    def test_wheel_filename_extraction(
        self, mock_mkdir, mock_urlretrieve, mock_get_url
    ):
        """Test that wheel filename is correctly extracted from URL."""
        wheel_filename = "flash_attn-2.8.3+cu12torch2.8cxx11abiTRUE-cp312-cp312-linux_x86_64.whl"
        mock_url = f"https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/{wheel_filename}"
        mock_get_url.return_value = mock_url

        result = download_flash_attention_wheel()

        assert wheel_filename in result
        assert result.endswith(wheel_filename)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_cuda_version_with_two_digits(self):
        """Test CUDA version parsing with 2-digit version."""
        result = get_latest(
            python_version_short="312",
            torch_version_clean="2.8",
            cuda_version="12",
            platform_str="linux_x86_64",
            cxx11_abi="TRUE",
        )

        assert result is not None
        assert "cu12" in result

    def test_cuda_version_with_single_digit(self):
        """Test CUDA version parsing with 1-digit version."""
        result = get_latest(
            python_version_short="312",
            torch_version_clean="2.8",
            cuda_version="12",
            platform_str="linux_x86_64",
            cxx11_abi="TRUE",
        )

        assert result is not None

    def test_url_components_present(self):
        """Test that all required URL components are present."""
        result = get_latest(
            python_version_short="312",
            torch_version_clean="2.8",
            cuda_version="12.1.0",
            platform_str="linux_x86_64",
            cxx11_abi="TRUE",
        )

        required_components = [
            "github.com",
            "flash-attention",
            "releases",
            "download",
            ".whl",
        ]

        for component in required_components:
            assert component in result

    def test_wheel_naming_convention(self):
        """Test that wheel follows PEP naming convention."""
        result = get_latest(
            python_version_short="312",
            torch_version_clean="2.8",
            cuda_version="12.1.0",
            platform_str="linux_x86_64",
            cxx11_abi="TRUE",
        )

        # Should match pattern: name-version-python-abi-platform.whl
        assert "-cp312-cp312-" in result
        assert result.endswith(".whl")
