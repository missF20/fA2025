"""
Dana AI Platform - Database Schema Validator

This module provides tools to validate the database schema and detect drift
between the expected schema in the codebase and the actual database schema.
"""

import logging
import json
import os
from datetime import datetime
from utils.db_connection import get_direct_connection
from utils.exceptions import DatabaseAccessError

logger = logging.getLogger(__name__)

# Define expected schema for each table
EXPECTED_SCHEMA = {
    'integration_configs': {
        'columns': {
            'id': {'type': 'uuid', 'nullable': False, 'primary_key': True},
            'user_id': {'type': 'uuid', 'nullable': False},
            'integration_type': {'type': 'varchar', 'nullable': False},
            'config': {'type': 'jsonb', 'nullable': False},
            'status': {'type': 'varchar', 'nullable': False},
            'date_created': {'type': 'timestamp', 'nullable': False},
            'date_updated': {'type': 'timestamp', 'nullable': False}
        },
        'constraints': [
            {'type': 'unique', 'columns': ['user_id', 'integration_type']},
            {'type': 'foreign_key', 'columns': ['user_id'], 'references': 'users(id)'}
        ]
    },
    'users': {
        'columns': {
            'id': {'type': 'uuid', 'nullable': False, 'primary_key': True},
            'email': {'type': 'varchar', 'nullable': False},
            'username': {'type': 'varchar', 'nullable': True},
            'auth_id': {'type': 'varchar', 'nullable': True},
            'is_admin': {'type': 'boolean', 'nullable': False, 'default': False},
            'date_created': {'type': 'timestamp', 'nullable': False},
            'date_updated': {'type': 'timestamp', 'nullable': False}
        },
        'constraints': [
            {'type': 'unique', 'columns': ['email']},
            {'type': 'unique', 'columns': ['auth_id']}
        ]
    },
    'token_usage': {
        'columns': {
            'id': {'type': 'uuid', 'nullable': False, 'primary_key': True},
            'user_id': {'type': 'uuid', 'nullable': False},
            'tokens_used': {'type': 'integer', 'nullable': False},
            'model': {'type': 'varchar', 'nullable': True},
            'date_created': {'type': 'timestamp', 'nullable': False}
        },
        'constraints': [
            {'type': 'foreign_key', 'columns': ['user_id'], 'references': 'users(id)'}
        ]
    },
    'knowledge_files': {
        'columns': {
            'id': {'type': 'uuid', 'nullable': False, 'primary_key': True},
            'user_id': {'type': 'uuid', 'nullable': False},
            'title': {'type': 'varchar', 'nullable': False},
            'content': {'type': 'text', 'nullable': True},
            'file_type': {'type': 'varchar', 'nullable': False},
            'date_created': {'type': 'timestamp', 'nullable': False},
            'date_updated': {'type': 'timestamp', 'nullable': False}
        },
        'constraints': [
            {'type': 'foreign_key', 'columns': ['user_id'], 'references': 'users(id)'}
        ]
    }
}

def get_database_schema():
    """
    Get the actual database schema
    
    Returns:
        dict: Database schema in the format {'table_name': {'columns': {...}, 'constraints': [...]}}
    """
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        schema = {}
        
        for table in tables:
            # Get columns for table
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
            """, (table,))
            
            columns = {}
            for row in cursor.fetchall():
                column_name, data_type, is_nullable, column_default = row
                columns[column_name] = {
                    'type': data_type,
                    'nullable': is_nullable == 'YES',
                    'default': column_default
                }
                
            # Get primary key for table
            cursor.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary
            """, (table,))
            
            primary_keys = [row[0] for row in cursor.fetchall()]
            for pk in primary_keys:
                if pk in columns:
                    columns[pk]['primary_key'] = True
                    
            # Get foreign keys for table
            cursor.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = %s
            """, (table,))
            
            constraints = []
            for row in cursor.fetchall():
                column_name, foreign_table, foreign_column = row
                constraints.append({
                    'type': 'foreign_key',
                    'columns': [column_name],
                    'references': f"{foreign_table}({foreign_column})"
                })
                
            # Get unique constraints for table
            cursor.execute("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'UNIQUE'
                  AND tc.table_name = %s
                ORDER BY tc.constraint_name, kcu.ordinal_position
            """, (table,))
            
            unique_constraints = {}
            for row in cursor.fetchall():
                constraint_name, column_name = row
                if constraint_name not in unique_constraints:
                    unique_constraints[constraint_name] = []
                unique_constraints[constraint_name].append(column_name)
                
            for columns_list in unique_constraints.values():
                constraints.append({
                    'type': 'unique',
                    'columns': columns_list
                })
                
            schema[table] = {
                'columns': columns,
                'constraints': constraints
            }
            
        cursor.close()
        conn.close()
        
        return schema
        
    except Exception as e:
        logger.exception(f"Error getting database schema: {str(e)}")
        raise DatabaseAccessError(f"Error getting database schema: {str(e)}")

def validate_schema():
    """
    Validate the database schema against expected schema
    
    Returns:
        dict: Validation results with drift information
    """
    try:
        # Get actual schema
        actual_schema = get_database_schema()
        
        # Validate against expected schema
        drift = {
            'missing_tables': [],
            'extra_tables': [],
            'table_drift': {}
        }
        
        # Check for missing tables
        for table_name in EXPECTED_SCHEMA:
            if table_name not in actual_schema:
                drift['missing_tables'].append(table_name)
                
        # Check for extra tables
        for table_name in actual_schema:
            if table_name not in EXPECTED_SCHEMA:
                drift['extra_tables'].append(table_name)
                
        # Check for drift in tables that exist in both
        for table_name in EXPECTED_SCHEMA:
            if table_name not in actual_schema:
                continue
                
            expected = EXPECTED_SCHEMA[table_name]
            actual = actual_schema[table_name]
            
            table_drift = {
                'missing_columns': [],
                'extra_columns': [],
                'type_mismatches': [],
                'missing_constraints': [],
                'extra_constraints': []
            }
            
            # Check columns
            for column_name, expected_column in expected['columns'].items():
                if column_name not in actual['columns']:
                    table_drift['missing_columns'].append(column_name)
                else:
                    actual_column = actual['columns'][column_name]
                    # Check type
                    if expected_column.get('type', '').lower() not in actual_column.get('type', '').lower():
                        table_drift['type_mismatches'].append({
                            'column': column_name,
                            'expected': expected_column.get('type'),
                            'actual': actual_column.get('type')
                        })
                    # Could add more checks here (nullable, default, etc.)
                    
            # Check for extra columns
            for column_name in actual['columns']:
                if column_name not in expected['columns']:
                    table_drift['extra_columns'].append(column_name)
                    
            # Check constraints (simplified)
            # This is a simplified check and might not catch all constraints correctly
            
            # For brevity, we'll just check foreign keys
            expected_fks = [c for c in expected.get('constraints', []) if c.get('type') == 'foreign_key']
            actual_fks = [c for c in actual.get('constraints', []) if c.get('type') == 'foreign_key']
            
            # Check missing foreign keys (very simple check)
            for expected_fk in expected_fks:
                found = False
                for actual_fk in actual_fks:
                    if expected_fk.get('columns') == actual_fk.get('columns') and expected_fk.get('references') == actual_fk.get('references'):
                        found = True
                        break
                        
                if not found:
                    table_drift['missing_constraints'].append({
                        'type': 'foreign_key',
                        'columns': expected_fk.get('columns'),
                        'references': expected_fk.get('references')
                    })
                    
            # If there's any drift for this table, add it to the overall drift
            if any(table_drift.values()):
                drift['table_drift'][table_name] = table_drift
                
        # Generate summary
        drift['summary'] = {
            'missing_table_count': len(drift['missing_tables']),
            'extra_table_count': len(drift['extra_tables']),
            'drifted_table_count': len(drift['table_drift']),
            'timestamp': datetime.now().isoformat()
        }
        
        # Calculate overall drift severity
        severity = 'none'
        if drift['missing_tables'] or any(
            'missing_columns' in table_drift and table_drift['missing_columns'] 
            for table_drift in drift['table_drift'].values()
        ):
            severity = 'critical'
        elif drift['table_drift']:
            severity = 'moderate'
        elif drift['extra_tables']:
            severity = 'low'
            
        drift['summary']['severity'] = severity
        
        return drift
        
    except Exception as e:
        logger.exception(f"Error validating schema: {str(e)}")
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def save_validation_report(drift):
    """
    Save schema validation report to file
    
    Args:
        drift: Schema validation results
        
    Returns:
        str: Path to saved report
    """
    try:
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(os.getcwd(), 'reports')
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"schema_validation_{timestamp}.json"
        filepath = os.path.join(reports_dir, filename)
        
        # Save report
        with open(filepath, 'w') as f:
            json.dump(drift, f, indent=2)
            
        return filepath
        
    except Exception as e:
        logger.exception(f"Error saving validation report: {str(e)}")
        return None

def get_latest_validation_report():
    """
    Get the latest schema validation report
    
    Returns:
        dict: Latest schema validation report or None if not found
    """
    try:
        # Check if reports directory exists
        reports_dir = os.path.join(os.getcwd(), 'reports')
        if not os.path.exists(reports_dir):
            return None
            
        # Get list of report files
        report_files = [f for f in os.listdir(reports_dir) if f.startswith('schema_validation_') and f.endswith('.json')]
        if not report_files:
            return None
            
        # Get latest report
        latest_report = max(report_files)
        filepath = os.path.join(reports_dir, latest_report)
        
        # Load report
        with open(filepath, 'r') as f:
            report = json.load(f)
            
        return report
        
    except Exception as e:
        logger.exception(f"Error getting latest validation report: {str(e)}")
        return None

if __name__ == '__main__':
    # Run validation when script is executed directly
    print("Validating database schema...")
    drift = validate_schema()
    report_path = save_validation_report(drift)
    
    print(f"Schema validation completed with severity: {drift['summary']['severity']}")
    print(f"Report saved to: {report_path}")
    
    if drift['summary']['severity'] != 'none':
        print("\nDrift Summary:")
        if drift['missing_tables']:
            print(f"- Missing tables: {', '.join(drift['missing_tables'])}")
        if drift['extra_tables']:
            print(f"- Extra tables: {', '.join(drift['extra_tables'])}")
        for table, table_drift in drift['table_drift'].items():
            print(f"\nTable '{table}' drift:")
            if table_drift['missing_columns']:
                print(f"- Missing columns: {', '.join(table_drift['missing_columns'])}")
            if table_drift['extra_columns']:
                print(f"- Extra columns: {', '.join(table_drift['extra_columns'])}")
            if table_drift['type_mismatches']:
                for mismatch in table_drift['type_mismatches']:
                    print(f"- Column '{mismatch['column']}' type mismatch: expected {mismatch['expected']}, actual {mismatch['actual']}")
    else:
        print("No schema drift detected!")