"""
Test Integration Service

A simple script to test the Integration Service
"""

from utils.integration_service import IntegrationService
from models import IntegrationType, IntegrationStatus

def test_integration_service():
    """
    Test the IntegrationService utility functions
    """
    # Use a real user ID from the database because of foreign key constraint
    # The user_id in integration_configs table is an integer with a foreign key to users table
    test_user_id = 1  # Using an existing user ID from the database
    
    # 1. Create a test integration
    print("\n1. Creating test integration...")
    test_config = {
        "api_key": "test_api_key_123",
        "enabled": True,
        "test_setting": "test_value"
    }
    
    result = IntegrationService.create_integration(
        user_id=test_user_id,
        integration_type=IntegrationType.SLACK.value,
        config=test_config,
        status=IntegrationStatus.ACTIVE.value
    )
    
    if result:
        print(f"Integration created successfully: {result}")
    else:
        print("Failed to create integration")
    
    # 2. Get the integration we just created
    print("\n2. Getting test integration...")
    integration = IntegrationService.get_integration(
        user_id=test_user_id,
        integration_type=IntegrationType.SLACK.value
    )
    
    if integration:
        print(f"Integration retrieved successfully: {integration}")
    else:
        print("Failed to retrieve integration")
    
    # 3. Update the integration
    print("\n3. Updating test integration...")
    updated_config = {
        "api_key": "updated_api_key_456",
        "enabled": True,
        "test_setting": "updated_value",
        "new_setting": "new_value"
    }
    
    updated = IntegrationService.update_integration(
        user_id=test_user_id,
        integration_type=IntegrationType.SLACK.value,
        config=updated_config
    )
    
    if updated:
        print(f"Integration updated successfully: {updated}")
    else:
        print("Failed to update integration")
    
    # 4. Get all integrations for the user
    print("\n4. Getting all integrations for user...")
    integrations = IntegrationService.get_user_integrations(user_id=test_user_id)
    
    if integrations:
        print(f"Retrieved {len(integrations)} integrations for user")
        for i, integration in enumerate(integrations):
            print(f"Integration {i+1}: {integration}")
    else:
        print("No integrations found for user")
    
    # 5. Update integration status
    print("\n5. Updating integration status...")
    status_updated = IntegrationService.update_integration_status(
        user_id=test_user_id,
        integration_type=IntegrationType.SLACK.value,
        status=IntegrationStatus.PENDING.value
    )
    
    if status_updated:
        print("Integration status updated successfully")
    else:
        print("Failed to update integration status")
        
    # Check the updated status
    integration = IntegrationService.get_integration(
        user_id=test_user_id,
        integration_type=IntegrationType.SLACK.value
    )
    if integration:
        print(f"Integration status now: {integration['status']}")
    
    # 6. Get integration counts
    print("\n6. Getting integration counts...")
    counts = IntegrationService.get_integration_counts()
    
    if counts:
        print(f"Integration counts: {counts}")
    else:
        print("No integration counts available")
    
    # 7. Delete the test integration
    print("\n7. Deleting test integration...")
    deleted = IntegrationService.delete_integration(
        user_id=test_user_id,
        integration_type=IntegrationType.SLACK.value
    )
    
    if deleted:
        print("Integration deleted successfully")
    else:
        print("Failed to delete integration")
    
    # Verify deletion
    integration = IntegrationService.get_integration(
        user_id=test_user_id,
        integration_type=IntegrationType.SLACK.value
    )
    
    if integration:
        print("Warning: Integration still exists after deletion")
    else:
        print("Verified: Integration no longer exists")
        
    print("\nIntegration Service test completed")

if __name__ == "__main__":
    test_integration_service()