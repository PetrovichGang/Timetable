from config import API_IP, API_PORT
import uvicorn


if __name__ == "__main__":
    uvicorn.run("api:app", host=API_IP, port=API_PORT, log_level="info", reload=True, headers=[("Access-Control-Allow-Origin", "*")])
