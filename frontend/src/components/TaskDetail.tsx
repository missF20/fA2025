
import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

interface TaskDetailProps {
  taskId: string;
  onClose: () => void;
}

export const TaskDetail: React.FC<TaskDetailProps> = ({ taskId, onClose }) => {
  const [task, setTask] = useState<any>(null);
  const { token } = useAuth();

  useEffect(() => {
    fetchTaskDetails();
  }, [taskId]);

  const fetchTaskDetails = async () => {
    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setTask(data);
    } catch (error) {
      console.error('Error fetching task details:', error);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    try {
      await fetch(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: newStatus })
      });
      fetchTaskDetails();
    } catch (error) {
      console.error('Error updating task status:', error);
    }
  };

  if (!task) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Task Details</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ×
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="font-medium">Description</label>
            <p className="mt-1">{task.description}</p>
          </div>
          
          <div>
            <label className="font-medium">Status</label>
            <select
              value={task.status}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="mt-1 block w-full rounded border-gray-300"
            >
              <option value="todo">To Do</option>
              <option value="inProgress">In Progress</option>
              <option value="done">Done</option>
            </select>
          </div>
          
          <div>
            <label className="font-medium">Priority</label>
            <p className="mt-1">{task.priority}</p>
          </div>
          
          <div>
            <label className="font-medium">Platform</label>
            <p className="mt-1">{task.platform}</p>
          </div>
          
          <div>
            <label className="font-medium">Client</label>
            <p className="mt-1">{task.client_name}</p>
          </div>
          
          <div>
            <label className="font-medium">Created</label>
            <p className="mt-1">
              {new Date(task.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
