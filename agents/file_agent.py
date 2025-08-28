from core.base_agent import BaseAgent
from typing import Dict, Any, List
import PyPDF2
import docx
import pandas as pd
import json
from pathlib import Path

class FileAgent(BaseAgent):
    """Agent for file processing and analysis"""
    
    def __init__(self):
        super().__init__(name="file_agent")
        self.supported_formats = {
            'pdf': self.process_pdf,
            'docx': self.process_docx,
            'txt': self.process_txt,
            'csv': self.process_csv,
            'xlsx': self.process_excel,
            'json': self.process_json
        }
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process uploaded files"""
        context = input_data.get("context", {})
        files = context.get("files", [])
        message = input_data.get("message", "")
        
        if not files:
            return {"text": "No files to process.", "metadata": {"agent": self.name}}
            
        processed_files = []
        for file_info in files:
            file_content = await self.process_file(file_info)
            processed_files.append(file_content)
            
        # Analyze files based on user query
        analysis = await self.analyze_files(processed_files, message)
        
        return {
            "text": analysis,
            "files": processed_files,
            "metadata": {"agent": self.name}
        }
    
    async def process_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual file"""
        file_path = file_info.get("path")
        file_ext = Path(file_path).suffix[1:].lower()
        
        if file_ext in self.supported_formats:
            content = await self.supported_formats[file_ext](file_path)
            return {
                "name": Path(file_path).name,
                "type": file_ext,
                "content": content,
                "size": Path(file_path).stat().st_size
            }
        else:
            return {
                "name": Path(file_path).name,
                "type": file_ext,
                "error": f"Unsupported file format: {file_ext}"
            }
    
    async def process_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    
    async def process_docx(self, file_path: str) -> str:
        """Extract text from Word document"""
        doc = docx.Document(file_path)
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    
    async def process_txt(self, file_path: str) -> str:
        """Read text file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    async def process_csv(self, file_path: str) -> Dict[str, Any]:
        """Process CSV file"""
        df = pd.read_csv(file_path)
        return {
            "preview": df.head(10).to_dict(),
            "shape": df.shape,
            "columns": list(df.columns),
            "summary": df.describe().to_dict()
        }
    
    async def process_excel(self, file_path: str) -> Dict[str, Any]:
        """Process Excel file"""
        excel_data = {}
        xls = pd.ExcelFile(file_path)
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name)
            excel_data[sheet_name] = {
                "preview": df.head(10).to_dict(),
                "shape": df.shape,
                "columns": list(df.columns)
            }
            
        return excel_data
    
    async def process_json(self, file_path: str) -> Dict[str, Any]:
        """Process JSON file"""
        with open(file_path, 'r') as file:
            return json.load(file)
    
    async def analyze_files(self, files: List[Dict], query: str) -> str:
        """Analyze processed files based on user query"""
        # Prepare file contents for analysis
        file_summaries = []
        for file in files:
            if file.get("error"):
                file_summaries.append(f"File: {file['name']} - Error: {file['error']}")
            else:
                content_preview = str(file.get("content", ""))[:1000]
                file_summaries.append(f"File: {file['name']} ({file['type']})\nContent: {content_preview}")
                
        combined_content = "\n\n".join(file_summaries)
        
        prompt = f"""Analyze the following files based on the user query: "{query}"
        
        Files:
        {combined_content}
        
        Analysis:"""
        
        return await self.think(prompt)