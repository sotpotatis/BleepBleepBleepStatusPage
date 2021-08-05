'''Schema.py
Contains definition of some things in the BleepBleepStatusPage schema.'''

#Things for "type" under affected_components in an incident
AFFECTED_COMPONENT_CATEGORY = "category"
AFFECTED_COMPONENT_MONITOR = "monitor"
VALID_INCIDENT_AFFECTED_COMPONENT_TYPES = [AFFECTED_COMPONENT_MONITOR, AFFECTED_COMPONENT_CATEGORY]

#The languages supported by the platform (add here if you want to add a translation)
PLATFORM_SUPPORTED_LANGUAGES = ["en", "sv"]
