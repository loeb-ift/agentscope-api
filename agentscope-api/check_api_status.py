import uvicorn
from app.main import app

print('API startup check successful')
print('Registered routes:')
for route in app.routes:
    print(f'- {route.path}')