"""
Environment-specific configuration management for CRM Agent.
Provides structured configuration with validation and environment-specific overrides.
"""

from pydantic import BaseSettings, Field, validator
from typing import Optional, List, Dict, Any, Union
import os
from pathlib import Path
from enum import Enum


class Environment(str, Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MCPConfig(BaseSettings):
    """MCP-specific configuration."""
    server_command: str = Field(default="python", description="Command to start MCP server")
    server_args: List[str] = Field(
        default=["-m", "crm_fastmcp_server.stdio_server"],
        description="Arguments for MCP server command"
    )
    timeout_seconds: int = Field(default=30, description="MCP operation timeout")
    max_connections: int = Field(default=10, description="Maximum concurrent MCP connections")
    enable_resources: bool = Field(default=True, description="Enable MCP resources")
    enable_prompts: bool = Field(default=True, description="Enable MCP prompts")
    
    class Config:
        env_prefix = "MCP_"


class A2AConfig(BaseSettings):
    """A2A-specific configuration."""
    host: str = Field(default="localhost", description="A2A server host")
    port: int = Field(default=10000, description="A2A server port")
    max_concurrent_tasks: int = Field(default=5, description="Maximum concurrent tasks")
    rate_limit_rpm: int = Field(default=60, description="Rate limit requests per minute")
    auth_secret_key: Optional[str] = Field(default=None, description="JWT signing secret key")
    enable_discovery: bool = Field(default=True, description="Enable agent discovery")
    enable_security: bool = Field(default=True, description="Enable security features")
    health_check_interval: int = Field(default=300, description="Health check interval in seconds")
    
    @validator("auth_secret_key", pre=True)
    def generate_secret_if_none(cls, v):
        if v is None:
            import secrets
            return secrets.token_urlsafe(64)
        return v
    
    class Config:
        env_prefix = "A2A_"


class HubSpotConfig(BaseSettings):
    """HubSpot integration configuration."""
    access_token: str = Field(..., description="HubSpot access token")
    client_id: Optional[str] = Field(default=None, description="HubSpot OAuth client ID")
    client_secret: Optional[str] = Field(default=None, description="HubSpot OAuth client secret")
    refresh_token: Optional[str] = Field(default=None, description="HubSpot OAuth refresh token")
    
    # API configuration
    api_base_url: str = Field(default="https://api.hubapi.com", description="HubSpot API base URL")
    api_version: str = Field(default="v3", description="HubSpot API version")
    rate_limit_rpm: int = Field(default=100, description="HubSpot API rate limit")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    
    # Safety settings
    test_portal: bool = Field(default=False, description="Use test portal mode")
    dry_run: bool = Field(default=False, description="Enable dry run mode")
    require_approval: bool = Field(default=True, description="Require human approval for writes")
    
    @validator("access_token")
    def validate_access_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError("HubSpot access token must be provided and valid")
        return v
    
    class Config:
        env_prefix = "HUBSPOT_"


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    url: Optional[str] = Field(default=None, description="Database URL")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="crm_assistant", description="Database name")
    username: str = Field(default="postgres", description="Database username")
    password: str = Field(default="", description="Database password")
    
    # Connection pool settings
    min_connections: int = Field(default=1, description="Minimum pool connections")
    max_connections: int = Field(default=10, description="Maximum pool connections")
    
    @property
    def connection_url(self) -> str:
        """Get the full database connection URL."""
        if self.url:
            return self.url
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    class Config:
        env_prefix = "DATABASE_"


class RedisConfig(BaseSettings):
    """Redis configuration for session storage."""
    url: Optional[str] = Field(default=None, description="Redis URL")
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    
    # Connection settings
    max_connections: int = Field(default=10, description="Maximum pool connections")
    socket_timeout: int = Field(default=5, description="Socket timeout in seconds")
    
    @property
    def connection_url(self) -> str:
        """Get the full Redis connection URL."""
        if self.url:
            return self.url
        
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_prefix = "REDIS_"


class ObservabilityConfig(BaseSettings):
    """Observability and logging configuration."""
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    enable_structured_logging: bool = Field(default=True, description="Enable structured JSON logging")
    
    # Tracing
    enable_tracing: bool = Field(default=True, description="Enable distributed tracing")
    trace_sample_rate: float = Field(default=0.1, description="Trace sampling rate (0.0-1.0)")
    
    # Metrics
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    
    # Log destinations
    log_file: Optional[str] = Field(default=None, description="Log file path")
    log_to_console: bool = Field(default=True, description="Log to console")
    
    class Config:
        env_prefix = "OBSERVABILITY_"


class SecurityConfig(BaseSettings):
    """Security configuration."""
    enable_authentication: bool = Field(default=True, description="Enable authentication")
    jwt_secret_key: Optional[str] = Field(default=None, description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    
    # Token lifetimes
    access_token_lifetime_hours: int = Field(default=24, description="Access token lifetime in hours")
    refresh_token_lifetime_days: int = Field(default=30, description="Refresh token lifetime in days")
    api_key_lifetime_days: int = Field(default=365, description="API key lifetime in days")
    
    # Rate limiting
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    default_rate_limit_rpm: int = Field(default=60, description="Default rate limit per minute")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"], description="Allowed CORS origins")
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE"], description="Allowed CORS methods")
    
    @validator("jwt_secret_key", pre=True)
    def generate_jwt_secret_if_none(cls, v):
        if v is None:
            import secrets
            return secrets.token_urlsafe(64)
        return v
    
    class Config:
        env_prefix = "SECURITY_"


class ExternalServicesConfig(BaseSettings):
    """Configuration for external services."""
    # Web search
    search_api_key: Optional[str] = Field(default=None, description="Search API key")
    search_engine: str = Field(default="duckduckgo", description="Search engine to use")
    
    # Email services
    email_api_key: Optional[str] = Field(default=None, description="Email service API key")
    email_provider: str = Field(default="sendgrid", description="Email service provider")
    
    # Slack integration
    slack_bot_token: Optional[str] = Field(default=None, description="Slack bot token")
    slack_signing_secret: Optional[str] = Field(default=None, description="Slack signing secret")
    
    # LinkedIn
    linkedin_client_id: Optional[str] = Field(default=None, description="LinkedIn client ID")
    linkedin_client_secret: Optional[str] = Field(default=None, description="LinkedIn client secret")
    
    class Config:
        env_prefix = "EXTERNAL_"


class CRMConfig(BaseSettings):
    """Main CRM configuration that combines all sub-configurations."""
    
    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Deployment environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Application
    app_name: str = Field(default="CRM Assistant", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    
    # Sub-configurations
    mcp: MCPConfig = Field(default_factory=MCPConfig, description="MCP configuration")
    a2a: A2AConfig = Field(default_factory=A2AConfig, description="A2A configuration")
    hubspot: HubSpotConfig = Field(default_factory=HubSpotConfig, description="HubSpot configuration")
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="Database configuration")
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis configuration")
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig, description="Observability configuration")
    security: SecurityConfig = Field(default_factory=SecurityConfig, description="Security configuration")
    external: ExternalServicesConfig = Field(default_factory=ExternalServicesConfig, description="External services configuration")
    
    @validator("debug", pre=True)
    def set_debug_from_environment(cls, v, values):
        env = values.get("environment", Environment.DEVELOPMENT)
        if env == Environment.DEVELOPMENT:
            return True
        return v
    
    @validator("observability", pre=True)
    def adjust_logging_for_environment(cls, v, values):
        if isinstance(v, dict):
            env = values.get("environment", Environment.DEVELOPMENT)
            if env == Environment.DEVELOPMENT:
                v.setdefault("log_level", LogLevel.DEBUG)
            elif env == Environment.PRODUCTION:
                v.setdefault("log_level", LogLevel.INFO)
        return v
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the configuration (without sensitive data)."""
        return {
            "environment": self.environment.value,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "debug": self.debug,
            "mcp_enabled": True,
            "a2a_enabled": True,
            "hubspot_configured": bool(self.hubspot.access_token),
            "database_configured": bool(self.database.url or self.database.host),
            "redis_configured": bool(self.redis.url or self.redis.host),
            "security_enabled": self.security.enable_authentication,
            "observability": {
                "log_level": self.observability.log_level.value,
                "tracing_enabled": self.observability.enable_tracing,
                "metrics_enabled": self.observability.enable_metrics
            }
        }


# Global configuration instance
_config: Optional[CRMConfig] = None


def get_config() -> CRMConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = CRMConfig()
    return _config


def reload_config() -> CRMConfig:
    """Reload configuration from environment."""
    global _config
    _config = CRMConfig()
    return _config


def get_config_for_environment(env: Environment) -> CRMConfig:
    """Get configuration for a specific environment."""
    # Temporarily override environment
    old_env = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = env.value
    
    try:
        config = CRMConfig()
        return config
    finally:
        # Restore original environment
        if old_env is not None:
            os.environ["ENVIRONMENT"] = old_env
        else:
            os.environ.pop("ENVIRONMENT", None)


def validate_configuration(config: Optional[CRMConfig] = None) -> Dict[str, Any]:
    """
    Validate configuration and return validation results.
    
    Returns:
        Dictionary with validation results and any issues found
    """
    if config is None:
        config = get_config()
    
    validation_results = {
        "valid": True,
        "issues": [],
        "warnings": []
    }
    
    # Check required configurations
    if not config.hubspot.access_token:
        validation_results["issues"].append("HubSpot access token is required")
        validation_results["valid"] = False
    
    # Check environment-specific requirements
    if config.is_production():
        if not config.security.enable_authentication:
            validation_results["issues"].append("Authentication must be enabled in production")
            validation_results["valid"] = False
        
        if config.hubspot.dry_run:
            validation_results["warnings"].append("Dry run mode is enabled in production")
        
        if config.debug:
            validation_results["warnings"].append("Debug mode is enabled in production")
    
    # Check service dependencies
    if config.observability.enable_tracing and not config.redis.url and not config.redis.host:
        validation_results["warnings"].append("Tracing enabled but Redis not configured")
    
    # Check port conflicts
    ports_in_use = [config.a2a.port]
    if config.observability.enable_metrics:
        if config.observability.metrics_port in ports_in_use:
            validation_results["issues"].append("Port conflict: metrics port conflicts with A2A port")
            validation_results["valid"] = False
        ports_in_use.append(config.observability.metrics_port)
    
    return validation_results


def create_config_template(output_file: str = ".env.template") -> str:
    """
    Create a configuration template file with all available settings.
    
    Returns:
        Path to the created template file
    """
    template_content = """# CRM Assistant Configuration Template
# Copy this file to .env and customize the values

# Environment
ENVIRONMENT=development
DEBUG=true

# HubSpot Configuration (REQUIRED)
HUBSPOT__ACCESS_TOKEN=your_hubspot_access_token_here
HUBSPOT__TEST_PORTAL=true
HUBSPOT__DRY_RUN=false
HUBSPOT__REQUIRE_APPROVAL=true

# A2A Configuration
A2A__HOST=localhost
A2A__PORT=10000
A2A__MAX_CONCURRENT_TASKS=5
A2A__RATE_LIMIT_RPM=60
A2A__ENABLE_SECURITY=true

# MCP Configuration
MCP__TIMEOUT_SECONDS=30
MCP__MAX_CONNECTIONS=10
MCP__ENABLE_RESOURCES=true
MCP__ENABLE_PROMPTS=true

# Database Configuration (Optional)
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__NAME=crm_assistant
DATABASE__USERNAME=postgres
DATABASE__PASSWORD=your_password_here

# Redis Configuration (Optional)
REDIS__HOST=localhost
REDIS__PORT=6379
REDIS__DB=0

# Security Configuration
SECURITY__ENABLE_AUTHENTICATION=true
SECURITY__ENABLE_RATE_LIMITING=true
SECURITY__DEFAULT_RATE_LIMIT_RPM=60

# Observability Configuration
OBSERVABILITY__LOG_LEVEL=INFO
OBSERVABILITY__ENABLE_TRACING=true
OBSERVABILITY__ENABLE_METRICS=true
OBSERVABILITY__LOG_TO_CONSOLE=true

# External Services (Optional)
EXTERNAL__SEARCH_API_KEY=your_search_api_key
EXTERNAL__SLACK_BOT_TOKEN=your_slack_bot_token
EXTERNAL__LINKEDIN_CLIENT_ID=your_linkedin_client_id
"""
    
    with open(output_file, 'w') as f:
        f.write(template_content)
    
    return output_file
