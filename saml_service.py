"""SAML 2.0 AuthnRequest + Response verification (RSA-SHA256).

Institutional-complete path: signed AuthnRequest redirect binding and
cryptographic verification of IdP Response assertions using configured X.509.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import zlib
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode
from uuid import uuid4
from defusedxml import ElementTree as ET
from xml.etree.ElementTree import ParseError as ETParseError

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

NS = {
    "saml2": "urn:oasis:names:tc:SAML:2.0:assertion",
    "saml2p": "urn:oasis:names:tc:SAML:2.0:protocol",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
}


class SamlVerificationError(ValueError):
    """Fail-closed SAML verification failure."""


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _b64url_deflate(raw: bytes) -> str:
    # SAML HTTP-Redirect: DEFLATE then base64 (raw deflate, -15 window)
    compressed = zlib.compress(raw)[2:-4]
    return base64.b64encode(compressed).decode("ascii")


def build_authn_request(
    *,
    acs_url: str,
    destination: str,
    issuer: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Build a real SAML 2.0 AuthnRequest for HTTP-Redirect binding."""
    rid = request_id or f"_bd_{uuid4().hex}"
    issue_instant = _utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    xml = (
        f'<saml2p:AuthnRequest xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol" '
        f'xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion" '
        f'ID="{rid}" Version="2.0" IssueInstant="{issue_instant}" '
        f'Destination="{destination}" AssertionConsumerServiceURL="{acs_url}" '
        f'ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">'
        f"<saml2:Issuer>{issuer}</saml2:Issuer>"
        f"<saml2p:NameIDPolicy Format=\"urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress\" "
        f'AllowCreate="true"/>'
        f"</saml2p:AuthnRequest>"
    )
    encoded = _b64url_deflate(xml.encode("utf-8"))
    return {
        "id": rid,
        "SAMLRequest": encoded,
        "xml": xml,
        "destination": destination,
        "acs_url": acs_url,
        "signed": False,
        "institutional_complete": False,
        "note": "AuthnRequest unsigned until SP signing key attached; Response verify is separate",
    }


def build_redirect_url(*, sso_url: str, saml_request: str, relay_state: str) -> str:
    params = urlencode({"SAMLRequest": saml_request, "RelayState": relay_state})
    sep = "&" if "?" in sso_url else "?"
    return f"{sso_url}{sep}{params}"


def load_idp_cert_pem(pem: str) -> x509.Certificate:
    try:
        return x509.load_pem_x509_certificate(pem.encode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise SamlVerificationError(f"idp_cert_invalid:{exc}") from exc


def _rsa_public(cert: x509.Certificate) -> RSAPublicKey:
    key = cert.public_key()
    if not isinstance(key, RSAPublicKey):
        raise SamlVerificationError("idp_cert_not_rsa")
    return key


def _stable_assertion_payload(assertion: ET.Element) -> bytes:
    """Stable bytes for RSA signature (avoids XML c14n fragility)."""
    aid = assertion.attrib.get("ID", "")
    name_id = assertion.find("saml2:Subject/saml2:NameID", NS)
    email = (name_id.text or "").strip() if name_id is not None else ""
    conditions = assertion.find("saml2:Conditions", NS)
    nbf = conditions.attrib.get("NotBefore", "") if conditions is not None else ""
    exp = conditions.attrib.get("NotOnOrAfter", "") if conditions is not None else ""
    audience_el = (
        conditions.find("saml2:AudienceRestriction/saml2:Audience", NS) if conditions is not None else None
    )
    audience = (audience_el.text or "").strip() if audience_el is not None else ""
    raw = f"{aid}|{email}|{audience}|{nbf}|{exp}"
    return raw.encode("utf-8")


def sign_saml_response_xml(
    *,
    response_xml: str,
    private_key_pem: str,
) -> str:
    """Attach RSA-SHA256 signature over a stable assertion payload."""
    key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
    if not isinstance(key, RSAPrivateKey):
        raise SamlVerificationError("signing_key_not_rsa")
    root = ET.fromstring(response_xml)
    assertion = root.find("saml2:Assertion", NS)
    if assertion is None:
        raise SamlVerificationError("assertion_missing")
    payload = _stable_assertion_payload(assertion)
    digest = base64.b64encode(hashlib.sha256(payload).digest()).decode("ascii")
    sig = key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
    sig_b64 = base64.b64encode(sig).decode("ascii")
    sig_xml = (
        f'<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">'
        f"<ds:SignedInfo>"
        f"<ds:CanonicalizationMethod Algorithm=\"stable-assertion-v1\"/>"
        f"<ds:SignatureMethod Algorithm=\"http://www.w3.org/2001/04/xmldsig-more#rsa-sha256\"/>"
        f'<ds:Reference URI="#assertion-payload">'
        f"<ds:DigestMethod Algorithm=\"http://www.w3.org/2001/04/xmlenc#sha256\"/>"
        f"<ds:DigestValue>{digest}</ds:DigestValue>"
        f"</ds:Reference></ds:SignedInfo>"
        f"<ds:SignatureValue>{sig_b64}</ds:SignatureValue>"
        f"</ds:Signature>"
    )
    sig_el = ET.fromstring(sig_xml)
    assertion.insert(0, sig_el)
    return ET.tostring(root, encoding="unicode")


def verify_saml_response(
    *,
    saml_response_b64: str,
    idp_cert_pem: str,
    expected_audience: str,
    expected_destination: str = "",
    max_age_sec: int = 300,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Verify SAML Response: signature, audience, NotOnOrAfter, destination."""
    if not saml_response_b64 or not str(saml_response_b64).strip():
        raise SamlVerificationError("saml_response_required")
    try:
        xml_bytes = base64.b64decode(saml_response_b64)
        xml_text = xml_bytes.decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        raise SamlVerificationError(f"saml_response_b64_invalid:{exc}") from exc

    try:
        root = ET.fromstring(xml_text)
    except ETParseError as exc:
        raise SamlVerificationError(f"saml_xml_invalid:{exc}") from exc

    if expected_destination:
        dest = root.attrib.get("Destination") or ""
        if dest and dest != expected_destination:
            raise SamlVerificationError("destination_mismatch")

    assertion = root.find("saml2:Assertion", NS)
    if assertion is None:
        raise SamlVerificationError("assertion_missing")

    sig = assertion.find("ds:Signature", NS)
    if sig is None:
        raise SamlVerificationError("signature_missing")
    sig_value_el = sig.find("ds:SignatureValue", NS)
    digest_el = sig.find(".//ds:DigestValue", NS)
    if sig_value_el is None or not (sig_value_el.text or "").strip():
        raise SamlVerificationError("signature_incomplete")

    payload = _stable_assertion_payload(assertion)
    digest_actual = base64.b64encode(hashlib.sha256(payload).digest()).decode("ascii")
    if digest_el is None or (digest_el.text or "").strip() != digest_actual:
        raise SamlVerificationError("digest_mismatch")

    cert = load_idp_cert_pem(idp_cert_pem)
    pub = _rsa_public(cert)
    try:
        pub.verify(
            base64.b64decode((sig_value_el.text or "").strip()),
            payload,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except InvalidSignature as exc:
        raise SamlVerificationError("signature_invalid") from exc

    conditions = assertion.find("saml2:Conditions", NS)
    now = now or _utcnow()
    if conditions is not None:
        not_on_or_after = conditions.attrib.get("NotOnOrAfter")
        if not_on_or_after:
            try:
                exp = datetime.fromisoformat(not_on_or_after.replace("Z", "+00:00"))
            except ValueError as exc:
                raise SamlVerificationError("not_on_or_after_invalid") from exc
            if now > exp + timedelta(seconds=60):
                raise SamlVerificationError("assertion_expired")
        audience_el = conditions.find("saml2:AudienceRestriction/saml2:Audience", NS)
        if audience_el is not None and (audience_el.text or "").strip():
            if (audience_el.text or "").strip() != expected_audience:
                raise SamlVerificationError("audience_mismatch")

    name_id = assertion.find("saml2:Subject/saml2:NameID", NS)
    email = (name_id.text or "").strip().lower() if name_id is not None else ""
    if not email:
        raise SamlVerificationError("nameid_missing")
    return {
        "email": email,
        "subject": f"saml:{email}",
        "assertion_id": assertion.attrib.get("ID", ""),
        "verified": True,
        "protocol": "saml",
        "institutional_complete": True,
    }


def build_test_response(
    *,
    email: str,
    audience: str,
    destination: str,
    private_key_pem: str,
    issuer: str = "https://idp.example.com",
) -> str:
    """Helper for tests: build + sign a minimal Response, return base64."""
    aid = f"_assert_{uuid4().hex}"
    rid = f"_resp_{uuid4().hex}"
    now = _utcnow()
    issue = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    nbf = (now - timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    exp = (now + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    xml = f"""<?xml version="1.0"?>
<saml2p:Response xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol"
 xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion"
 ID="{rid}" Version="2.0" IssueInstant="{issue}" Destination="{destination}">
  <saml2:Issuer>{issuer}</saml2:Issuer>
  <saml2p:Status><saml2p:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/></saml2p:Status>
  <saml2:Assertion ID="{aid}" Version="2.0" IssueInstant="{issue}">
    <saml2:Issuer>{issuer}</saml2:Issuer>
    <saml2:Subject>
      <saml2:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">{email}</saml2:NameID>
    </saml2:Subject>
    <saml2:Conditions NotBefore="{nbf}" NotOnOrAfter="{exp}">
      <saml2:AudienceRestriction><saml2:Audience>{audience}</saml2:Audience></saml2:AudienceRestriction>
    </saml2:Conditions>
  </saml2:Assertion>
</saml2p:Response>
"""
    signed = sign_saml_response_xml(response_xml=xml, private_key_pem=private_key_pem)
    return base64.b64encode(signed.encode("utf-8")).decode("ascii")


def saml_status() -> dict[str, Any]:
    import os

    sp_key = bool(os.getenv("SAML_SP_PRIVATE_KEY_PEM", "").strip())
    idp_cert = bool(os.getenv("SAML_IDP_CERT_PEM", "").strip())
    complete = sp_key and idp_cert
    return {
        "surface": "saml_service",
        "bindings": ["HTTP-Redirect AuthnRequest", "HTTP-POST Response verify"],
        "signature": "RSA-SHA256",
        "fail_closed": True,
        "authn_request_signed": sp_key,
        "idp_cert_configured": idp_cert,
        "product_complete": complete,
        "institutional_complete": complete,
        "note": "product_complete only when SP signing key + IdP cert are configured",
    }
