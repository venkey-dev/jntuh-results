import os
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from jntuh.Executables.jntuhresultscraper import ResultScraper

app = FastAPI(title="JNTU Results API", version="1.0.0")

# Enable CORS for cross-origin requests from frontend apps or local static files
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_PATH = Path(__file__).resolve().parent.parent / "result.html"

@app.get("/", response_class=FileResponse)
def root():
    """Serve the interactive academic result HTML page."""
    if HTML_PATH.exists():
        return FileResponse(HTML_PATH)
    return {"message": "Go to /docs for API documentation or place result.html in the root directory."}

@app.get("/result", response_class=FileResponse)
def view_result():
    """Direct route for viewing results memo HTML."""
    if HTML_PATH.exists():
        return FileResponse(HTML_PATH)
    raise HTTPException(status_code=404, detail="result.html not found")

@app.get('/api/{university}/academicresult')
def academicResult(university: str, htno: str = Query(...)):

    # Check if the university code is 'jntuh'
    if university.lower() == 'jntuh':

        # Check if the hall ticket number is valid
        if len(htno) != 10:
            raise HTTPException(status_code=401, detail="Invalid hall ticket number")
        
        # Create an instance of ResultScraper
        jntuhresult = ResultScraper(htno.upper())
        
        try:
            # Run the scraper and return the result
            result = jntuhresult.run()
            
            # Calculate the total marks and credits
            total = sum(i.get("total", 0) for i in result["Results"].values() if i.get("credits", 0) != 0)
            total_credits = sum(i["credits"] for i in result["Results"].values() if i.get("credits", 0) != 0)

            # Calculate the CGPA if there are non-zero credits
            if total_credits != 0:
                result["CGPA"] =  total / total_credits

            # Return the result
            return result
        except Exception as e:
            # Catch any exceptions raised during scraping
            raise HTTPException(status_code=500, detail=str(e))


