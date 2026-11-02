"""Behaviour contracts: endpoint predicates match hosts, never raw-URL substrings.

A base URL such as ``https://evil.com/azure.com/v1`` or
``https://generativelanguage.googleapis.com.evil/openai`` must not select a
provider's auth header, beta flags or native adapter. These cases pin the
host/path matching introduced after the CodeQL
``py/incomplete-url-substring-sanitization`` triage.
"""
from __future__ import annotations

from types import SimpleNamespace

from agent.anthropic_endpoints import (
    _base_url_needs_context_1m_beta,
    _is_minimax_anthropic_endpoint,
    _requires_bearer_auth,
)
from agent.gemini_native_adapter import is_native_gemini_base_url, is_vertex_express_base_url
from agent.transports.chat_completions import _is_gemini_openai_compat_base_url
from hermes_cli.main_provider_setup import _infer_stepfun_region
from run_agent import AIAgent


def test_bearer_auth_accepts_real_minimax_and_azure_hosts():
    assert _requires_bearer_auth("https://api.minimax.io/anthropic") is True
    assert _requires_bearer_auth("https://api.minimaxi.com/anthropic/v1") is True
    assert _requires_bearer_auth("https://team.services.ai.azure.com/anthropic") is True
    assert _requires_bearer_auth("https://api.openai.azure.com/openai") is True


def test_bearer_auth_rejects_path_and_lookalike_host_spoofing():
    assert _requires_bearer_auth("https://evil.com/azure.com/v1") is False
    assert _requires_bearer_auth("https://evil.com/api.minimax.io/anthropic") is False
    assert _requires_bearer_auth("https://api.minimax.io.evil.com/anthropic") is False
    assert _requires_bearer_auth("https://azure.com.evil.example/v1") is False


def test_minimax_path_prefix_requires_a_segment_boundary():
    assert _is_minimax_anthropic_endpoint("https://api.minimax.io/anthropicx") is False
    assert _is_minimax_anthropic_endpoint("https://api.minimax.io/anthropic") is True


def test_context_1m_beta_is_host_scoped():
    assert _base_url_needs_context_1m_beta("https://my.services.ai.azure.com/anthropic") is True
    assert _base_url_needs_context_1m_beta("https://evil.com/azure.com") is False


def test_gemini_native_hosts_are_not_substring_matches():
    assert is_native_gemini_base_url("https://generativelanguage.googleapis.com") is True
    assert is_native_gemini_base_url("https://evil.com/generativelanguage.googleapis.com") is False
    assert is_native_gemini_base_url("https://generativelanguage.googleapis.com.evil.example") is False
    assert is_native_gemini_base_url("https://generativelanguage.googleapis.com/v1beta/openai") is False


def test_vertex_express_requires_the_real_host():
    assert is_vertex_express_base_url("https://aiplatform.googleapis.com/v1beta1") is True
    assert is_vertex_express_base_url("https://evil.com/aiplatform.googleapis.com/v1beta1") is False
    assert is_vertex_express_base_url("https://aiplatform.googleapis.com.evil.example/v1beta1") is False
    # The OAuth Vertex route carries a project path and stays off the express surface.
    assert is_vertex_express_base_url(
        "https://aiplatform.googleapis.com/v1/projects/p/locations/r/endpoints/openapi"
    ) is False


def test_gemini_openai_compat_requires_host_and_openai_path():
    assert _is_gemini_openai_compat_base_url(
        "https://generativelanguage.googleapis.com/v1beta/openai") is True
    assert _is_gemini_openai_compat_base_url(
        "https://evil.com/generativelanguage.googleapis.com/v1beta/openai") is False
    assert _is_gemini_openai_compat_base_url(
        "https://generativelanguage.googleapis.com/v1beta") is False


def test_stepfun_region_uses_the_endpoint_host():
    assert _infer_stepfun_region("https://api.stepfun.com/v1") == "china"
    assert _infer_stepfun_region("https://evil.com/api.stepfun.com") == "international"
    assert _infer_stepfun_region("https://api.stepfun.com.evil.example/v1") == "international"


def _ollama_agent(base_url: str) -> SimpleNamespace:
    from utils import base_url_hostname

    return SimpleNamespace(
        model="glm-4.6",
        provider="",
        _base_url_lower=base_url.lower(),
        _base_url_hostname=base_url_hostname(base_url),
    )


def test_ollama_detection_ignores_paths_but_matches_local_hosts_and_port():
    assert AIAgent._is_ollama_glm_backend(_ollama_agent("https://evil.com/ollama")) is False
    assert AIAgent._is_ollama_glm_backend(_ollama_agent("https://ollama.com/v1")) is False
    assert AIAgent._is_ollama_glm_backend(_ollama_agent("http://ollama:11434")) is True
    assert AIAgent._is_ollama_glm_backend(_ollama_agent("http://127.0.0.1:11434")) is True
    assert AIAgent._is_ollama_glm_backend(_ollama_agent("http://gpu-box.lan:8080")) is False
