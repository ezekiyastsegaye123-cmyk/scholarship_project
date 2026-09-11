import ipaddress
import socket
import urllib.parse
from typing import Optional


class IngestionSafetyError(ValueError):
    """Raised when an ingestion URL or response violates safety constraints."""
    pass


ALLOWED_SCHEMES = {"http", "https"}
MAX_URL_LENGTH = 2048
ALLOWED_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "text/plain",
}

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "metadata.google.internal",
    "instance-data",
}

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private RFC 1918
    ipaddress.ip_network("172.16.0.0/12"),    # Private RFC 1918
    ipaddress.ip_network("192.168.0.0/16"),   # Private RFC 1918
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / Cloud metadata (AWS, GCP, Azure, DigitalOcean)
    ipaddress.ip_network("100.64.0.0/10"),    # Carrier-grade NAT
    ipaddress.ip_network("0.0.0.0/8"),        # This-network
    ipaddress.ip_network("224.0.0.0/4"),      # Multicast
    ipaddress.ip_network("240.0.0.0/4"),      # Reserved
    ipaddress.ip_network("::1/128"),          # IPv6 Loopback
    ipaddress.ip_network("fe80::/10"),        # IPv6 Link-local
    ipaddress.ip_network("fc00::/7"),         # IPv6 Unique Local Address
    ipaddress.ip_network("ff00::/8"),         # IPv6 Multicast
]


def is_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Checks if an IP address belongs to loopback, private, link-local, or cloud metadata."""
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        return True
    return any(ip in net for net in BLOCKED_IP_NETWORKS)


def validate_url(url: str, allow_private: bool = False, check_dns: bool = True) -> None:
    """Validates URL for safe HTTP ingestion and prevents SSRF attacks.
    
    Raises IngestionSafetyError if the URL is invalid or targets private/internal resources.
    """
    if not url or not isinstance(url, str):
        raise IngestionSafetyError("URL must be a non-empty string.")

    if len(url) > MAX_URL_LENGTH:
        raise IngestionSafetyError(f"URL exceeds maximum length of {MAX_URL_LENGTH} characters.")

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        raise IngestionSafetyError(f"Malformed URL: {e}") from e

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise IngestionSafetyError(
            f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are permitted."
        )

    if not parsed.netloc:
        raise IngestionSafetyError("URL missing valid network location / domain.")

    # Extract hostname, stripping port and brackets if IPv6
    hostname = parsed.hostname
    if not hostname:
        raise IngestionSafetyError("URL missing valid hostname.")

    hostname_lower = hostname.lower().strip(".")

    if not allow_private:
        # 1. Exact or suffix checks for internal/local hostnames
        if hostname_lower in BLOCKED_HOSTNAMES:
            raise IngestionSafetyError(f"SSRF blocked: Hostname '{hostname}' is not permitted.")

        for suffix in (".localhost", ".local", ".internal", ".lan", ".localdomain"):
            if hostname_lower.endswith(suffix):
                raise IngestionSafetyError(f"SSRF blocked: Internal domain '{hostname}' is not permitted.")

        # 2. Check direct IP address literal in URL
        ip_obj = None
        try:
            ip_obj = ipaddress.ip_address(hostname_lower)
        except ValueError:
            # Not an IP literal, standard domain name
            pass

        if ip_obj is not None and is_ip_blocked(ip_obj):
            raise IngestionSafetyError(
                f"SSRF blocked: IP literal '{hostname_lower}' targets private or restricted network."
            )

        # 3. DNS resolution check (if enabled)
        if check_dns:
            try:
                addr_info = socket.getaddrinfo(hostname_lower, None)
                for family, _, _, _, sockaddr in addr_info:
                    ip_str = sockaddr[0]
                    try:
                        resolved_ip = ipaddress.ip_address(ip_str)
                        if is_ip_blocked(resolved_ip):
                            raise IngestionSafetyError(
                                f"SSRF blocked: Hostname '{hostname}' resolves to restricted IP '{ip_str}'."
                            )
                    except ValueError:
                        continue
            except socket.gaierror:
                # DNS failure or offline environment: do not fail URL validation here
                # let HTTP client handle reachability or mock transport
                pass


def is_safe_content_type(content_type_header: Optional[str]) -> bool:
    """Checks if the Content-Type header indicates safe HTML or text content."""
    if not content_type_header:
        # If server omits Content-Type, allow HTML sniffing in client
        return True

    mime_part = content_type_header.split(";")[0].strip().lower()
    return mime_part in ALLOWED_CONTENT_TYPES
