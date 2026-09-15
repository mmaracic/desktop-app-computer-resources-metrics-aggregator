from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class EnvironmentConfig(BaseSettings):
    """Configuration settings for the metrics aggregator application.

    This class manages environment-based configuration using Pydantic Settings,
    loading values from environment variables and .env files with support for
    initialization overrides.
    """

    metric_refresh_interval: int = 5  # Interval in seconds to refresh metrics
    metric_filename: str = "daily_metrics.json"  # Filename for storing daily metrics

    model_config = SettingsConfigDict(case_sensitive=True)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Configure the order of settings sources.

        Priority order: environment variables > .env file > initialization arguments.

        Args:
            settings_cls: The settings class being configured.
            init_settings: Settings from __init__ parameters (lowest priority).
            env_settings: Settings from OS environment variables.
            dotenv_settings: Settings from .env file.
            file_secret_settings: Settings from secret files (not used).

        Returns:
            Tuple of settings sources in priority order.
        """
        return env_settings, dotenv_settings, init_settings