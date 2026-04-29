#FastAPI entry point
from fastapi import FastAPI
from pydantic import BaseModel
from weather import download_epw_from_pvgis
from off_app import office_cooling_from_epw
