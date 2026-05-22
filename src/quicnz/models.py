"""Data models returned by the Quic API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


def _parse_date(obj: dict[str, str] | str | None) -> datetime | None:
    """Parse a Quic API date value to a datetime.

    Accepts either a plain ISO-8601 string or the ``{"$date": "<iso8601>"}``
    wrapper object used in the API schema examples.
    """
    if obj is None:
        return None
    raw = obj.get("$date") if isinstance(obj, dict) else obj
    if not raw:
        return None
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def _require_date(obj: dict[str, str] | str | None, field: str) -> datetime:
    dt = _parse_date(obj)
    if dt is None:
        raise ValueError(f"Missing or invalid date for field '{field}'")
    return dt


@dataclass(frozen=True)
class ServiceInfo:
    """Static configuration of a Quic broadband service."""

    static_ipv4_prefix: str
    static_ipv6_prefix: str
    static_ipv4_prefix_length: int | None
    static_ipv6_prefix_length: int | None
    username: str
    password: str
    datacap: float
    mac: str
    asid: str
    lfc: str
    """Local Fibre Company (e.g. 'Chorus')."""
    status: str
    entity: str
    entity_unique_id: str
    routes: list[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_api(cls, data: dict) -> ServiceInfo:  # type: ignore[type-arg]
        return cls(
            static_ipv4_prefix=data.get("staticIPv4Prefix", ""),
            static_ipv6_prefix=data.get("staticIPv6Prefix", ""),
            static_ipv4_prefix_length=data.get("staticIPv4PrefixLength"),
            static_ipv6_prefix_length=data.get("staticIPv6PrefixLength"),
            username=data.get("username", ""),
            password=data.get("password", ""),
            datacap=data.get("datacap", 0.0),
            mac=data.get("mac", ""),
            asid=data.get("asid", ""),
            lfc=data.get("lfc", ""),
            status=data.get("status", ""),
            entity=data.get("entity", ""),
            entity_unique_id=data.get("entityUniqueId", ""),
            routes=list(data.get("routes", [])),
            created_at=_require_date(data.get("createdAt"), "service.createdAt"),
            updated_at=_require_date(data.get("updatedAt"), "service.updatedAt"),
        )


@dataclass(frozen=True)
class PPPPayload:
    """Raw RADIUS/PPP attributes received during a PPPoE session."""

    packet_source_address: str
    nas_port_type: str
    nas_port: str
    nas_port_id: str
    service_type: str
    link_layer_address: str
    calling_station_id: str
    called_station_id: str
    delegated_ipv6_prefix: str
    nas_identifier: str
    nas_ip_address: str
    adsl_agent_remote_id: str
    adsl_agent_circuit_id: str
    event_timestamp: str
    acct_status_type: str
    acct_session_id: str
    acct_authentic: str
    acct_delay_time: float
    post_auth_result: str
    acct_input_octets: str
    user_name: str
    user_password: str
    acct_output_octets: str
    acct_unique_session_id: str

    @classmethod
    def from_api(cls, data: dict) -> PPPPayload:  # type: ignore[type-arg]
        return cls(
            packet_source_address=data.get("packetSourceAddress", ""),
            nas_port_type=data.get("nasPortType", ""),
            nas_port=data.get("nasPort", ""),
            nas_port_id=data.get("nasPortId", ""),
            service_type=data.get("serviceType", ""),
            link_layer_address=data.get("linkLayerAddress", ""),
            calling_station_id=data.get("callingStationId", ""),
            called_station_id=data.get("calledStationId", ""),
            delegated_ipv6_prefix=data.get("delegatedIPv6Prefix", ""),
            nas_identifier=data.get("nasIdentifier", ""),
            nas_ip_address=data.get("nasIPAddress", ""),
            adsl_agent_remote_id=data.get("adslAgentRemoteId", ""),
            adsl_agent_circuit_id=data.get("adslAgentCircuitId", ""),
            event_timestamp=data.get("eventTimestamp", ""),
            acct_status_type=data.get("acctStatusType", ""),
            acct_session_id=data.get("acctSessionId", ""),
            acct_authentic=data.get("acctAuthentic", ""),
            acct_delay_time=data.get("acctDelayTime", 0.0),
            post_auth_result=data.get("postAuthResult", ""),
            acct_input_octets=data.get("acctInputOctets", ""),
            user_name=data.get("userName", ""),
            user_password=data.get("userPassword", ""),
            acct_output_octets=data.get("acctOutputOctets", ""),
            acct_unique_session_id=data.get("acctUniqueSessionId", ""),
        )


@dataclass(frozen=True)
class Session:
    """Active session data for a Quic broadband service."""

    service: ServiceInfo
    status: str
    """Connection status, e.g. 'connected'."""
    session_type: str
    """Authentication type, e.g. 'DHCP' or 'PPPoE'."""
    active_ipv4_prefix: str
    active_ipv4_prefix_length: int
    active_ipv6_prefix: str
    active_ipv6_prefix_length: int
    last_radius_update: datetime
    session_expires_at: datetime
    ppp_payload: PPPPayload | None
    """Present only for PPPoE sessions."""
    created_at: datetime
    updated_at: datetime

    @property
    def is_connected(self) -> bool:
        """Return ``True`` when the session status is 'connected'."""
        return self.status.lower() == "connected"

    @property
    def active_ipv4_address(self) -> str:
        """Active IPv4 address without prefix-length notation."""
        return self.active_ipv4_prefix

    @classmethod
    def from_api(cls, data: dict) -> Session:  # type: ignore[type-arg]
        ppp_data = data.get("pppPayload")
        return cls(
            service=ServiceInfo.from_api(data["service"]),
            status=data.get("status", ""),
            session_type=data.get("sessionType", ""),
            active_ipv4_prefix=data.get("activeIPv4Prefix", ""),
            active_ipv4_prefix_length=data.get("activeIPv4PrefixLength", 0),
            active_ipv6_prefix=data.get("activeIPv6Prefix", ""),
            active_ipv6_prefix_length=data.get("activeIPv6PrefixLength", 0),
            last_radius_update=_require_date(data.get("lastRadiusUpdate"), "lastRadiusUpdate"),
            session_expires_at=_require_date(data.get("sessionExpiresAt"), "sessionExpiresAt"),
            ppp_payload=PPPPayload.from_api(ppp_data) if ppp_data else None,
            created_at=_require_date(data.get("createdAt"), "createdAt"),
            updated_at=_require_date(data.get("updatedAt"), "updatedAt"),
        )
