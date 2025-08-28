from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
import asyncio

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

@dataclass
class MCPMessage:
    """Model Context Protocol Message"""
    type: MessageType
    method: str
    params: Dict[str, Any]
    id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class MCPProtocol:
    """MCP Protocol handler for agent communication"""
    
    def __init__(self):
        self.handlers = {}
        self.pending_requests = {}
        
    def register_handler(self, method: str, handler):
        """Register a method handler"""
        self.handlers[method] = handler
        
    async def send_request(self, method: str, params: Dict[str, Any]) -> Any:
        """Send an MCP request"""
        message = MCPMessage(
            type=MessageType.REQUEST,
            method=method,
            params=params,
            id=self._generate_id()
        )
        
        # Process request
        if method in self.handlers:
            try:
                result = await self.handlers[method](params)
                return MCPMessage(
                    type=MessageType.RESPONSE,
                    method=method,
                    params={},
                    id=message.id,
                    result=result
                )
            except Exception as e:
                return MCPMessage(
                    type=MessageType.ERROR,
                    method=method,
                    params={},
                    id=message.id,
                    error={"message": str(e)}
                )
        else:
            raise ValueError(f"No handler for method: {method}")
    
    def _generate_id(self) -> str:
        import uuid
        return str(uuid.uuid4())