# Makes simnet_agent a package and exposes root_agent for easy import
import os
from .agent import root_agent

__all__ = ['root_agent']