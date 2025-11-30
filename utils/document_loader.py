from config.config import config
import os

def load_documents():
    files = os.listdir(config.DOCUMENTS_PATH)
    return files  # placeholder
