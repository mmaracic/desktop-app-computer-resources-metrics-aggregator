#!/usr/bin/env python3
import psutil

from src.metric.metric_provider import MetricProvider
from src.metric.model.component_type import ComponentType
from src.metric.model.metric import Metric
from src.metric.model.metric_type import MetricType


class TemperatureProvider(MetricProvider):
    """
    Provider for system temperatures and fan speeds using psutil.
    """

    def get_metrics(self) -> list[Metric]:
        metrics = []
        
        # Temperatures
        sensors = psutil.sensors_temperatures()
        for name, temps in sensors.items():
            for temp in temps:
                alias = self._get_alias(name)
                metrics.append(Metric(
                    name=f"temperature_{name}",
                    metric_type=MetricType.FLOAT,
                    value=temp.current,
                    alias=alias,
                    component_type=self._get_component_type_for_sensor(name)
                ))
        
        # Fan Speeds
        fans = psutil.sensors_fans()
        for name, fans_list in fans.items():
            for fan in fans_list:
                alias = self._get_fan_alias(name)
                metrics.append(Metric(
                    name=f"fan_speed_{name}",
                    metric_type=MetricType.INTEGER,
                    value=fan.current,
                    alias=alias,
                    component_type=self._get_component_type_for_sensor(name.replace("fan_speed_", ""))
                ))
                
        return metrics
    
    def _get_temperature_alias(self, sensor_name: str) -> str | None:
        """Get human-readable alias for temperature sensors based on name."""
        alias_map = {
            "acpitz": "System temperature - overall motherboard temperature reading",
            "k10temp": "AMD CPU temperature - core temperature of AMD processor",
            "coretemp": "Intel CPU temperature - core temperature of Intel processor",
            "nvme": "NVMe SSD temperature - drive temperature of NVMe solid-state drive",
            "intel_rapl_msr": "Intel RAPL temperature - power/thermal management temperature for Intel CPUs",
            "amdgpu": "AMD GPU temperature - junction temperature of AMD graphics card",
            "nvidia": "NVIDIA GPU temperature - temperature of NVIDIA graphics card",
            "wmi_alsi": "Motherboard sensor temperature - additional motherboard thermal sensor",
            "ecore": "Embedded controller temperature - system management temperature reading",
            "kvmhost": "KVM host temperature - virtualization host thermal sensor",
            "asus_ec": "ASUS EC temperature - ASUS Embedded Controller thermal reading",
            "fhwmon": "Fan hardware monitor temperature - fan controller thermal sensor",
            "nct6775": "NCT6775 chip temperature - Winbond super I/O temperature sensor",
            "it87": "IT87 chip temperature - Vitessa super I/O temperature sensor",
            "dell_smm": "Dell SMM temperature - Dell System Management Mode thermal reading",
            "ibm_sensor": "IBM sensor temperature - IBM system thermal sensor",
            "pcieport0": "PCIe port temperature - temperature at PCIe bus port",
            "nvidia_g2": "NVIDIA G2 GPU temperature - secondary NVIDIA GPU temperature",
            "asus_nic_temp": "ASUS NIC temperature - network interface card temperature",
        }
        return alias_map.get(sensor_name.lower())

    def _get_fan_alias(self, fan_name: str) -> str | None:
        """Get human-readable alias for fans based on name."""
        alias_map = {
            "amdgpu": "GPU fan speed - rotational speed of the graphics card cooling fan in RPM",
        }
        return alias_map.get(fan_name.lower())

    def _get_alias(self, sensor_name: str) -> str | None:
        """Get human-readable alias for sensors or fans based on name."""
        if sensor_name.startswith("fan_speed_"):
            # Extract the actual fan name (e.g., "amdgpu" from "fan_speed_amdgpu")
            return self._get_fan_alias(sensor_name.replace("fan_speed_", ""))
        else:
            # Handle temperature sensors
            return self._get_temperature_alias(sensor_name)

    def _get_component_type_for_sensor(self, sensor_name: str) -> ComponentType:
        """Determine the component type for a given sensor name."""
        sensor_lower = sensor_name.lower()
        
        # GPU sensors
        if "amdgpu" in sensor_lower or "nvidia" in sensor_lower or "nvidia_g2" in sensor_lower:
            return ComponentType.GPU
        
        # CPU sensors
        if "k10temp" in sensor_lower or "coretemp" in sensor_lower or "intel_rapl_msr" in sensor_lower:
            return ComponentType.CPU
        
        # Disk/Storage sensors
        if "nvme" in sensor_lower:
            return ComponentType.DISK
        
        # Motherboard/system sensors
        motherboard_sensors = [
            "acpitz", "wmi_alsi", "ecore", "kvmhost", "asus_ec", 
            "fhwmon", "nct6775", "it87", "dell_smm", "ibm_sensor", "gigabyte_wmi"
        ]
        if any(sensor in sensor_lower for sensor in motherboard_sensors):
            return ComponentType.MOTHERBOARD
        
        # PCIe port sensors (can be GPU or other devices)
        if "pcieport" in sensor_lower:
            return ComponentType.MOTHERBOARD  # Default to motherboard for PCIe ports
        
        # NIC sensors (wireless and ethernet)
        nic_sensors = [
            "iwlwifi", "ath9k", "rtl8xxxu", "brcm80211", "mt76", 
            "wlan", "phyintel", "phyath", "phyrtllibusb", "phyrtlnet"
        ]
        if any(sensor in sensor_lower for sensor in nic_sensors):
            return ComponentType.NETWORK
        
        # Raise error for unknown sensors
        raise ValueError(f"Unknown sensor component type for sensor: {sensor_name}")
