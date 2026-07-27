"""
Shared message contracts package for Kung-Fu Chess Microservices.
Contains DTOs, schemas, constants, and NATS message client.
"""

from shared.message_contracts import subjects
from shared.message_contracts.contracts import *
from shared.message_contracts.nats_client import NatsBus

__all__ = ["subjects", "NatsBus"]
