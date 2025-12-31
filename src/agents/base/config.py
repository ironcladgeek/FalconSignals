"""Agent configuration models."""

from pydantic import BaseModel, ConfigDict, Field


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    role: str = Field(description="Agent's role in the system")
    goal: str = Field(description="Agent's goal and objectives")
    backstory: str = Field(description="Agent's backstory and expertise")
    max_iterations: int = Field(default=5, ge=1, le=20, description="Maximum iterations")
    allow_delegation: bool = Field(default=False, description="Can delegate to other agents")
    memory: bool = Field(default=True, description="Keep memory of interactions")
    verbose: bool = Field(default=False, description="Enable verbose output")

    model_config = ConfigDict(use_enum_values=True)
