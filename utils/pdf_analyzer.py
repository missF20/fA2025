"""
PDF Analyzer Utility

This module provides advanced PDF analysis capabilities using AI to extract
insights, summaries, key information, and perform document classification.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple

from utils.file_parser import FileParser
from utils.ai_client import AIClient

# Configure logging
logger = logging.getLogger(__name__)

class PDFAnalyzer:
    """Advanced PDF analysis using AI capabilities"""
    
    def __init__(self):
        """Initialize the PDF analyzer with AI client"""
        self.ai_client = AIClient()
        
    def analyze_document(self, pdf_data: bytes, analysis_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive document analysis
        
        Args:
            pdf_data: Raw PDF file data
            analysis_types: List of analysis types to perform
                Options: "summary", "key_info", "entities", "classification", "sentiment", "topics"
                
        Returns:
            Dict containing analysis results
        """
        if analysis_types is None:
            analysis_types = ["summary", "key_info", "entities"]
            
        # First parse the PDF to extract text
        parse_result = FileParser.parse_pdf(pdf_data)
        
        if not parse_result.get("success", False):
            return {
                "success": False,
                "error": parse_result.get("error", "Unknown error parsing PDF")
            }
            
        content = parse_result.get("content", "")
        metadata = parse_result.get("metadata", {})
        
        # If no content found, return error
        if not content.strip():
            return {
                "success": False,
                "error": "No text content found in PDF"
            }
            
        # Perform the requested analyses
        result = {
            "success": True,
            "metadata": metadata,
            "analyses": {}
        }
        
        try:
            # Handle large documents by chunking if necessary
            if len(content) > 8000:
                logger.info(f"Document is large ({len(content)} chars), using chunked analysis")
                content_chunks = self._chunk_text(content, 8000, 200)
            else:
                content_chunks = [content]
                
            # Perform each requested analysis
            if "summary" in analysis_types:
                result["analyses"]["summary"] = self._generate_summary(content_chunks)
                
            if "key_info" in analysis_types:
                result["analyses"]["key_info"] = self._extract_key_info(content_chunks)
                
            if "entities" in analysis_types:
                result["analyses"]["entities"] = self._extract_entities(content_chunks)
                
            if "classification" in analysis_types:
                result["analyses"]["classification"] = self._classify_document(content_chunks)
                
            if "sentiment" in analysis_types:
                result["analyses"]["sentiment"] = self._analyze_sentiment(content_chunks)
                
            if "topics" in analysis_types:
                result["analyses"]["topics"] = self._extract_topics(content_chunks)
                
            return result
            
        except Exception as e:
            logger.error(f"Error during document analysis: {str(e)}")
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }
            
    def _chunk_text(self, text: str, chunk_size: int = 8000, overlap: int = 200) -> List[str]:
        """
        Split large text into manageable chunks with overlap
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk
            overlap: Overlap between chunks to maintain context
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            # Get end of this chunk
            end = min(start + chunk_size, len(text))
            
            # Try to find a good break point (period or newline)
            if end < len(text):
                # Try to find the last sentence break
                last_period = text.rfind(".", start, end)
                last_newline = text.rfind("\n", start, end)
                
                break_point = max(last_period, last_newline)
                
                if break_point > start + (chunk_size // 2):  # Ensure the break isn't too early
                    end = break_point + 1
            
            # Add this chunk to our list
            chunks.append(text[start:end])
            
            # Move to next chunk, accounting for overlap
            start = end - overlap
            
        return chunks
        
    def _generate_summary(self, content_chunks: List[str]) -> Dict[str, Any]:
        """
        Generate a document summary using AI
        
        Args:
            content_chunks: List of document content chunks
            
        Returns:
            Dict with summary information
        """
        results = {
            "brief": "",
            "detailed": "",
            "key_points": []
        }
        
        try:
            # For single chunks, do a direct summary
            if len(content_chunks) == 1:
                prompt = f"""Analyze the following document and provide:
1. A brief summary (2-3 sentences)
2. A more detailed summary (1-2 paragraphs)
3. 5-7 key points in bullet form

Document content:
{content_chunks[0]}
"""
                response = self.ai_client.generate_text(prompt, max_tokens=1000)
                
                if response:
                    # Parse the response to extract each part
                    brief_summary = self._extract_section(response, "brief summary", "detailed summary")
                    detailed_summary = self._extract_section(response, "detailed summary", "key points")
                    key_points_text = self._extract_section(response, "key points", "")
                    
                    results["brief"] = brief_summary.strip()
                    results["detailed"] = detailed_summary.strip()
                    
                    # Extract bullet points
                    key_points = []
                    for line in key_points_text.split("\n"):
                        if line.strip().startswith("-") or line.strip().startswith("•"):
                            key_points.append(line.strip()[1:].strip())
                    
                    results["key_points"] = key_points
            
            else:
                # For multi-chunk documents, do a hierarchical summarization
                chunk_summaries = []
                
                # First summarize each chunk
                for i, chunk in enumerate(content_chunks):
                    prompt = f"""Summarize the following section (part {i+1} of {len(content_chunks)}) of a larger document in 3-5 sentences:

{chunk}"""
                    
                    summary = self.ai_client.generate_text(prompt, max_tokens=250)
                    if summary:
                        chunk_summaries.append(summary)
                
                # Then create a global summary from the chunk summaries
                combined_summaries = "\n\n".join([f"Part {i+1}: {s}" for i, s in enumerate(chunk_summaries)])
                
                final_prompt = f"""Based on these summaries of different parts of a document, create:
1. A brief summary (2-3 sentences)
2. A more detailed summary (1-2 paragraphs)
3. 5-7 key points in bullet form

Document summaries:
{combined_summaries}
"""
                
                response = self.ai_client.generate_text(final_prompt, max_tokens=1000)
                
                if response:
                    # Parse the response
                    brief_summary = self._extract_section(response, "brief summary", "detailed summary")
                    detailed_summary = self._extract_section(response, "detailed summary", "key points")
                    key_points_text = self._extract_section(response, "key points", "")
                    
                    results["brief"] = brief_summary.strip()
                    results["detailed"] = detailed_summary.strip()
                    
                    # Extract bullet points
                    key_points = []
                    for line in key_points_text.split("\n"):
                        if line.strip().startswith("-") or line.strip().startswith("•"):
                            key_points.append(line.strip()[1:].strip())
                    
                    results["key_points"] = key_points
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return {
                "error": f"Failed to generate summary: {str(e)}"
            }
    
    def _extract_key_info(self, content_chunks: List[str]) -> Dict[str, Any]:
        """
        Extract key information from the document
        
        Args:
            content_chunks: List of document content chunks
            
        Returns:
            Dict with key information
        """
        try:
            # For single chunks, do direct extraction
            if len(content_chunks) == 1:
                prompt = f"""Extract key information from the following document.
Include:
- Document type
- Names of people mentioned (if any)
- Organizations mentioned (if any)
- Dates mentioned (if any)
- Numerical figures (if any)
- Locations mentioned (if any)
- Key metrics or statistics (if any)

Present the information in a structured format.

Document content:
{content_chunks[0]}
"""
                response = self.ai_client.generate_text(prompt, max_tokens=800, response_format="json_object")
                
                if response:
                    try:
                        # Try to parse as JSON
                        return json.loads(response)
                    except json.JSONDecodeError:
                        # If not JSON, return as text
                        return {"text": response}
            
            else:
                # For multi-chunk documents, extract from each chunk then combine
                all_key_info = []
                
                # Process each chunk
                for i, chunk in enumerate(content_chunks):
                    prompt = f"""Extract key information from the following section (part {i+1} of {len(content_chunks)}) of a document.
Include:
- Names of people mentioned
- Organizations mentioned
- Dates mentioned
- Numerical figures
- Locations mentioned
- Key metrics or statistics

Present the information in a structured JSON format.

Document section:
{chunk}
"""
                    response = self.ai_client.generate_text(prompt, max_tokens=600, response_format="json_object")
                    
                    if response:
                        try:
                            info = json.loads(response)
                            all_key_info.append(info)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse key info JSON from chunk {i+1}")
                
                # Combine all extracted information
                return self._combine_key_info(all_key_info)
            
            return {"error": "Failed to extract key information"}
            
        except Exception as e:
            logger.error(f"Error extracting key information: {str(e)}")
            return {
                "error": f"Failed to extract key information: {str(e)}"
            }
    
    def _combine_key_info(self, info_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine key information extracted from multiple chunks
        
        Args:
            info_list: List of key information dictionaries
            
        Returns:
            Combined key information
        """
        combined = {}
        
        # Common fields to combine
        list_fields = ["people", "names", "organizations", "dates", "locations", 
                      "numerical_figures", "key_metrics", "statistics"]
        
        for info in info_list:
            for key, value in info.items():
                # For list fields, combine lists
                if key.lower() in list_fields:
                    if key not in combined:
                        combined[key] = []
                    
                    # Add items from this chunk
                    if isinstance(value, list):
                        for item in value:
                            if item not in combined[key]:
                                combined[key].append(item)
                    else:
                        # Handle case where AI returned single string instead of list
                        if value and value not in combined[key]:
                            combined[key].append(value)
                
                # For other fields, take the most common or first
                else:
                    if key not in combined:
                        combined[key] = value
        
        return combined
    
    def _extract_entities(self, content_chunks: List[str]) -> Dict[str, Any]:
        """
        Extract named entities from the document
        
        Args:
            content_chunks: List of document content chunks
            
        Returns:
            Dict with entity information
        """
        try:
            # Use similar approach as _extract_key_info but focus on entities
            if len(content_chunks) == 1:
                prompt = f"""Extract all named entities from the following document.
Categorize them as:
- People (full names)
- Organizations (company names, institutions)
- Locations (cities, countries, etc.)
- Dates and Times
- Products or Services
- Events

Return the results in a structured JSON format with entity categories as keys and arrays of unique entities as values.

Document content:
{content_chunks[0].strip()[:6000]}  # Limit size for entity extraction
"""
                response = self.ai_client.generate_text(prompt, max_tokens=800, response_format="json_object")
                
                if response:
                    try:
                        return json.loads(response)
                    except json.JSONDecodeError:
                        return {"text": response}
            
            else:
                # For multi-chunk documents
                all_entities = []
                
                # Process each chunk
                for i, chunk in enumerate(content_chunks):
                    prompt = f"""Extract all named entities from the following section (part {i+1} of {len(content_chunks)}) of a document.
Categorize them as:
- People (full names)
- Organizations (company names, institutions)
- Locations (cities, countries, etc.)
- Dates and Times
- Products or Services
- Events

Return the results in a structured JSON format with entity categories as keys and arrays of entities as values.

Document section:
{chunk[:6000]}  # Limit size for entity extraction
"""
                    response = self.ai_client.generate_text(prompt, max_tokens=800, response_format="json_object")
                    
                    if response:
                        try:
                            entities = json.loads(response)
                            all_entities.append(entities)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse entities JSON from chunk {i+1}")
                
                # Combine entities from all chunks
                return self._combine_entities(all_entities)
            
            return {"error": "Failed to extract entities"}
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return {
                "error": f"Failed to extract entities: {str(e)}"
            }
    
    def _combine_entities(self, entities_list: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Combine entities extracted from multiple chunks
        
        Args:
            entities_list: List of entity dictionaries
            
        Returns:
            Combined entity dictionary
        """
        combined = {}
        
        for entities in entities_list:
            for category, values in entities.items():
                if category not in combined:
                    combined[category] = []
                
                # Add new entities
                if isinstance(values, list):
                    for entity in values:
                        if entity not in combined[category]:
                            combined[category].append(entity)
                else:
                    # Handle case where AI returned string instead of list
                    if values and values not in combined[category]:
                        combined[category].append(values)
        
        return combined
    
    def _classify_document(self, content_chunks: List[str]) -> Dict[str, Any]:
        """
        Classify the document into categories
        
        Args:
            content_chunks: List of document content chunks
            
        Returns:
            Dict with classification information
        """
        try:
            # For classification, use the first chunk and a portion of others if available
            content_sample = content_chunks[0]
            
            # Add samples from other chunks if available
            if len(content_chunks) > 1:
                additional_samples = []
                for i in range(1, min(3, len(content_chunks))):
                    # Get the first 500 characters from additional chunks
                    additional_samples.append(content_chunks[i][:500])
                
                content_sample += "\n\n[Additional content samples:]\n" + "\n\n".join(additional_samples)
            
            prompt = f"""Classify the following document into categories.
Provide:
1. Primary document type (e.g., report, article, contract, academic paper)
2. Subject matter categories (e.g., finance, technology, legal, medical)
3. Audience level (e.g., technical, general, academic)
4. Formality level (e.g., formal, informal, technical)
5. Purpose (e.g., informational, persuasive, instructional)

Return the results in a structured JSON format.

Document content sample:
{content_sample[:7000]}  # Limit to 7000 chars for classification
"""
            response = self.ai_client.generate_text(prompt, max_tokens=500, response_format="json_object")
            
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return {"text": response}
            
            return {"error": "Failed to classify document"}
            
        except Exception as e:
            logger.error(f"Error classifying document: {str(e)}")
            return {
                "error": f"Failed to classify document: {str(e)}"
            }
    
    def _analyze_sentiment(self, content_chunks: List[str]) -> Dict[str, Any]:
        """
        Analyze the sentiment of the document
        
        Args:
            content_chunks: List of document content chunks
            
        Returns:
            Dict with sentiment analysis information
        """
        try:
            # For sentiment, analyze first chunk and sample of others
            content_sample = content_chunks[0]
            
            # If multiple chunks, sample from others
            if len(content_chunks) > 1:
                additional_samples = []
                for i in range(1, min(3, len(content_chunks))):
                    chunk_len = len(content_chunks[i])
                    # Get start, middle and end samples
                    start_sample = content_chunks[i][:500]
                    mid_point = chunk_len // 2
                    mid_sample = content_chunks[i][mid_point-250:mid_point+250] if chunk_len > 500 else ""
                    end_sample = content_chunks[i][-500:] if chunk_len > 500 else ""
                    
                    samples = [s for s in [start_sample, mid_sample, end_sample] if s]
                    additional_samples.extend(samples)
                
                content_sample += "\n\n[Additional content samples:]\n" + "\n\n".join(additional_samples)
            
            prompt = f"""Analyze the sentiment and emotional tone of the following document.
Provide:
1. Overall sentiment (positive, negative, neutral, or mixed)
2. Sentiment score (-1.0 to 1.0, where -1 is very negative, 0 is neutral, and 1 is very positive)
3. Dominant emotions detected (e.g., happiness, sadness, anger, concern, optimism)
4. Confidence level for this analysis (0.0 to 1.0)
5. Brief explanation of this assessment

Return the results in a structured JSON format.

Document content:
{content_sample[:7000]}  # Limit to 7000 chars for sentiment analysis
"""
            response = self.ai_client.generate_text(prompt, max_tokens=500, response_format="json_object")
            
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return {"text": response}
            
            return {"error": "Failed to analyze sentiment"}
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                "error": f"Failed to analyze sentiment: {str(e)}"
            }
    
    def _extract_topics(self, content_chunks: List[str]) -> Dict[str, Any]:
        """
        Extract main topics from the document
        
        Args:
            content_chunks: List of document content chunks
            
        Returns:
            Dict with topic information
        """
        try:
            # For topics, use a sample from each chunk
            content_samples = []
            
            for i, chunk in enumerate(content_chunks):
                # Use first 1000 chars of each chunk
                content_samples.append(chunk[:1000])
            
            combined_sample = "\n\n".join([f"[Sample {i+1}:]\n{sample}" for i, sample in enumerate(content_samples)])
            
            prompt = f"""Identify the main topics and themes in the following document samples.
Provide:
1. A list of 5-10 main topics in order of importance
2. For each topic, provide a relevance score (0-100) 
3. For each topic, list key related terms or concepts found in the text
4. Overall document theme (1-2 sentences)

Return the results in a structured JSON format.

Document samples:
{combined_sample}
"""
            response = self.ai_client.generate_text(prompt, max_tokens=800, response_format="json_object")
            
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return {"text": response}
            
            return {"error": "Failed to extract topics"}
            
        except Exception as e:
            logger.error(f"Error extracting topics: {str(e)}")
            return {
                "error": f"Failed to extract topics: {str(e)}"
            }
    
    def _extract_section(self, text: str, start_marker: str, end_marker: Optional[str] = "") -> str:
        """
        Extract a section from text based on markers
        
        Args:
            text: Text to extract from
            start_marker: Marker indicating section start
            end_marker: Marker indicating section end (if empty, extract to end of text)
            
        Returns:
            Extracted section
        """
        # Case insensitive search
        text_lower = text.lower()
        start_marker_lower = start_marker.lower()
        
        # Find start position
        start_pos = text_lower.find(start_marker_lower)
        if start_pos == -1:
            return ""
        
        # Adjust start position to after the marker
        start_pos += len(start_marker_lower)
        
        # Find the end position if end marker is provided
        if end_marker:
            end_marker_lower = end_marker.lower()
            end_pos = text_lower.find(end_marker_lower, start_pos)
            if end_pos == -1:
                # If end marker not found, go to the end of the text
                section = text[start_pos:]
            else:
                section = text[start_pos:end_pos]
        else:
            # If no end marker, take everything to the end
            section = text[start_pos:]
        
        return section.strip()