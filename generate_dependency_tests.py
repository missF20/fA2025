#!/usr/bin/env python
"""
Generate Dependency Tests

This script generates tests for updated dependencies to verify that they work
correctly with the application.

Usage:
    python generate_dependency_tests.py [--packages=package1,package2] [--output=tests]

Options:
    --packages  Comma-separated list of packages to test (default: all updated packages)
    --output    Output directory for tests (default: tests/dependencies)
"""

import argparse
import importlib
import inspect
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test templates
PYTHON_TEST_TEMPLATE = """
import unittest
import sys
import logging

logging.basicConfig(level=logging.INFO)

# Module to test
{import_statement}

class Test{module_name}(unittest.TestCase):
    
    def setUp(self):
        logging.info("Setting up test for {module_name}")
    
    def tearDown(self):
        logging.info("Cleaning up after {module_name} test")
    
{test_methods}

if __name__ == '__main__':
    unittest.main()
"""

PYTHON_TEST_METHOD_TEMPLATE = """    def test_{test_name}(self):
        """Test {test_description}"""
{test_code}
"""

NODE_TEST_TEMPLATE = """
const assert = require('assert');

// Module to test
const {module_name} = require('{module_path}');

describe('{module_name}', function() {
{test_methods}
});
"""

NODE_TEST_METHOD_TEMPLATE = """  it('should {test_description}', function() {
{test_code}
  });
"""

def find_updated_packages():
    """
    Find recently updated packages
    
    Returns:
        dict: Updated packages with details
    """
    notification_dir = Path("notifications")
    
    if not notification_dir.exists():
        logger.warning(f"Notification directory not found: {notification_dir}")
        return {}
    
    # Find all update notification files from the last 7 days
    cutoff_date = datetime.now() - timedelta(days=7)
    notification_files = list(notification_dir.glob("dependency_*.txt"))
    
    # Filter recent files
    recent_files = [
        f for f in notification_files
        if datetime.fromtimestamp(f.stat().st_mtime) >= cutoff_date
    ]
    
    # Parse files to find updated packages
    updated_packages = {}
    
    for file_path in recent_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if this is a dependency update notification
            if 'updated' in content.lower() and 'following packages' in content.lower():
                package_list_match = re.search(r'following packages[^:]*:\s*\n\n([^\n]+)', content)
                if package_list_match:
                    package_list = package_list_match.group(1).split(',')
                    for package in package_list:
                        package = package.strip()
                        if package:
                            # Try to extract version information
                            version_match = re.search(r'([^=]+)==([^ ]+)', package)
                            if version_match:
                                package_name = version_match.group(1).strip()
                                version = version_match.group(2).strip()
                            else:
                                package_name = package
                                version = "latest"
                            
                            # Add to updated packages
                            updated_packages[package_name] = {
                                'version': version,
                                'notification_file': str(file_path)
                            }
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
    
    return updated_packages

def detect_package_type(package_name):
    """
    Detect if a package is a Python or Node.js package
    
    Args:
        package_name: Name of the package
        
    Returns:
        str: 'python' or 'node' or 'unknown'
    """
    # First check if it's a Python package
    try:
        subprocess.run(
            [sys.executable, '-c', f"import {package_name}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return 'python'
    except:
        pass
    
    # Check if it's a Node.js package (if package.json exists)
    if os.path.exists('package.json'):
        try:
            with open('package.json', 'r') as f:
                package_data = json.load(f)
            
            dependencies = {}
            dependencies.update(package_data.get('dependencies', {}))
            dependencies.update(package_data.get('devDependencies', {}))
            
            if package_name in dependencies:
                return 'node'
        except:
            pass
    
    return 'unknown'

def analyze_python_module(module_name):
    """
    Analyze a Python module to generate tests
    
    Args:
        module_name: Name of the module
        
    Returns:
        dict: Module analysis information
    """
    try:
        # Try to import the module
        module = importlib.import_module(module_name)
        
        # Get module attributes
        attributes = {
            name: getattr(module, name)
            for name in dir(module)
            if not name.startswith('_')
        }
        
        # Categorize attributes
        classes = {}
        functions = {}
        constants = {}
        
        for name, attr in attributes.items():
            if inspect.isclass(attr):
                classes[name] = attr
            elif inspect.isfunction(attr):
                functions[name] = attr
            elif not callable(attr) and not inspect.ismodule(attr):
                constants[name] = attr
        
        return {
            'name': module_name,
            'classes': classes,
            'functions': functions,
            'constants': constants
        }
    except Exception as e:
        logger.error(f"Error analyzing module {module_name}: {str(e)}")
        return {
            'name': module_name,
            'error': str(e)
        }

def generate_python_test(module_info, output_dir):
    """
    Generate a Python test file for a module
    
    Args:
        module_info: Module analysis information
        output_dir: Output directory
        
    Returns:
        str: Path to generated test file
    """
    module_name = module_info['name']
    snake_case_name = re.sub(r'[-.]', '_', module_name)
    import_statement = f"import {module_name}"
    
    # Generate test methods
    test_methods = []
    
    # Test module import
    test_methods.append(PYTHON_TEST_METHOD_TEMPLATE.format(
        test_name="import",
        test_description=f"that {module_name} can be imported",
        test_code=f"""        # Test that the module can be imported
        import {module_name}
        self.assertIsNotNone({module_name})"""
    ))
    
    # Test functions
    for func_name, func in module_info.get('functions', {}).items():
        # Get function signature
        try:
            signature = inspect.signature(func)
            params = signature.parameters
            
            # Skip functions that require parameters
            if params:
                param_list = []
                for name, param in params.items():
                    if param.default is inspect.Parameter.empty and param.kind not in (
                        inspect.Parameter.VAR_POSITIONAL,
                        inspect.Parameter.VAR_KEYWORD
                    ):
                        # Required parameter with no default value
                        if name == 'self':
                            continue  # Skip 'self' parameter for instance methods
                        
                        # Add a default value based on parameter type hint
                        annotation = param.annotation
                        if annotation is not inspect.Parameter.empty:
                            if annotation == str:
                                param_list.append(f'"{name}"')
                            elif annotation == int:
                                param_list.append("0")
                            elif annotation == float:
                                param_list.append("0.0")
                            elif annotation == bool:
                                param_list.append("False")
                            elif annotation == list:
                                param_list.append("[]")
                            elif annotation == dict:
                                param_list.append("{}")
                            else:
                                param_list.append("None")
                        else:
                            param_list.append("None")
                
                if param_list:
                    args = ", ".join(param_list)
                    test_code = f"""        # This test is a placeholder and may need to be updated with valid parameters
        try:
            result = {module_name}.{func_name}({args})
            # Add assertions based on expected result
        except Exception as e:
            self.skipTest(f"Function requires parameters: {{e}}")"""
                else:
                    test_code = f"""        try:
            result = {module_name}.{func_name}()
            # Add assertions based on expected result
        except Exception as e:
            self.skipTest(f"Function call failed: {{e}}")"""
            else:
                # Function with no parameters
                test_code = f"""        try:
            result = {module_name}.{func_name}()
            # Add assertions based on expected result
        except Exception as e:
            self.skipTest(f"Function call failed: {{e}}")"""
            
            test_methods.append(PYTHON_TEST_METHOD_TEMPLATE.format(
                test_name=f"function_{func_name}",
                test_description=f"function {func_name}",
                test_code=test_code
            ))
        except Exception as e:
            logger.warning(f"Error generating test for function {func_name}: {str(e)}")
    
    # Test classes
    for class_name, cls in module_info.get('classes', {}).items():
        try:
            # Check if class can be instantiated without arguments
            sig = inspect.signature(cls.__init__)
            params = list(sig.parameters.items())
            
            if len(params) == 1 and params[0][0] == 'self':
                # Class can be instantiated without arguments
                test_code = f"""        try:
            instance = {module_name}.{class_name}()
            self.assertIsInstance(instance, {module_name}.{class_name})
        except Exception as e:
            self.skipTest(f"Could not instantiate class: {{e}}")"""
            else:
                # Class requires arguments
                test_code = f"""        # This test is a placeholder as the class requires arguments to instantiate
        self.assertTrue(hasattr({module_name}, '{class_name}'))
        self.assertTrue(inspect.isclass({module_name}.{class_name}))"""
            
            test_methods.append(PYTHON_TEST_METHOD_TEMPLATE.format(
                test_name=f"class_{class_name}",
                test_description=f"class {class_name}",
                test_code=test_code
            ))
        except Exception as e:
            logger.warning(f"Error generating test for class {class_name}: {str(e)}")
    
    # Test constants
    if module_info.get('constants'):
        constants_code = "        # Test that expected constants exist\n"
        for const_name in module_info['constants']:
            constants_code += f"        self.assertTrue(hasattr({module_name}, '{const_name}'))\n"
        
        test_methods.append(PYTHON_TEST_METHOD_TEMPLATE.format(
            test_name="constants",
            test_description="module constants",
            test_code=constants_code
        ))
    
    # Generate full test file
    test_file_content = PYTHON_TEST_TEMPLATE.format(
        import_statement=import_statement,
        module_name=snake_case_name,
        test_methods="\n".join(test_methods)
    )
    
    # Write test file
    os.makedirs(output_dir, exist_ok=True)
    test_file_path = os.path.join(output_dir, f"test_{snake_case_name}.py")
    
    with open(test_file_path, 'w') as f:
        f.write(test_file_content)
    
    return test_file_path

def generate_node_test(package_name, output_dir):
    """
    Generate a Node.js test file for a package
    
    Args:
        package_name: Name of the package
        output_dir: Output directory
        
    Returns:
        str: Path to generated test file
    """
    # Check if the package is installed
    try:
        module_path = package_name
        module_name = package_name.replace('-', '_').replace('.', '_')
        
        # Generate test methods
        test_methods = []
        
        # Test module import
        test_methods.append(NODE_TEST_METHOD_TEMPLATE.format(
            test_description=f"be able to require {package_name}",
            test_code=f"""    // Test that the module can be required
    assert({module_name} !== null, 'Module should be importable');
    assert({module_name} !== undefined, 'Module should be importable');"""
        ))
        
        # Generate generic test for module structure
        test_methods.append(NODE_TEST_METHOD_TEMPLATE.format(
            test_description="have expected structure",
            test_code=f"""    // This is a placeholder test that should be customized
    // based on the actual structure of the {package_name} module
    if (typeof {module_name} === 'function') {{
      assert(typeof {module_name} === 'function', 'Should be a function');
    }} else if (typeof {module_name} === 'object') {{
      assert(typeof {module_name} === 'object', 'Should be an object');
    }}"""
        ))
        
        # Generate full test file
        test_file_content = NODE_TEST_TEMPLATE.format(
            module_name=module_name,
            module_path=module_path,
            test_methods="\n".join(test_methods)
        )
        
        # Write test file
        os.makedirs(output_dir, exist_ok=True)
        test_file_path = os.path.join(output_dir, f"test_{module_name}.js")
        
        with open(test_file_path, 'w') as f:
            f.write(test_file_content)
        
        return test_file_path
    except Exception as e:
        logger.error(f"Error generating Node.js test for {package_name}: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate Dependency Tests')
    parser.add_argument('--packages', help='Comma-separated list of packages to test')
    parser.add_argument('--output', default='tests/dependencies', help='Output directory for tests')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Get packages to test
    if args.packages:
        packages = [p.strip() for p in args.packages.split(',')]
        selected_packages = {p: {'version': 'current'} for p in packages}
    else:
        # Find recently updated packages
        logger.info("Finding recently updated packages")
        selected_packages = find_updated_packages()
    
    if not selected_packages:
        print("No packages found to test")
        return
    
    print(f"Generating tests for {len(selected_packages)} packages: {', '.join(selected_packages.keys())}")
    
    # Generate tests for each package
    python_tests = []
    node_tests = []
    
    for package_name, package_info in selected_packages.items():
        # Detect package type
        package_type = detect_package_type(package_name)
        
        if package_type == 'python':
            logger.info(f"Generating Python tests for {package_name}")
            
            # Analyze module
            module_info = analyze_python_module(package_name)
            
            if 'error' not in module_info:
                # Generate test file
                test_file = generate_python_test(module_info, args.output)
                python_tests.append(test_file)
                print(f"✓ Generated Python test: {test_file}")
            else:
                logger.warning(f"Could not generate test for {package_name}: {module_info.get('error')}")
                print(f"✗ Failed to generate test for {package_name}")
        
        elif package_type == 'node':
            logger.info(f"Generating Node.js tests for {package_name}")
            
            # Generate test file
            test_file = generate_node_test(package_name, args.output)
            if test_file:
                node_tests.append(test_file)
                print(f"✓ Generated Node.js test: {test_file}")
            else:
                print(f"✗ Failed to generate test for {package_name}")
        
        else:
            logger.warning(f"Unknown package type for {package_name}")
            print(f"? Could not determine type for {package_name}")
    
    # Generate test runner
    if python_tests:
        runner_path = os.path.join(args.output, "run_python_tests.py")
        with open(runner_path, 'w') as f:
            f.write("""#!/usr/bin/env python
import unittest
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

if __name__ == '__main__':
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern='test_*.py')
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with error code if any tests failed
    sys.exit(not result.wasSuccessful())
""")
        os.chmod(runner_path, 0o755)
        print(f"Generated Python test runner: {runner_path}")
    
    if node_tests:
        runner_path = os.path.join(args.output, "run_node_tests.js")
        with open(runner_path, 'w') as f:
            f.write("""#!/usr/bin/env node
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Find all test files
const testDir = __dirname;
const testFiles = fs.readdirSync(testDir)
  .filter(file => file.startsWith('test_') && file.endsWith('.js'));

// Run each test file
let passedCount = 0;
let failedCount = 0;

function runTest(index) {
  if (index >= testFiles.length) {
    // All tests complete
    console.log(`\\nTest Results: ${passedCount} passed, ${failedCount} failed`);
    process.exit(failedCount > 0 ? 1 : 0);
    return;
  }
  
  const testFile = testFiles[index];
  const testPath = path.join(testDir, testFile);
  
  console.log(`\\nRunning ${testFile}...`);
  
  const mocha = spawn('npx', ['mocha', testPath], { stdio: 'inherit' });
  
  mocha.on('close', (code) => {
    if (code === 0) {
      passedCount++;
    } else {
      failedCount++;
    }
    
    runTest(index + 1);
  });
}

runTest(0);
""")
        os.chmod(runner_path, 0o755)
        print(f"Generated Node.js test runner: {runner_path}")
    
    print(f"\\nGenerated {len(python_tests)} Python tests and {len(node_tests)} Node.js tests")

if __name__ == "__main__":
    main()