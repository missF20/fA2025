"""
PDF Analysis API Routes

This module provides API endpoints for advanced PDF analysis using AI.
"""

import os
import logging
import base64
import tempfile
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename

from utils.auth import token_required
from utils.pdf_analyzer import PDFAnalyzer
from utils.file_parser import FileParser

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
pdf_analysis_bp = Blueprint('pdf_analysis', __name__, url_prefix='/api/pdf-analysis')

# Initialize PDF analyzer
analyzer = PDFAnalyzer()

@pdf_analysis_bp.route('/analyze', methods=['POST'])
@token_required
def analyze_pdf():
    """
    Analyze a PDF document
    
    Accepts PDF as file upload or base64-encoded string
    """
    try:
        # Check for required parameters
        if not request.json and not request.files:
            return jsonify({
                "success": False,
                "error": "Either a file upload or JSON with base64 PDF data is required"
            }), 400
            
        # Get analysis options
        analysis_types = request.args.get('types', 'summary,key_info,entities')
        analysis_types = [t.strip() for t in analysis_types.split(',')]
        
        # Get the PDF data - either from file upload or base64
        pdf_data = None
        
        # Method 1: File upload
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file.filename == '':
                return jsonify({
                    "success": False,
                    "error": "No file selected"
                }), 400
                
            if not pdf_file.filename.lower().endswith('.pdf'):
                return jsonify({
                    "success": False,
                    "error": "File must be a PDF"
                }), 400
                
            # Read the file data
            pdf_data = pdf_file.read()
            
        # Method 2: Base64 encoded data
        elif request.json and 'pdf_base64' in request.json:
            base64_data = request.json['pdf_base64']
            
            # Remove data URL prefix if present
            if ';base64,' in base64_data:
                base64_data = base64_data.split(';base64,')[1]
                
            try:
                pdf_data = base64.b64decode(base64_data)
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Invalid base64 data: {str(e)}"
                }), 400
                
        # Method 3: From a URL
        elif request.json and 'pdf_url' in request.json:
            # This feature would require implementing URL fetching functionality
            return jsonify({
                "success": False,
                "error": "PDF URL parsing is not implemented yet"
            }), 501
        
        else:
            return jsonify({
                "success": False,
                "error": "No PDF data provided"
            }), 400
            
        # Validate PDF data
        if not pdf_data or len(pdf_data) == 0:
            return jsonify({
                "success": False,
                "error": "Empty PDF data"
            }), 400
            
        # Perform the analysis
        result = analyzer.analyze_document(pdf_data, analysis_types)
        
        # Add user information to the response
        if hasattr(g, 'user_id'):
            result['user_id'] = g.user_id
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in PDF analysis: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }), 500

@pdf_analysis_bp.route('/summary', methods=['POST'])
@token_required
def summarize_pdf():
    """Generate a summary of a PDF document"""
    try:
        # Similar setup to analyze_pdf but focused on summary only
        if not request.json and not request.files:
            return jsonify({
                "success": False,
                "error": "Either a file upload or JSON with base64 PDF data is required"
            }), 400
            
        # Get the PDF data
        pdf_data = None
        
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file.filename == '' or not pdf_file.filename.lower().endswith('.pdf'):
                return jsonify({
                    "success": False,
                    "error": "Invalid PDF file"
                }), 400
                
            pdf_data = pdf_file.read()
            
        elif request.json and 'pdf_base64' in request.json:
            base64_data = request.json['pdf_base64']
            if ';base64,' in base64_data:
                base64_data = base64_data.split(';base64,')[1]
                
            try:
                pdf_data = base64.b64decode(base64_data)
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Invalid base64 data: {str(e)}"
                }), 400
        else:
            return jsonify({
                "success": False, 
                "error": "No PDF data provided"
            }), 400
            
        # Validate PDF data
        if not pdf_data or len(pdf_data) == 0:
            return jsonify({
                "success": False,
                "error": "Empty PDF data"
            }), 400
            
        # Perform analysis with just the summary type
        result = analyzer.analyze_document(pdf_data, ["summary"])
        
        # Simplify the response to focus on summary
        if result.get("success", False) and "analyses" in result and "summary" in result["analyses"]:
            return jsonify({
                "success": True,
                "summary": result["analyses"]["summary"]
            })
        else:
            error_msg = result.get("error", "Unknown error during summarization")
            return jsonify({
                "success": False,
                "error": error_msg
            }), 500
            
    except Exception as e:
        logger.error(f"Error in PDF summarization: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Summarization failed: {str(e)}"
        }), 500

@pdf_analysis_bp.route('/extract-entities', methods=['POST'])
@token_required
def extract_entities():
    """Extract entities from a PDF document"""
    try:
        # Similar to summarize_pdf but for entity extraction
        if not request.json and not request.files:
            return jsonify({
                "success": False,
                "error": "Either a file upload or JSON with base64 PDF data is required"
            }), 400
            
        # Get the PDF data
        pdf_data = None
        
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file.filename == '' or not pdf_file.filename.lower().endswith('.pdf'):
                return jsonify({
                    "success": False,
                    "error": "Invalid PDF file"
                }), 400
                
            pdf_data = pdf_file.read()
            
        elif request.json and 'pdf_base64' in request.json:
            base64_data = request.json['pdf_base64']
            if ';base64,' in base64_data:
                base64_data = base64_data.split(';base64,')[1]
                
            try:
                pdf_data = base64.b64decode(base64_data)
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Invalid base64 data: {str(e)}"
                }), 400
        else:
            return jsonify({
                "success": False, 
                "error": "No PDF data provided"
            }), 400
            
        # Validate PDF data
        if not pdf_data or len(pdf_data) == 0:
            return jsonify({
                "success": False,
                "error": "Empty PDF data"
            }), 400
            
        # Perform analysis with just the entities type
        result = analyzer.analyze_document(pdf_data, ["entities"])
        
        # Simplify the response to focus on entities
        if result.get("success", False) and "analyses" in result and "entities" in result["analyses"]:
            return jsonify({
                "success": True,
                "entities": result["analyses"]["entities"]
            })
        else:
            error_msg = result.get("error", "Unknown error during entity extraction")
            return jsonify({
                "success": False,
                "error": error_msg
            }), 500
            
    except Exception as e:
        logger.error(f"Error in PDF entity extraction: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Entity extraction failed: {str(e)}"
        }), 500

@pdf_analysis_bp.route('/classify', methods=['POST'])
@token_required
def classify_document():
    """Classify a PDF document"""
    try:
        # Similar to other endpoints but for classification
        if not request.json and not request.files:
            return jsonify({
                "success": False,
                "error": "Either a file upload or JSON with base64 PDF data is required"
            }), 400
            
        # Get the PDF data
        pdf_data = None
        
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file.filename == '' or not pdf_file.filename.lower().endswith('.pdf'):
                return jsonify({
                    "success": False,
                    "error": "Invalid PDF file"
                }), 400
                
            pdf_data = pdf_file.read()
            
        elif request.json and 'pdf_base64' in request.json:
            base64_data = request.json['pdf_base64']
            if ';base64,' in base64_data:
                base64_data = base64_data.split(';base64,')[1]
                
            try:
                pdf_data = base64.b64decode(base64_data)
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Invalid base64 data: {str(e)}"
                }), 400
        else:
            return jsonify({
                "success": False, 
                "error": "No PDF data provided"
            }), 400
            
        # Validate PDF data
        if not pdf_data or len(pdf_data) == 0:
            return jsonify({
                "success": False,
                "error": "Empty PDF data"
            }), 400
            
        # Perform analysis with just the classification type
        result = analyzer.analyze_document(pdf_data, ["classification"])
        
        # Simplify the response to focus on classification
        if result.get("success", False) and "analyses" in result and "classification" in result["analyses"]:
            return jsonify({
                "success": True,
                "classification": result["analyses"]["classification"]
            })
        else:
            error_msg = result.get("error", "Unknown error during classification")
            return jsonify({
                "success": False,
                "error": error_msg
            }), 500
            
    except Exception as e:
        logger.error(f"Error in PDF classification: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Classification failed: {str(e)}"
        }), 500

@pdf_analysis_bp.route('/extract-text', methods=['POST'])
@token_required
def extract_text():
    """Extract text from a PDF document"""
    try:
        # This endpoint uses the file parser rather than the analyzer
        if not request.json and not request.files:
            return jsonify({
                "success": False,
                "error": "Either a file upload or JSON with base64 PDF data is required"
            }), 400
            
        # Get the PDF data
        pdf_data = None
        
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file.filename == '' or not pdf_file.filename.lower().endswith('.pdf'):
                return jsonify({
                    "success": False,
                    "error": "Invalid PDF file"
                }), 400
                
            pdf_data = pdf_file.read()
            
        elif request.json and 'pdf_base64' in request.json:
            base64_data = request.json['pdf_base64']
            if ';base64,' in base64_data:
                base64_data = base64_data.split(';base64,')[1]
                
            try:
                pdf_data = base64.b64decode(base64_data)
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Invalid base64 data: {str(e)}"
                }), 400
        else:
            return jsonify({
                "success": False, 
                "error": "No PDF data provided"
            }), 400
            
        # Validate PDF data
        if not pdf_data or len(pdf_data) == 0:
            return jsonify({
                "success": False,
                "error": "Empty PDF data"
            }), 400
            
        # Use file parser to extract text
        result = FileParser.parse_pdf(pdf_data)
        
        # Return the result directly
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error in PDF text extraction: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Text extraction failed: {str(e)}"
        }), 500