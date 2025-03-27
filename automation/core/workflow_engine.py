"""
Workflow Engine for Dana AI

This module handles the core automation workflow engine that orchestrates the entire
message processing, AI response generation, and task management processes.
"""

import logging
import asyncio
from typing import Dict, Any, List, Callable, Awaitable, Optional, Union, cast
from datetime import datetime

logger = logging.getLogger(__name__)

class WorkflowStep:
    """
    Represents a single step in a workflow process
    """
    def __init__(self, name: str, handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
                 required_inputs: Optional[List[str]] = None, 
                 optional_inputs: Optional[List[str]] = None,
                 output_keys: Optional[List[str]] = None):
        """
        Initialize a workflow step
        
        Args:
            name: The name of the step
            handler: Async function that processes the step
            required_inputs: List of input keys this step requires
            optional_inputs: List of optional input keys
            output_keys: List of keys this step produces in its output
        """
        self.name = name
        self.handler = handler
        self.required_inputs = required_inputs or []
        self.optional_inputs = optional_inputs or []
        self.output_keys = output_keys or []

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute this workflow step
        
        Args:
            context: The workflow context data
            
        Returns:
            Updated context with this step's outputs
        """
        logger.debug(f"Executing workflow step: {self.name}")
        
        # Verify required inputs
        missing_inputs = [key for key in self.required_inputs if key not in context]
        if missing_inputs:
            raise ValueError(f"Missing required inputs for step '{self.name}': {missing_inputs}")
        
        # Execute the handler
        start_time = datetime.now()
        try:
            result = await self.handler(context)
            
            # Verify the handler returned all expected outputs
            missing_outputs = [key for key in self.output_keys if key not in result]
            if missing_outputs:
                logger.warning(f"Step '{self.name}' did not return expected outputs: {missing_outputs}")
            
            # Update context with results
            context.update(result)
            
            # Add execution metadata
            duration = (datetime.now() - start_time).total_seconds()
            if '_metadata' not in context:
                context['_metadata'] = {}
            if 'step_execution' not in context['_metadata']:
                context['_metadata']['step_execution'] = {}
            
            context['_metadata']['step_execution'][self.name] = {
                'start_time': start_time.isoformat(),
                'duration_seconds': duration,
                'status': 'success'
            }
            
            logger.debug(f"Completed step '{self.name}' in {duration:.2f}s")
            return context
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error executing step '{self.name}': {str(e)}", exc_info=True)
            
            # Record error in metadata
            if '_metadata' not in context:
                context['_metadata'] = {}
            if 'step_execution' not in context['_metadata']:
                context['_metadata']['step_execution'] = {}
                
            context['_metadata']['step_execution'][self.name] = {
                'start_time': start_time.isoformat(),
                'duration_seconds': duration,
                'status': 'error',
                'error': str(e)
            }
            
            raise


class Workflow:
    """
    Represents a complete workflow of multiple steps
    """
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a workflow
        
        Args:
            name: The name of the workflow
            description: A description of what this workflow does
        """
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        
    def add_step(self, step: WorkflowStep) -> 'Workflow':
        """
        Add a step to this workflow
        
        Args:
            step: The workflow step to add
            
        Returns:
            Self for method chaining
        """
        self.steps.append(step)
        return self
        
    async def execute(self, initial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the entire workflow
        
        Args:
            initial_context: Optional initial context data
            
        Returns:
            The final context after all steps have executed
        """
        context: Dict[str, Any] = initial_context or {}
        
        # Add workflow metadata
        if '_metadata' not in context:
            context['_metadata'] = {}
        
        context['_metadata']['workflow'] = {
            'name': self.name,
            'start_time': datetime.now().isoformat(),
            'num_steps': len(self.steps)
        }
        
        logger.info(f"Starting workflow '{self.name}' with {len(self.steps)} steps")
        
        # Execute each step in sequence
        try:
            for step in self.steps:
                context = await step.execute(context)
                
            # Record completion
            duration = (datetime.now() - datetime.fromisoformat(context['_metadata']['workflow']['start_time'])).total_seconds()
            context['_metadata']['workflow']['end_time'] = datetime.now().isoformat()
            context['_metadata']['workflow']['duration_seconds'] = duration
            context['_metadata']['workflow']['status'] = 'success'
            
            logger.info(f"Completed workflow '{self.name}' in {duration:.2f}s")
            return context
            
        except Exception as e:
            # Record error in metadata
            duration = (datetime.now() - datetime.fromisoformat(context['_metadata']['workflow']['start_time'])).total_seconds()
            context['_metadata']['workflow']['end_time'] = datetime.now().isoformat()
            context['_metadata']['workflow']['duration_seconds'] = duration
            context['_metadata']['workflow']['status'] = 'error'
            context['_metadata']['workflow']['error'] = str(e)
            
            logger.error(f"Error in workflow '{self.name}': {str(e)}", exc_info=True)
            raise


class WorkflowEngine:
    """
    Engine that manages and executes workflows
    """
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.default_context: Dict[str, Any] = {}
    
    def register_workflow(self, workflow: Workflow):
        """
        Register a workflow with this engine
        
        Args:
            workflow: The workflow to register
        """
        self.workflows[workflow.name] = workflow
        logger.info(f"Registered workflow: {workflow.name}")
        
    def set_default_context(self, context: Dict[str, Any]):
        """
        Set default context values for all workflow executions
        
        Args:
            context: Default context values
        """
        self.default_context = context
        
    async def execute_workflow(self, workflow_name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a registered workflow by name
        
        Args:
            workflow_name: Name of the workflow to execute
            context: Optional context to merge with default context
            
        Returns:
            The final context after workflow execution
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")
            
        # Merge with default context
        full_context: Dict[str, Any] = {**self.default_context}
        if context:
            full_context.update(context)
            
        # Add execution ID
        if '_metadata' not in full_context:
            full_context['_metadata'] = {}
        full_context['_metadata']['execution_id'] = f"{workflow_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(full_context)}"
        
        # Execute the workflow
        logger.info(f"Executing workflow: {workflow_name}")
        return await self.workflows[workflow_name].execute(full_context)


# Create a global workflow engine instance
engine = WorkflowEngine()


def create_workflow(name: str, description: str = "") -> Workflow:
    """
    Convenience function to create and register a new workflow
    
    Args:
        name: The workflow name
        description: Optional workflow description
        
    Returns:
        The created workflow for further configuration
    """
    workflow = Workflow(name, description)
    engine.register_workflow(workflow)
    return workflow


async def execute_workflow(workflow_name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to execute a workflow by name
    
    Args:
        workflow_name: Name of the workflow to execute
        context: Optional execution context
        
    Returns:
        The workflow execution result
    """
    return await engine.execute_workflow(workflow_name, context)