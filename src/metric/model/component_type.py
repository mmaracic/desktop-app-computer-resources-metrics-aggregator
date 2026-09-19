"""Component types for computer hardware metrics."""

from enum import Enum


class ComponentType(Enum):
    """Enumeration of computer hardware component types.

    This enum defines the different types of computer components that can be
    monitored for resource utilization and performance metrics. Each component
    type represents a distinct hardware category with specific metrics associated
    with it (e.g., CPU usage, GPU temperature, RAM utilization).

    Attributes:
        CPU: Central Processing Unit - handles general computation tasks
        GPU: Graphics Processing Unit - handles graphics rendering and parallel computation
        RAM: Random Access Memory - volatile memory for active data storage
        DISK: Storage devices including HDDs and SSDs
        MOTHERBOARD: Main circuit board connecting all components
        NETWORK: Network interfaces and communication hardware

    """

    CPU = "cpu"
    GPU = "gpu"
    RAM = "ram"
    DISK = "disk"
    MOTHERBOARD = "motherboard"
    NETWORK = "network"
