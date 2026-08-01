"""Shared service metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceIdentity:
    name: str
    seed: str
    port: int | str

    @property
    def address(self) -> str:
        return f"local://{self.name.lower()}"

    @property
    def endpoint(self) -> str:
        if isinstance(self.port, int):
            return f"http://localhost:{self.port}/submit"
        return self.port


class BioAgentService:
    """Small base class used for dashboard service status."""

    identity: ServiceIdentity

    @property
    def name(self) -> str:
        return self.identity.name

    @property
    def address(self) -> str:
        return self.identity.address

    @property
    def endpoint(self) -> str:
        return self.identity.endpoint
