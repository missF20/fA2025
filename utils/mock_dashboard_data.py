"""
Mock Dashboard Data Utility

This module provides sample data for dashboard visualizations during development.
This is a temporary solution until the proper API endpoints are fully implemented.
"""

def get_mock_dashboard_data():
    """
    Get mock dashboard data for the frontend visualization components
    """
    return {
        "totalResponses": 142,
        "responsesBreakdown": {
            "facebook": 48,
            "instagram": 35,
            "whatsapp": 42,
            "slack": 17,
            "email": 10
        },
        "completedTasks": 86,
        "completedTasksBreakdown": {
            "facebook": 29,
            "instagram": 21,
            "whatsapp": 25,
            "slack": 7,
            "email": 4
        },
        "pendingTasks": [
            {
                "id": "1",
                "task": "Follow up on shipping delay",
                "client": {
                    "name": "John Smith",
                    "company": "Acme Corp"
                },
                "timestamp": "2025-05-04T14:30:00Z",
                "platform": "facebook",
                "priority": "high"
            },
            {
                "id": "2",
                "task": "Respond to refund request",
                "client": {
                    "name": "Maria Garcia",
                    "company": "Global Tech"
                },
                "timestamp": "2025-05-05T09:15:00Z",
                "platform": "whatsapp",
                "priority": "medium"
            },
            {
                "id": "3",
                "task": "Address product information inquiry",
                "client": {
                    "name": "James Chen",
                    "company": "Summit Solutions"
                },
                "timestamp": "2025-05-06T11:45:00Z",
                "platform": "instagram",
                "priority": "low"
            }
        ],
        "escalatedTasks": [
            {
                "id": "4",
                "task": "Urgent login issue resolution",
                "client": {
                    "name": "Sarah Johnson",
                    "company": "First Bank"
                },
                "timestamp": "2025-05-05T13:20:00Z",
                "platform": "facebook",
                "priority": "high",
                "reason": "Customer unable to access account for 48 hours"
            },
            {
                "id": "5",
                "task": "Critical payment failure",
                "client": {
                    "name": "Alex Martinez",
                    "company": "Blue Sky Airlines"
                },
                "timestamp": "2025-05-06T08:50:00Z",
                "platform": "whatsapp",
                "priority": "high",
                "reason": "Multiple payment attempts failed, customer needs immediate assistance"
            }
        ],
        "totalChats": 215,
        "chatsBreakdown": {
            "facebook": 78,
            "instagram": 62,
            "whatsapp": 55,
            "slack": 12,
            "email": 8
        },
        "peopleInteracted": [
            {
                "id": "101",
                "name": "David Wilson",
                "company": "Sunset Retail",
                "timestamp": "2025-05-07T09:30:00Z",
                "platform": "facebook"
            },
            {
                "id": "102",
                "name": "Linda Kim",
                "company": "Green Energy Co.",
                "timestamp": "2025-05-07T10:15:00Z",
                "platform": "instagram"
            },
            {
                "id": "103",
                "name": "Robert Miller",
                "company": "Metro Logistics",
                "timestamp": "2025-05-07T11:05:00Z",
                "platform": "whatsapp"
            }
        ],
        "responseTime": "1m 24s",
        "topIssues": [
            {
                "id": "201",
                "name": "Login problems",
                "count": 24,
                "trend": -15,
                "platform": "facebook"
            },
            {
                "id": "202",
                "name": "Payment issues",
                "count": 18,
                "trend": 5,
                "platform": "whatsapp"
            },
            {
                "id": "203",
                "name": "Product information",
                "count": 15,
                "trend": -7,
                "platform": "instagram"
            },
            {
                "id": "204",
                "name": "Shipping delays",
                "count": 12,
                "trend": 12,
                "platform": "email"
            },
            {
                "id": "205",
                "name": "Return process",
                "count": 9,
                "trend": -3,
                "platform": "facebook"
            }
        ],
        "interactionsByType": [
            {
                "type": "Inquiries",
                "count": 87
            },
            {
                "type": "Support",
                "count": 65
            },
            {
                "type": "Feedback",
                "count": 42
            },
            {
                "type": "Complaints",
                "count": 21
            }
        ],
        "allowedPlatforms": ["facebook", "instagram", "whatsapp", "slack", "email"],
        "sentimentData": [
            {
                "id": "positive",
                "type": "positive",
                "count": 120,
                "trend": 8,
                "percentage": 55.8
            },
            {
                "id": "neutral",
                "type": "neutral",
                "count": 65,
                "trend": -3,
                "percentage": 30.2
            },
            {
                "id": "negative",
                "type": "negative",
                "count": 30,
                "trend": -12,
                "percentage": 14.0
            }
        ]
    }