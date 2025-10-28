A free and opensource tool for converting Markdown documents into professional screenplays in the PDF format.

A Web interface is available at https://md2script.kevs.wtf to either drag and drop a markdown file or edit directly in the browser.

Ensures no other files other than markdown are uploaded for security reasons, limit of 1mb per file, not more than 5 requests per minute from a single IP address.

Use FastAPI for the backend API

Create a Dockerfile and docker-compose.yml for easy deployment

Use GitHub Actions for CI/CD to build and push Docker images to a private Docker registry at 192.168.2.1:5000/md2script:latest

