"""
Test if python-docx is available and working.
"""

def test_docx_import():
    """
    Try to import docx and check if it's working.
    """
    print("Testing docx import...")
    
    try:
        from docx import Document
        print("✅ Successfully imported Document from docx!")
        
        # Check if we can create a simple document
        try:
            doc = Document()
            doc.add_paragraph("Test Paragraph")
            print("✅ Successfully created a document!")
            return True
        except Exception as e:
            print(f"❌ Error creating document: {str(e)}")
            return False
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_docx_import()