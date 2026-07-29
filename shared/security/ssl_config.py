import os
import ssl
import datetime
import logging
from typing import Optional, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import ipaddress

logger = logging.getLogger(__name__)

DEFAULT_CERT_PATH = os.path.join("certs", "cert.pem")
DEFAULT_KEY_PATH = os.path.join("certs", "key.pem")


def generate_self_signed_cert(cert_path: str = DEFAULT_CERT_PATH, key_path: str = DEFAULT_KEY_PATH) -> Tuple[str, str]:
    """Generates a self-signed RSA certificate and private key if they don't already exist."""
    abs_cert = os.path.abspath(cert_path)
    abs_key = os.path.abspath(key_path)
    os.makedirs(os.path.dirname(abs_cert), exist_ok=True)

    if os.path.exists(abs_cert) and os.path.exists(abs_key):
        return abs_cert, abs_key

    logger.info(f"Generating self-signed SSL certificate at {abs_cert}...")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Kung-Fu Chess Dev"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            x509.IPAddress(ipaddress.IPv4Address("0.0.0.0")),
        ]),
        critical=False,
    ).sign(key, hashes.SHA256())

    with open(abs_key, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open(abs_cert, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    logger.info("Self-signed SSL certificate generated successfully.")
    return abs_cert, abs_key


def get_server_ssl_context(
    cert_path: Optional[str] = None,
    key_path: Optional[str] = None,
    auto_generate: bool = True
) -> Optional[ssl.SSLContext]:
    """Creates an ssl.SSLContext for server-side TLS connections.
    If cert/key paths are omitted, tries environment variables or auto-generates dev certificates.
    """
    if not cert_path or not key_path:
        cert_env = os.getenv("SSL_CERT_FILE")
        key_env = os.getenv("SSL_KEY_FILE")
        if cert_env and key_env:
            cert_path, key_path = cert_env, key_env
        elif auto_generate:
            cert_path, key_path = generate_self_signed_cert()
        else:
            return None

    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        if auto_generate:
            cert_path, key_path = generate_self_signed_cert(cert_path, key_path)
        else:
            raise FileNotFoundError(f"SSL cert or key not found: {cert_path}, {key_path}")

    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    return ctx


def get_client_ssl_context(verify_ssl: bool = False, ca_file: Optional[str] = None) -> ssl.SSLContext:
    """Creates an ssl.SSLContext for client-side TLS connections.
    For local development with self-signed certificates, verify_ssl=False skips hostname/CA validation.
    """
    if not verify_ssl:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    if ca_file and os.path.exists(ca_file):
        return ssl.create_default_context(cafile=ca_file)
    return ssl.create_default_context()
